import json
from timeit import default_timer as timer

import typer

from performance_utils import to_ms
from mtsssigner.cffs.cff_utils import parse_file
from mtsssigner.signature_scheme import SigScheme, ALGORITHM
from mtsssigner.signer import sign
from mtsssigner.utils.file_and_block_utils import write_signature_to_file, get_signature_file_path
from mtsssigner.verifier import pre_verify, verify_raw
from sig_ver_all import PATH_KEY, PATH_MSG, FILES, D_FILES, HASHES, FILES_MODIFIED

app = typer.Typer()

QTD_ITERATION = 100
CONCATENATE_STRINGS = True

SIG_ALGORITHMS = [
    (ALGORITHM.DILITHIUM2, PATH_KEY + "dilithium_2_priv.key", PATH_KEY + "dilithium_2_pub.key"),
    (ALGORITHM.DILITHIUM3, PATH_KEY + "dilithium_3_priv.key", PATH_KEY + "dilithium_3_pub.key"),
    (ALGORITHM.DILITHIUM5, PATH_KEY + "dilithium_5_priv.key", PATH_KEY + "dilithium_5_pub.key"),
]

TABLE_NAME = "ver-time-performance"
OUTPUT_JSON = f"performance/output/{TABLE_NAME}.json"
OUTPUT_TABLE = f"performance/output/{TABLE_NAME}.tex"
LABEL_LATEX_TABLE = f"table:{TABLE_NAME}"
TABLE_CAPTION = '''Performance of \\texttt{MTSS}($\\Sigma, \\H, \\M$).\\texttt{Ver} for several choices 
of $\\H$ and security parameters after NIST, using files with different $n$. The top values are using $\\M 
= $ $2$-CFF($25, 125$); the middle is using $\\M = $ $2$-CFF($49, 2401$); the bottom is using $\\M = $
$3$-CFF($121, 14641$). All values are using $\\Sigma$ as ML-DSA. The values at the center of the cells are \\texttt{
MTSS}.\\texttt{Ver} with $|I| = 1$; values at the top corner right are with $|I| = 0$; and the top corner left of the
values are $\\Sigma$.\\texttt{Ver}.'''

KEY_VERIFY = "verify-mtss"
KEY_LOCATE = "locate-mtss"
KEY_RAW = "verify-raw"

data_test = {
    "100_dilitihum2": {
        "sha256": {
            "verify-mtss": "",
            "locate-mtss": "",
            "verify-raw": ""
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
        d = D_FILES[k]
        path_file = PATH_MSG + file
        path_modified = PATH_MSG + FILES_MODIFIED[k]

        with open(path_file, "rb") as f:
            message_bytes = f.read()

        for alg, priv, pub in SIG_ALGORITHMS:
            key_data = f'{file}_{alg.value}'
            data[key_data] = {}

            with open(priv, "rb") as f:
                priv_bytes = f.read()

            print(f'running {file} for {alg.value}')

            for hash_function in HASHES:
                sig_scheme = SigScheme(alg, hash_function)

                # first, we need to sign once (our algorithms take signatures from disk)
                # sign mtss
                signature = sign(sig_scheme, path_file, priv, d, concatenate_strings=CONCATENATE_STRINGS)
                write_signature_to_file(signature, path_file, False)

                # verify/locate mtss
                result_verify = verify_mtss_test(sig_scheme, pub, path_file)
                result_locate = locate_mtss_test(sig_scheme, pub, path_modified)

                # sign raw
                signature_raw = sig_scheme.sign(priv_bytes, message_bytes)
                write_signature_to_file(signature_raw, path_file, True)

                # verify raw
                result_raw = verify_raw_test(sig_scheme, pub, path_file)

                data[key_data][hash_function.value] = {
                    KEY_VERIFY: result_verify,
                    KEY_LOCATE: result_locate,
                    KEY_RAW: result_raw
                }

    # save output to json and save to latex table
    generate_output()
    generate_table_latex()


@app.command()
def table_from_file(path: str = OUTPUT_JSON):
    read_from_json(path)
    generate_table_latex()


def verify_mtss_test(sig_scheme: SigScheme, pub, file: str, operation="verify-mtss") -> float:
    if operation == "verify-mtss":
        file_verify = file
        file_signature = get_signature_file_path(file_verify, is_raw=False)
    elif operation == "locate-mtss":
        file_verify = file
        file_signed = file.replace("_1", "")
        file_signature = get_signature_file_path(file_signed, is_raw=False)
    else:
        raise Exception("Invalid operation")

    result = 0
    for i in range(QTD_ITERATION):
        arguments = pre_verify(file_verify, file_signature, sig_scheme, pub, concatenate_strings=CONCATENATE_STRINGS)
        start = timer()
        result, modified_blocks = verify_raw(*arguments)
        end = timer()

        if not result:
            raise Exception("Signature verification is invalid")

        if result == 0:
            result = to_ms(start, end)
        else:
            result = round((result + to_ms(start, end)) / 2, 2)

    return result


def locate_mtss_test(sig_scheme: SigScheme, pub, file_modified: str) -> float:
    return verify_mtss_test(sig_scheme, pub, file_modified, "locate-mtss")


def verify_raw_test(sig_scheme: SigScheme, pub, file: str) -> float:
    with open(file, "rb") as f:
        message_bytes = f.read()

    path_signed = get_signature_file_path(file, is_raw=True)
    with open(path_signed, "rb") as f:
        signature_bytes = f.read()

    public_bytes = sig_scheme.get_public_key(pub)

    result = 0
    for i in range(QTD_ITERATION):
        start = timer()
        result_verification = sig_scheme.verify(public_bytes, message_bytes, signature_bytes)
        end = timer()

        if not result_verification:
            raise Exception("Raw signature verification is invalid")

        if result == 0:
            result = to_ms(start, end)
        else:
            result = round((result + to_ms(start, end)) / 2, 2)

    return result


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
      \\begin{tabular}{ccccccc}
        \\toprule
            \\multicolumn{1}{r}{\\multirow{5}{*}{NIST}}
            & \\multicolumn{6}{c}{\\textsc{Ver} time (ms)} \\\\
        \\cmidrule{2-7}
            & \\multicolumn{2}{c}{SHA-2}
            & \\multicolumn{2}{c}{SHA-3}
            & \\multicolumn{2}{c}{BLAKE} \\\\
        \\cmidrule{2-7}
        & 256 & 512 & 256 & 512 & 2s & 2b \\\\
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
            body += "\t\\cmidrule{1-7}\n"

        body += f'\t {"I" * ((counter % 3) + 1)} & '

        counter += 1

        for _, mapping in value.items():
            body += ('\\raisebox{0.2em}{\\small %s} %s \\raisebox{0.2em}{\\small %s} & ' %
                     (mapping[KEY_RAW], mapping[KEY_LOCATE], mapping[KEY_VERIFY]))

        # remove last two characeters from body
        body = body[:-2] + "\\\\\n"

    # write table to latex file
    with open(OUTPUT_TABLE, "w") as file:
        file.write(header)
        file.write(body)
        file.write(footer)


if __name__ == "__main__":
    app()
