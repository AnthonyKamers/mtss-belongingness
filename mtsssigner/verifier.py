import functools
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import sqrt
from multiprocessing import Pool
from typing import List, Tuple, Union
from itertools import combinations_with_replacement

from Crypto.PublicKey.ECC import EccKey
from Crypto.PublicKey.RSA import RsaKey

from mtsssigner import logger
from mtsssigner.blocks.CSVParser import DELIMITER, CSVParser
from mtsssigner.blocks.ImageParser import ImageParser
from mtsssigner.blocks.Parser import Parser
from mtsssigner.blocks.block_utils import get_parser_for_file, DEFAULT_IMAGE_BLOCK_SIZE
from mtsssigner.cff_builder import (create_cff,
                                    create_1_cff)
from mtsssigner.cffs.cff_utils import get_parameters_polynomial_cff, ignore_columns_cff
from mtsssigner.signature_scheme import SigScheme, D_BYTES_LENGTH, D_BYTES_ORDER
from mtsssigner.utils.file_and_block_utils import (rebuild_content_from_blocks,
                                                   read_cff_from_file)

cff: List[List[int]] = [[]]
parser: Union[None, Parser] = None
message: str
blocks: List[str]
block_hashes: List[Union[bytearray, bytes, str]] = []
hashed_tests: List[Union[bytearray, bytes]] = []
corrected = {}


def clear_globals():
    global cff, message, blocks, block_hashes, hashed_tests, corrected, parser
    cff = [[]]
    parser = None
    message = ""
    blocks = []
    block_hashes = []
    hashed_tests = []
    corrected = {}


def pre_verify(message_file_path: str, signature_file_path: str, sig_scheme: SigScheme, public_key_file_path: str,
               csv_delimiter: DELIMITER = DELIMITER.BREAK_LINE, image_block_size: int = DEFAULT_IMAGE_BLOCK_SIZE,
               concatenate_strings: bool = False):
    global message, parser

    clear_globals()

    # here, we do not need to parse the file into blocks
    # we only need the blocks for the message if the message was modified
    # this is done in #verify_raw
    parser = get_parser_for_file(message_file_path)

    if isinstance(parser, CSVParser):
        parser.set_delimiter(csv_delimiter)

    if isinstance(parser, ImageParser):
        parser.set_block_size(image_block_size)

    message = parser.get_content()

    with open(signature_file_path, "rb") as signature_file:
        signature: bytes = signature_file.read()

    public_key = sig_scheme.get_public_key(public_key_file_path)

    return signature, public_key, sig_scheme, message_file_path, public_key_file_path, concatenate_strings


