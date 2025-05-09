import json
from pathlib import Path
from typing import Tuple, List, Union, Any

import typer
from Crypto.PublicKey.ECC import EccKey
from Crypto.PublicKey.RSA import RsaKey

from mtsssigner.cffs.cff_utils import ignore_columns_cff
from mtsssigner.signature_scheme import ALGORITHM, HASH, DIRECTORY_BLOCKS, SigScheme, D_BYTES_LENGTH
from mtsssigner.utils.file_and_block_utils import read_cff_from_file

index_possible_tests = 0
possible_tests = []
cff = None
blocks_file = None
signature = None

CONCATENATE_STRINGS = True

app = typer.Typer()


def clear_globals():
    global index_possible_tests, possible_tests, cff, blocks_file, signature

    index_possible_tests = 0
    possible_tests = []
    cff = None
    blocks_file = None
    signature = None


def block_ver(m_j, pk, Y, sig_scheme: SigScheme, concatenate_strings):
    signature, i, M, k = Y

    # step 1
    t = signature[:-int(sig_scheme.signature_length_bytes)]
    t_signature = signature[-int(sig_scheme.signature_length_bytes):]

    verification_result = sig_scheme.verify(pk, t, t_signature)
    if not verification_result:
        return False

    t_without_d = t[:-D_BYTES_LENGTH]

    # step 2
    M.insert(k, m_j)

    # step 3
    concatenation = "" if concatenate_strings else bytes()
    for m in M:
        if concatenate_strings:
            concatenation += str(m)
        else:
            concatenation += sig_scheme.get_digest(m)

    # step 4
    h = sig_scheme.get_digest(concatenation)

    # step 5
    digest_size = sig_scheme.digest_size_bytes
    test_hash = t_without_d[i * digest_size: (i + 1) * digest_size]

    if h != test_hash:
        return False

    return True


def client_1(algorithm: ALGORITHM, hash_func: HASH, public_key_path: Path,
             hash_message: str, block_message: str, index_block: int):
    sig_scheme = SigScheme(algorithm, hash_func)
    public_key = sig_scheme.get_public_key(str(public_key_path))

    X = (hash_message, index_block, sig_scheme, public_key, block_message)
    return X


def client_2(X: Tuple[str, int, SigScheme, Union[RsaKey, EccKey], str], Y: Tuple[bytes, int, List[str], int],
             concatenate_strings: bool = CONCATENATE_STRINGS):
    h_m, j, sig_scheme, public_key, block_message = X
    return block_ver(block_message, public_key, Y, sig_scheme, concatenate_strings)


@app.command()
def protocol(algorithm: ALGORITHM, hash_func: HASH, public_key_path: Path,
             hash_message: str, block_message: str, index_block: int,
             concatenate_strings: bool = CONCATENATE_STRINGS):
    flag = False

    X = client_1(algorithm, hash_func, public_key_path, hash_message, block_message, index_block)

    while not flag:
        Y = server(X)

        if Y is None:
            break

        flag = client_2(X, Y, concatenate_strings)

    print(flag)
    clear_globals()


def server(X: Tuple[str, int, SigScheme, Union[RsaKey, EccKey], str]) -> tuple[bytes, int, Any, Any] | None:
    def get_blocks_from_test() -> Tuple[List[str], int]:
        # find indexes in which the test is 1
        indexes = [i for i, x in enumerate(test_now) if x == 1]

        # get the value of the blocks (appearing in the indexes and if the index is not j)
        blocks_test = [blocks_file[str(i)] for i in indexes if i != j]
        return blocks_test, indexes.index(j)

    global possible_tests, index_possible_tests, cff, blocks_file, signature

    h_m, j, _, _, _ = X

    if cff is None:
        # read blocks division from disk
        with open(f"{DIRECTORY_BLOCKS}/{h_m}.json", "r") as file:
            file_bytes = file.read()

        # read signature from disk
        with open(f"{DIRECTORY_BLOCKS}/{h_m}.sig", "rb") as file:
            signature = file.read()

        blocks_file = json.loads(file_bytes)

        t, n_file, n_expected, d = blocks_file["cff"].values()

        # read CFF from disk and ignore last columns (if necessary)
        cff = read_cff_from_file(t, n_expected, d)
        cff = ignore_columns_cff(cff, n_expected - n_file)

        for test in cff:
            if test[j] == 1:
                possible_tests.append(test)

    if len(possible_tests) <= index_possible_tests:
        return None

    test_now = possible_tests[index_possible_tests]
    blocks_from_test, k = get_blocks_from_test()

    Y = (signature, index_possible_tests, blocks_from_test, k)

    index_possible_tests += 1

    return Y


if __name__ == "__main__":
    app()

    # example working
    # key = keys/rsa_2048_pub.pem
    # hash_message = "43a39a552c4d381f0ccba7a5b9ef1d2c19257287b31df8a8ea29b1a330a1fae3"
    # block_message = "1|sett"
    # index_block = 0
