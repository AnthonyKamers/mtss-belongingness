import json
from timeit import default_timer as timer
from typing import Tuple

import typer

from performance_utils import to_ms
from mtsssigner.cffs.cff_utils import parse_file
from mtsssigner.signature_scheme import SigScheme, ALGORITHM, HASH
from mtsssigner.signer import pre_sign, sign_raw
from mtsssigner.utils.file_and_block_utils import write_signature_to_file
from sig_ver_all import PATH_KEY, PATH_MSG, FILES, D_FILES, HASHES

app = typer.Typer()

QTD_ITERATION = 100
CONCATENATE_STRINGS = True

SIG_ALGORITHMS = [
    (ALGORITHM.DILITHIUM2, PATH_KEY + "dilithium_2_priv.key", PATH_KEY + "dilithium_2_pub.key"),
    (ALGORITHM.DILITHIUM3, PATH_KEY + "dilithium_3_priv.key", PATH_KEY + "dilithium_3_pub.key"),
    (ALGORITHM.DILITHIUM5, PATH_KEY + "dilithium_5_priv.key", PATH_KEY + "dilithium_5_pub.key"),
]

TABLE_NAME = "sig-time-performance"
OUTPUT_JSON = f"performance/output/{TABLE_NAME}.json"
OUTPUT_TABLE = f"performance/output/{TABLE_NAME}.tex"
LABEL_LATEX_TABLE = f"table:{TABLE_NAME}"
TABLE_CAPTION = '''Performance and output size of \\texttt{MTSS}($\\Sigma, \\H, \\M$).\\texttt{Sig} for several choices 
of $\\H$ and security parameters after NIST, using files with different $n$. The top values are using $\\M = $ $2$-CFF(
$25, 125$); the middle is using $\\M = $ $2$-CFF($49, 2401$); the bottom is using $\\M = $ $3$-CFF($121, 14641$). All
values are using $\\Sigma$ as ML-DSA. The values at the top corner left of the values are $\\Sigma$.\\texttt{Sig}.'''

KEY_MTSS = "mtss"
KEY_RAW = "raw"
KEY_BYTES_MTSS = "bytes-mtss"
KEY_BYTES_RAW = "bytes-raw"

data_test = {
    "100_dilitihum2": {
        "sha256": {
            "sign-mtss": "",
            "sign-raw": "",
            "bytes-mtss": "",
            "bytes-raw": ""
        },
    },
}

data = {}


# default command
@app.command()
def run():
    global data

    # necessary to call before the tests
    parse_file()

    for k, file in enumerate(FILES):
        for alg, priv, pub in SIG_ALGORITHMS:
            key_data = f'{file}_{alg.value}'
            data[key_data] = {}

            path_file = PATH_MSG + file
            d = D_FILES[k]

            print(f'running {file} for {alg.value}')

            for hash_function in HASHES:
                sig_scheme = SigScheme(alg, hash_function)

                result_mtss, bytes_mtss = sign_mtss_test(sig_scheme, priv, path_file, d)
                result_raw, bytes_raw = sign_raw_test(sig_scheme, priv, path_file)

                data[key_data][hash_function.value] = {
                    KEY_MTSS: result_mtss,
                    KEY_RAW: result_raw,
                    KEY_BYTES_MTSS: bytes_mtss,
                    KEY_BYTES_RAW: bytes_raw
                }

    # save output to json and save to latex table
    generate_output()
    generate_table_latex()


@app.command()
def table_from_file(path: str = OUTPUT_JSON):
    read_from_json(path)
    generate_table_latex()


def sign_mtss_test(sig_scheme: SigScheme, priv: str, file: str, d: int) -> Tuple[float, int]:
    result = 0
    signature = None
    for i in range(QTD_ITERATION):
        arguments = pre_sign(sig_scheme, file, priv, d, concatenate_strings=CONCATENATE_STRINGS)
        start = timer()
        signature = sign_raw(*arguments)
        end = timer()

        if result == 0:
            result = to_ms(start, end)
        else:
            result = round((result + to_ms(start, end)) / 2, 2)

        # save in disk only the first signature
        if i == 0:
            write_signature_to_file(signature, file)

    return result, len(signature)


def sign_raw_test(sig_scheme: SigScheme, priv, file: str) -> Tuple[float, int]:
    result = 0
    private_bytes = sig_scheme.get_private_key(priv)
    signature = None

    with open(file, "rb") as f:
        message_bytes = f.read()

    for i in range(QTD_ITERATION):
        start = timer()
        signature = sig_scheme.sign(private_bytes, message_bytes)
        end = timer()

        if result == 0:
            result = to_ms(start, end)
        else:
            result = round((result + to_ms(start, end)) / 2, 2)

        # save in disk only the first signature
        if i == 0:
            write_signature_to_file(signature, file, is_raw=True)

    return result, len(signature)


def read_from_json(path: str = OUTPUT_JSON):
    global data
    with open(path, "r") as file:
        data = json.load(file)


def generate_output():
    with open(OUTPUT_JSON, "w") as file:
        file.write(json.dumps(data, indent=4))


def generate_table_latex():
    header = '''
    \\begin{table*}[ht]
      \\setlength{\\tabcolsep}{10pt}
      \\centering
      \\caption{%s}
      \\begin{tabular}{crrrrrrrrr}
        \\toprule
            \\multicolumn{1}{r}{\\multirow{5}{*}{NIST}}
            & \\multicolumn{6}{c}{\\textsc{Sig} time (ms)}
            & \\multicolumn{2}{c}{\\multirow{3}{*}{$|\\sigma|$ (bytes)}} \\\\
        \\cmidrule{2-7}
            & \\multicolumn{2}{c}{SHA-2}
            & \\multicolumn{2}{c}{SHA-3}
            & \\multicolumn{2}{c}{BLAKE}
            & \\\\
        \\cmidrule{2-7}
        & 256 & 512 & 256 & 512 & 2s & 2b & 256 & 512 \\\\
    ''' % TABLE_CAPTION

    footer = '''
    \\bottomrule
      \\end{tabular}
      \\label{%s}
    \\end{table*}
    ''' % LABEL_LATEX_TABLE

    body = ""
    counter = 0
    for key, value in data.items():
        if counter % 3 == 0:
            body += "\t\\cmidrule{1-9}\n"

        body += f'\t {"I" * ((counter % 3) + 1)} & '

        counter += 1

        for _, mapping in value.items():
            body += '\\raisebox{0.2em}{\\hspace{-0.5em}\\small %s} %s & ' % (mapping[KEY_RAW], mapping[KEY_MTSS])

        # it will need two values more: bytes-mtss (256/512) and bytes-raw (256/512)
        sha256 = value[HASH.SHA256.value]
        sha512 = value[HASH.SHA512.value]
        body += '\\raisebox{0.2em}{\\hspace{-0.5em}\\small %s} %s & ' % (sha256[KEY_BYTES_RAW], sha256[KEY_BYTES_MTSS])
        body += '\\raisebox{0.2em}{\\hspace{-0.5em}\\small %s} %s \\\\\n' % (sha512[KEY_BYTES_RAW], sha512[KEY_BYTES_MTSS])

    # write table to latex file
    with open(OUTPUT_TABLE, "w") as file:
        file.write(header)
        file.write(body)
        file.write(footer)


if __name__ == "__main__":
    app()