def verify_raw(signature: bytes, public_key: Union[RsaKey, EccKey],
               sig_scheme: SigScheme, message_file_path, public_key_file_path,
               concatenate_strings: bool):
    global message, blocks, hashed_tests, cff, block_hashes, corrected, parser

    t = signature[:-int(sig_scheme.signature_length_bytes)]
    t_signature = signature[-int(sig_scheme.signature_length_bytes):]

    verification_result = sig_scheme.verify(public_key, t, t_signature)
    if not verification_result:
        logger.log_nonmodified_verification_result(
            message_file_path, public_key_file_path, sig_scheme, verification_result)
        return verification_result, []

    d = int.from_bytes(t[-D_BYTES_LENGTH:], D_BYTES_ORDER)
    t_without_d = t[:-D_BYTES_LENGTH]

    message_hash = sig_scheme.get_digest(message)
    signature_message_hash = t_without_d[-int(sig_scheme.digest_size_bytes):]

    if signature_message_hash == message_hash:
        verification_result = True
        logger.log_nonmodified_verification_result(
            message_file_path, public_key_file_path, sig_scheme, verification_result)
        return True, []

    # now that we know the message has been modified, we need to locate the error
    # here, we join the hashes to reconstruct our T
    joined_hashed_tests: bytearray = t_without_d[:-int(sig_scheme.digest_size_bytes)]
    hashed_tests = [
        joined_hashed_tests[i:i + int(sig_scheme.digest_size_bytes)]
        for i in range(0, len(joined_hashed_tests), int(sig_scheme.digest_size_bytes))
    ]

    # read the file and parse into blocks
    blocks = parser.parse()
    n_from_file = len(blocks)

    t = len(hashed_tests)
    q = int(sqrt(t))

    # if d=1, use 1-CFF, otherwise use the CFF(t, n) in polynomial construction
    if d == 1:
        n = n_from_file
        k = None

        try:
            cff = read_cff_from_file(t, n_from_file, d)
        except IOError:
            cff = create_1_cff(n)
    else:
        q_expected, k, n_expected, t_expected = get_parameters_polynomial_cff(d, n_from_file)
        n = n_expected

        if t != t_expected:
            raise ValueError("The number of tests 't' is different from the expected value")

        if q != q_expected:
            raise ValueError("The ratio 'q' is different from the expected one")

        try:
            cff = read_cff_from_file(t, n_expected, d)
            logger.log_cff_from_file()
        except IOError:
            cff = create_cff(q, k)

        # if the number of blocks parsed from the file is different from the expected for this d-CFF, we
        # need to create empty ones to match the expected number of blocks
        if n_expected > n_from_file:
            cff = ignore_columns_cff(cff, n_expected - n_from_file)

    # these dimensions take into account the possibility of not using the last columns of a CFF
    # all other references to cff must consider this
    cff_dimensions = (len(cff), len(cff[0]))

    # we may have updated the number of blocks in the file, so we need to get it again
    blocks = parser.get_blocks()

    # we will start recreating the CFF tests
    rebuilt_tests: List[Union[str, bytes]] = []

    for block in blocks:
        if concatenate_strings:
            block_hashes.append(str(block))
        else:
            block_hashes.append(sig_scheme.get_digest(block))

    for test in range(cff_dimensions[0]):
        concatenation = "" if concatenate_strings else bytes()

        for block in range(cff_dimensions[1]):
            if cff[test][block] == 1:
                concatenation += block_hashes[block]
        rebuilt_tests.append(concatenation)

    non_modified_blocks: List[int] = []

    for test in range(len(rebuilt_tests)):
        rebuilt_hashed_test = sig_scheme.get_digest(rebuilt_tests[test])
        if rebuilt_hashed_test == hashed_tests[test]:
            for block in range(cff_dimensions[1]):
                if cff[test][block] == 1:
                    non_modified_blocks.append(block)

    modified_blocks = [block for block in range(cff_dimensions[1])
                       if block not in non_modified_blocks]
    modified_blocks_content = [blocks[block] for block in modified_blocks]
    result = len(modified_blocks) <= d

    logger.log_localization_result(
        message_file_path, public_key_file_path, n, len(cff), d, q,
        k, result, modified_blocks, modified_blocks_content, parser)

    return result, modified_blocks


# Verifies the signature and localizes the modified blocks
# The resulting number of blocks from the supplied file must
# be the same as the one generated by the sign function
def verify(sig_scheme: SigScheme, message_file_path: str, signature_file_path: str,
           public_key_file_path: str) -> Tuple[bool, List[int]]:
    return verify_raw(*pre_verify(message_file_path, signature_file_path, sig_scheme, public_key_file_path))


