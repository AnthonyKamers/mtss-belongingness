import math
from timeit import default_timer as timer

import numpy as np
from matplotlib import pyplot as plt

from mtsssigner.signer import *

QTD_ITERATION = 100

K = 4
# MSG_FILE = "msg/sign/q/4096.txt"
HASH_FUNCTION = "BLAKE2B"
SIG_ALGORITHM = "PKCS#1 v1.5"

KEY_FILE = "keys/rsa_2048_priv.pem"

FILE_PATH = "msg/sign/q/"
FILE_EXTENSION = ".txt"
FILES = [
    "2401", "4096", "6561", "14641"
]

FILE_PATH_XML = "msg/xml/"
FILE_EXTENSION_XML = ".xml"
FILES_XML = [
    "2401", "4096", "6561"
]

DEBUG = False


def iterate_files(results, sig_scheme, files):
    for index, file in enumerate(files):
        results["pre-sign"].insert(index, 0)
        results["sign"].insert(index, 0)

        for i in range(1, QTD_ITERATION + 1):
            # MTSS
            start = timer()
            arguments = pre_sign(sig_scheme, file, KEY_FILE, K)
            end = timer()
            diff_pre_sign = end - start

            start = timer()
            sign_raw(*arguments)
            end = timer()
            diff_mtss = end - start

            results["pre-sign"][index] += math.floor((diff_pre_sign * 1000) / i)
            results["sign"][index] += math.floor((diff_mtss * 1000) / i)

        if DEBUG:
            print(f'finished file {file}')


def main():
    sig_scheme = SigScheme(SIG_ALGORITHM, HASH_FUNCTION)

    results = {
        "pre-sign": [],
        "sign": [],
    }

    files_text = list(map(lambda x: FILE_PATH + x + FILE_EXTENSION, FILES))
    files_xml = list(map(lambda x: FILE_PATH_XML + x + FILE_EXTENSION_XML, FILES_XML))
    files = files_text + files_xml

    iterate_files(results, sig_scheme, files)

    generate_file(results)
    # generate_graph(results)


def generate_file(results):
    files_text = list(map(lambda x: x + FILE_EXTENSION, FILES))
    files_xml = list(map(lambda x: x + FILE_EXTENSION_XML, FILES_XML))
    files = files_text + files_xml

    for i, file in enumerate(files):
        print(file, results["pre-sign"][i], results["sign"][i])


def generate_graph(results):
    files_text = list(map(lambda x: x + FILE_EXTENSION, FILES))
    files_xml = list(map(lambda x: x + FILE_EXTENSION_XML, FILES_XML))
    files = files_text + files_xml
    width = 0.6

    fig, ax = plt.subplots()
    bottom = np.zeros(len(files))
    for stage, stage_results in results.items():
        p = ax.bar(files, stage_results, width, label=stage, bottom=bottom)
        bottom += stage_results

        ax.bar_label(p, label_type='center')

    ax.set_title('Sign performance between stages')
    ax.legend()

    # plt.show()
    plt.savefig("sign_performance_stages1.png", bbox_inches='tight')


if __name__ == "__main__":
    main()
