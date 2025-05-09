import json
from timeit import default_timer as timer

import typer

from performance_utils import to_ms
from mtsssigner.cffs.cff_utils import parse_file
from mtsssigner.signature_scheme import SigScheme, ALGORITHM, HASH
from mtsssigner.signer import sign
from mtsssigner.utils.file_and_block_utils import write_signature_to_file, get_signature_file_path
from mtsssigner.verifier import pre_verify, verify_raw, verify_and_correct
from sig_ver_all import PATH_KEY

app = typer.Typer()

QTD_ITERATION = 100
CONCATENATE_STRINGS = True
OUTPUT_TXT = 'performance/output/correct_s.txt'

SIG_ALGORITHM = (ALGORITHM.DILITHIUM2, PATH_KEY + "dilithium_2_priv.key", PATH_KEY + "dilithium_2_pub.key")
HASH_FUCNTION = HASH.BLAKE2B

PATH_MSG = 'msg/correct/s/'
FILES_SIGN = [
    '4096_1',
    '4096_2',
    # '4096_3',
    # '4096_4',
    # '4096_5',
]
FILES_CORRECT = [
    '4096_1_1',
    '4096_2_1',
    # '4096_3_1',
    # '4096_4_1',
    # '4096_5_1',
]
D = 7
EXTENSION_FILE = '.txt'

values = [0, 0]


def main():
    # necessary to call before the tests
    parse_file()

    for k, file in enumerate(FILES_SIGN):
        file_sign = PATH_MSG + file + EXTENSION_FILE
        file_correct = PATH_MSG + FILES_CORRECT[k] + EXTENSION_FILE

        alg, priv, pub = SIG_ALGORITHM

        print(f'running {file} for {alg.value}')

        sig_scheme = SigScheme(alg, HASH_FUCNTION)

        # first, we need to sign once (our algorithms take signatures from disk)
        # sign mtss
        signature = sign(sig_scheme, file_sign, priv, D, concatenate_strings=CONCATENATE_STRINGS)
        write_signature_to_file(signature, file_sign, False)

        # locate mtss
        result_locate = locate_mtss_test(sig_scheme, pub, file_correct)

        for i in range(QTD_ITERATION):
            # correct
            start = timer()
            result_correct = verify_and_correct(result_locate, sig_scheme, file_correct, CONCATENATE_STRINGS)
            end = timer()

            _, _, valid = result_correct

            if not valid:
                raise Exception("Signature correction is invalid")

            result = to_ms(start, end)

            if values[k] == 0:
                values[k] = result
            else:
                values[k] = round((values[k] + result) / 2, 2)

    output = ''
    output += f'files _s (with |I| = 1): {FILES_SIGN}\n'
    output += f'result                 : {values}'

    print(output)
    with open(OUTPUT_TXT, 'w') as f:
        f.write(output)


def verify_mtss_test(sig_scheme: SigScheme, pub, file: str, operation="verify-mtss") -> float:
    if operation == "verify-mtss":
        file_verify = file
        file_signature = get_signature_file_path(file_verify, is_raw=False)
    elif operation == "locate-mtss":
        file_verify = file
        file_signed = file.replace("_1.txt", ".txt")
        file_signature = get_signature_file_path(file_signed, is_raw=False)
    else:
        raise Exception("Invalid operation")

    result_locate = None
    for i in range(QTD_ITERATION):
        arguments = pre_verify(file_verify, file_signature, sig_scheme, pub, concatenate_strings=CONCATENATE_STRINGS)
        result_locate = verify_raw(*arguments)

        if not result_locate[0]:
            raise Exception("Signature verification is invalid")
    return result_locate


def locate_mtss_test(sig_scheme: SigScheme, pub, file_modified: str) -> float:
    return verify_mtss_test(sig_scheme, pub, file_modified, "locate-mtss")


if __name__ == "__main__":
    main()