# Verifies the signature, localizes and corrects the modified blocks. The
# resulting number of blocks from the supplied file must be the same as the
# one generated by the sign function. Also, the correction works better if
# the number of characters of the original values of the modified blocks is
# small (i.e. 4 or less) or the characters of the file are codifiable by 1
# byte (UTF-8 equivalent to ASCII), otherwise the correction takes too long.
def verify_and_correct(verification_result, sig_scheme: SigScheme, message_file_path: str, concatenate_strings: bool) \
        -> Tuple[bool, List[int], str]:
    correction = ""
    if verification_result[1] == [] or not verification_result[0]:
        return verification_result[0], verification_result[1], correction

    for k in verification_result[1]:
        i_rows = []
        modified_blocks_minus_k = set(verification_result[1]) - {k}
        for i in range(len(cff)):
            if cff[i][k] == 1:
                i_rows.append(i)
                for j in modified_blocks_minus_k:
                    if cff[i][j] == 1:
                        i_rows.pop()
                        break
        i = i_rows[0]
        global corrected
        corrected[k] = False

        i_concatenation = []
        k_index = -1
        for block in range(len(cff[i])):
            if cff[i][block] == 1:
                if block != k:
                    if concatenate_strings:
                        i_concatenation.append(str(blocks[block]))
                    else:
                        i_concatenation.append(block_hashes[block])
                else:
                    k_index = len(i_concatenation)

                    if concatenate_strings:
                        i_concatenation.append('0')
                    else:
                        i_concatenation.append(b'0' * sig_scheme.digest_size_bytes)

        k_index = int((k_index * sig_scheme.digest_size) / 8)
        concatenation_now = i_concatenation if concatenate_strings else bytearray(b''.join(i_concatenation))

        find_correct_b = functools.partial(
            __return_if_correct_b,
            concatenation=concatenation_now,
            k_index=k_index, i=i, k=k, sig_scheme=sig_scheme,
            concatenate_strings=concatenate_strings
        )

        process_pool_size = __available_cpu_count()
        MAX_CORRECTABLE_BLOCK_LEN_CHARACTERS = __get_max_block_length(verification_result[1])
        logger.log_correction_parameters(MAX_CORRECTABLE_BLOCK_LEN_CHARACTERS, process_pool_size)

        if concatenate_strings:
            numbers = [i for i in range(2 ** 8)]
            b_s = []
            for index_now in range(MAX_CORRECTABLE_BLOCK_LEN_CHARACTERS):
                iterations = list(combinations_with_replacement(numbers, index_now + 1))
                b_s += iterations
        else:
            b_s = range(2 ** (MAX_CORRECTABLE_BLOCK_LEN_CHARACTERS * 8))

        with ProcessPoolExecutor(max_workers=process_pool_size) as executor:
            futures = {executor.submit(find_correct_b, b) for b in b_s}

            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    if result[0]:
                        corrected[k] = True
                        blocks[k] = result[1]
                        logger.log_block_correction(k, blocks[k])
                    else:
                        logger.log_collision(k, result[1])

                    # cancel all remaining futures
                    for f in futures:
                        f.cancel()
                    break

    if any(correction for correction in corrected.values()):
        correction = rebuild_content_from_blocks(blocks, message_file_path[-3:])
    else:
        logger.log_block_correction(-1)
    return verification_result[0], verification_result[1], correction


def __get_max_block_length(modified_blocks: List[int]):
    return max([len(blocks[block]) for block in modified_blocks])


# Checks if the given bytes match the original value for the
# modified block k, considering the hash value of the signed ith test
def __return_if_correct_b(b: Union[int, Tuple[int, ...]], concatenation: Union[bytearray, List[str]], k_index: int,
                          i: int, k: int, sig_scheme: SigScheme, concatenate_strings: bool) \
        -> Union[Tuple[bool, str], None]:
    if concatenate_strings:
        bytes_char = b''
        for number in b:
            bytes_char += __int_to_bytes(number)

        try:
            string_now = bytes_char.decode('utf-8')
        except UnicodeError:
            return None

        concatenation[k_index] = string_now
        rebuilt_corrected_test = sig_scheme.get_digest(''.join(concatenation))

        output_result = string_now
    else:
        bytes_char = __int_to_bytes(b)

        if (b % 500000) == 0:
            logger.log_correction_progress(b)

        hash_k = bytearray(sig_scheme.get_digest(bytes_char))
        concatenation[k_index:(k_index + sig_scheme.digest_size_bytes)] = hash_k

        rebuilt_corrected_test = sig_scheme.get_digest(concatenation)

        output_result = bytes_char.decode('utf-8')

    if rebuilt_corrected_test == hashed_tests[i]:
        return not corrected[k], output_result


# Converts an integer to a bytes object
def __int_to_bytes(number: int) -> bytes:
    return number.to_bytes((len(bin(number)[2:]) + 7) // 8, 'big')


# Return the number of cores (physycal of virtual) available for use by the program process
# https://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-using-python
def __available_cpu_count():
    """ Number of available virtual or physical CPUs on this system, i.e.
    user/real as output by time(1) when called with an optimally scaling
    userspace-only program"""

    # cpuset
    # cpuset may restrict the number of *available* processors
    try:
        m = re.search(r'(?m)^Cpus_allowed:\s*(.*)$',
                      open('/proc/self/status').read())
        if m:
            res = bin(int(m.group(1).replace(',', ''), 16)).count('1')
            if res > 0:
                return res
    except IOError:
        pass

    # Python 2.6+
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except (ImportError, NotImplementedError):
        pass

    # Linux
    try:
        res = open('/proc/cpuinfo').read().count('processor\t:')

        if res > 0:
            return res
    except IOError:
        pass

    raise Exception('Can not determine number of CPUs on this system')
