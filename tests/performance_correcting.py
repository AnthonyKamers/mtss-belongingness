import math
from timeit import default_timer as timer

import matplotlib.pyplot as plt

# procedure necessary to import from root
import sys

sys.path.append('.')

from mtsssigner.signature_scheme import HASH, ALGORITHM
from mtsssigner.verifier import *

QTD_ITERATION = 1

K = 3
HASH_FUNCTION = HASH.BLAKE2B
SIG_ALGORITHM = ALGORITHM.RSA

KEY_FILE = "keys/rsa_2048_pub.pem"

FILE_PATH = "msg/correct/i/"
FILE_EXTENSION = ".txt"
FILES = [
    "4096_1", "4096_4", "4096_7"
]

SIGNATURE_PATH = "msg/sign/q/4096_signature.mts"


def main():
    sig_scheme = SigScheme(SIG_ALGORITHM, HASH_FUNCTION)

    results = {}
    for file in FILES:
        results[file] = 0

    for index, file in enumerate(FILES):
        file_path = FILE_PATH + file + FILE_EXTENSION

        for i in range(1, QTD_ITERATION + 1):
            verify_result = verify(sig_scheme, file_path, SIGNATURE_PATH, KEY_FILE)

            start = timer()
            verify_and_correct(verify_result, sig_scheme, file_path, False)
            end = timer()

            diff = end - start

            results[file] += math.floor((diff * 1000) / i)

    generate_graph(results)


def generate_graph(results):
    fig, ax = plt.subplots()

    bars = [1, 4, 7]
    time = list(results.values())

    bar_labels = bars

    ax.bar(bars, time, color='b', align='center', label=bar_labels)

    ax.set_ylabel('Time (ms)')
    ax.set_xlabel('Number of modified blocks |I|')
    ax.set_title('Correction time')

    # plt.show()
    plt.savefig("performance_correcting.png", bbox_inches='tight')


if __name__ == "__main__":
    main()
