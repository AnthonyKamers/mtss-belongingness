import os
import sys

sys.path.append('.')

from timeit import default_timer as timer

from mtsssigner.signature_scheme import ALGORITHM, HASH
from mtsssigner.cffs.cff_utils import parse_file
from mtsssigner.signer import *
from mtsssigner.utils.file_and_block_utils import get_signature_file_path, write_signature_to_file
from mtsssigner.verifier import pre_verify, verify_raw

PATH_BENCHMARK = "performance/output/benchmark"
PATH_KEY = "keys/"
PATH_MSG = "msg/n/txt/"

FILES = ["100.txt", "1000.txt", "10000.txt"]
FILES_MODIFIED = ["100_1.txt", "1000_1.txt", "10000_1.txt"]
D_FILES = [2, 2, 3]
T_FILES = [25, 49, 121]
N_CFF_FILES = [125, 2401, 14641]

QTD_ITERATION = 1
HASHES = [
    HASH.SHA256,
    HASH.SHA512,
    HASH.SHA3_256,
    HASH.SHA3_512,
    HASH.BLAKE2S,
    HASH.BLAKE2B
]
SIG_ALGORITHMS = [
    (ALGORITHM.RSA, "rsa_2048_priv.pem", "rsa_2048_pub.pem"),
    (ALGORITHM.RSA, "rsa_4096_priv.pem", "rsa_4096_pub.pem"),
    # (ALGORITHM.ED25519, "ed25519_priv.pem", "ed25519_pub.pem"),
    (ALGORITHM.DILITHIUM2, "dilithium_2_priv.key", "dilithium_2_pub.key"),
    (ALGORITHM.DILITHIUM3, "dilithium_3_priv.key", "dilithium_3_pub.key"),
    (ALGORITHM.DILITHIUM5, "dilithium_5_priv.key", "dilithium_5_pub.key"),
    (ALGORITHM.FALCON512, "falcon_512_priv.key", "falcon_512_pub.key"),
    (ALGORITHM.FALCON1024, "falcon_1024_priv.key", "falcon_1024_pub.key"),
]


def main():
    # necessary to call before the tests
    parse_file()

    for alg, priv, pub in SIG_ALGORITHMS:
        for i, file in enumerate(FILES):
            file_modified = FILES_MODIFIED[i]
            d = D_FILES[i]

            for hash_function in HASHES:
                sig_scheme = SigScheme(alg, hash_function)
                aux(sig_scheme, priv, pub, file, file_modified, d)


def aux(sig_scheme: SigScheme, path_priv: str, path_pub: str, file: str, file_modified: str, d: int):
    sign_mtss_test(sig_scheme, path_priv, file, d)
    verify_mtss_test(sig_scheme, path_pub, file)
    locate_mtss_test(sig_scheme, path_pub, file_modified)
    sign_raw_test(sig_scheme, path_priv, file)
    verify_raw_test(sig_scheme, path_pub, file)


def sign_mtss_test(sig_scheme: SigScheme, priv: str, file: str, d: int):
    log_begin(sig_scheme, "sign-mtss", priv, file)
    results = []
    for i in range(QTD_ITERATION):
        arguments = pre_sign(sig_scheme, PATH_MSG + file, PATH_KEY + priv, d)
        start = timer()
        signature = sign_raw(*arguments)
        end = timer()

        results.append(end - start)

        # save in disk the last signature
        if i == QTD_ITERATION - 1:
            write_signature_to_file(signature, PATH_MSG + file)

    write_statistics_to_file(sig_scheme, priv, "sign-mtss", results, file)
    log_end(sig_scheme, "sign-mtss", priv, file)


def verify_mtss_test(sig_scheme: SigScheme, pub, file: str, operation="verify-mtss"):
    log_begin(sig_scheme, operation, pub, file)

    if operation == "verify-mtss":
        file_verify = PATH_MSG + file
        file_signature = get_signature_file_path(file_verify, is_raw=False)
    elif operation == "locate-mtss":
        file_verify = file
        file_signed = file.replace("_1", "")
        file_signature = get_signature_file_path(file_signed, is_raw=False)
    else:
        raise Exception("Invalid operation")

    results = []
    for i in range(QTD_ITERATION):
        arguments = pre_verify(file_verify, file_signature, sig_scheme, PATH_KEY + pub)
        start = timer()
        result, modified_blocks = verify_raw(*arguments)

        if not result:
            raise Exception("Signature verification is invalid")

        end = timer()

        results.append(end - start)

    write_statistics_to_file(sig_scheme, pub, operation, results, file)
    log_end(sig_scheme, operation, pub, file)


def locate_mtss_test(sig_scheme: SigScheme, pub, file_modified: str):
    verify_mtss_test(sig_scheme, pub, PATH_MSG + file_modified, "locate-mtss")


def sign_raw_test(sig_scheme: SigScheme, priv, file: str):
    log_begin(sig_scheme, "sign-raw", priv, file)
    private_bytes = sig_scheme.get_private_key(PATH_KEY + priv)

    with open(PATH_MSG + file, "rb") as f:
        message_bytes = f.read()

    results = []
    for i in range(QTD_ITERATION):
        start = timer()
        signature = sig_scheme.sign(private_bytes, message_bytes)
        end = timer()

        results.append(end - start)

        # save in disk the last signature
        if i == QTD_ITERATION - 1:
            write_signature_to_file(signature, PATH_MSG + file, is_raw=True)

    write_statistics_to_file(sig_scheme, priv, "sign-raw", results, file)
    log_end(sig_scheme, "sign-raw", priv, file)


def verify_raw_test(sig_scheme: SigScheme, pub, file: str):
    log_begin(sig_scheme, "verify-raw", pub, file)

    with open(PATH_MSG + file, "rb") as f:
        message_bytes = f.read()

    path_signed = get_signature_file_path(PATH_MSG + file, is_raw=True)
    with open(path_signed, "rb") as f:
        signature_bytes = f.read()

    public_bytes = sig_scheme.get_public_key(PATH_KEY + pub)

    results = []
    for i in range(QTD_ITERATION):
        start = timer()
        result = sig_scheme.verify(public_bytes, message_bytes, signature_bytes)
        end = timer()

        if not result:
            raise Exception("Raw signature verification is invalid")

        results.append(end - start)

    write_statistics_to_file(sig_scheme, pub, "verify-raw", results, file)
    log_end(sig_scheme, "verify-raw", pub, file)


def write_statistics_to_file(sig_scheme: SigScheme, key: str, operation, results, file_used: str):
    alg = sig_scheme.sig_algorithm
    hash_function = sig_scheme.hash_function
    key_used = key.split("_")[1]
    file_log = os.path.basename(file_used)

    with open(f"{PATH_BENCHMARK}/{file_log}-{alg}-{key_used}_{hash_function}_{operation}.txt", "w") as file:
        for line in results:
            file.write(str(line) + "\n")


def log_generic(sig_scheme: SigScheme, operation: str, key: str, status: str, file: str):
    alg = sig_scheme.sig_algorithm
    hash_function = sig_scheme.hash_function
    key_used = key.split("_")[1]

    print(f"{status} file {file} for {operation} with {alg} ({key_used}) and {hash_function}")


def log_begin(sig_scheme: SigScheme, operation: str, key: str, file: str):
    log_generic(sig_scheme, operation, key, "Started", file)


def log_end(sig_scheme: SigScheme, operation: str, key: str, file: str):
    log_generic(sig_scheme, operation, key, "Finished", file)


if __name__ == "__main__":
    main()
