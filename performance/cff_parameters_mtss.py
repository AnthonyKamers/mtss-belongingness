import json
from timeit import default_timer as timer

import typer

from performance_utils import to_ms
from mtsssigner.cffs.cff_utils import parse_file
from mtsssigner.utils.file_and_block_utils import write_signature_to_file, get_signature_file_path
from mtsssigner.signature_scheme import ALGORITHM, HASH, SigScheme
from mtsssigner.signer import sign_raw, pre_sign
from mtsssigner.verifier import pre_verify, verify_raw

PATH_MSG = "msg/sign/q/"
TOP_FILES = ["2401.txt", "6561.txt", "14641.txt", "28561.txt"]
D_TOP_FILES = [2, 2, 3, 4]

BOTTOM_FILE = "4096.txt"
D_BOTTOM_FILE = [1, 2, 7, 63]

QTD_ITERATION = 100
CONCATENATE_STRINGS = True

SIG_ALGORITHM = ALGORITHM.DILITHIUM2
HASH_ALGORITHM = HASH.BLAKE2B
PUB_KEY = "keys/dilithium_2_pub.key"
PRIV_KEY = "keys/dilithium_2_priv.key"

TABLE_NAME = "sign-locate-different-parameters"
OUTPUT_JSON_TOP = f"performance/output/top-{TABLE_NAME}.json"
OUTPUT_JSON_BOTTOM = f"performance/output/bottom-{TABLE_NAME}.json"
OUTPUT_TABLE = f"performance/output/{TABLE_NAME}.tex"
LABEL_LATEX_TABLE: str = f"table:{TABLE_NAME}"
TABLE_CAPTION = '''Performance of signature operations of MTSS(ML-DSA-I, BLAKE2b, $\\M$) for several choices of $\\M$,
plain text files of different sizes. For ease of notation, we use \\texttt{Ver$_0$} to denote \\texttt{Ver} with $|I| = 
0$, and \\texttt{Ver$_1$} to denote \\texttt{Ver} with $|I| = 1$.'''

top_data = {}
bottom_data = {}

app = typer.Typer()


@app.command()
def run():
    global top_data, bottom_data

    sig_scheme = SigScheme(SIG_ALGORITHM, HASH_ALGORITHM)
    parse_file()

    # top files
    for k, file in enumerate(TOP_FILES):
        print(f'running file {file}')

        d = D_TOP_FILES[k]
        path_file = PATH_MSG + file
        file_signature = get_signature_file_path(path_file, is_raw=False)

        aux(top_data, file, d, path_file, sig_scheme, file_signature)

    # bottom file
    print(f'running file {BOTTOM_FILE}')
    for k, d in enumerate(D_BOTTOM_FILE):
        path_file = PATH_MSG + BOTTOM_FILE
        file_signed = path_file.replace("_1", "")
        file_signature = get_signature_file_path(file_signed, is_raw=False)

        aux(bottom_data, BOTTOM_FILE, d, path_file, sig_scheme, file_signature)

    generate_output()
    generate_latex_table()


def aux(data_structure, file, d, path_file, sig_scheme, file_signature):
    key_data = f'{file}_{d}'

    locate_file = path_file.replace(".txt", "_1.txt")

    data_structure[key_data] = {
        "d": d,
        "message_size": len(open(path_file, "r").read()),
    }

    with open(path_file, "rb") as f:
        message_bytes = f.read()

    with open(PRIV_KEY, "rb") as f:
        priv_bytes = f.read()

    with open(PUB_KEY, "rb") as f:
        pub_bytes = f.read()

    for i in range(QTD_ITERATION):
        # sign MTSS
        parameters_sign = pre_sign(sig_scheme, path_file, PRIV_KEY, d, concatenate_strings=CONCATENATE_STRINGS)
        _, _, _, cff_dimensions, _, _, _, _ = parameters_sign
        t = cff_dimensions[0]
        n = cff_dimensions[1]
        q = cff_dimensions[3]
        k = cff_dimensions[4]

        start_signature = timer()
        signature = sign_raw(*parameters_sign)
        end_signature = timer()

        if i == 0:
            write_signature_to_file(signature, path_file, False)

        data_structure[key_data]['t'] = t
        data_structure[key_data]['n'] = n
        data_structure[key_data]['q'] = q
        data_structure[key_data]['k'] = k
        data_structure[key_data]['signature_size'] = len(signature)

        # sign raw
        signature_raw = sig_scheme.sign(priv_bytes, message_bytes)
        if i == 0:
            write_signature_to_file(signature_raw, path_file, True)

        # verify raw
        start_verify_raw = timer()
        result_raw = sig_scheme.verify(pub_bytes, message_bytes, signature_raw)
        end_verify_raw = timer()

        # verify (|I| = 0)
        parameters_verify = pre_verify(path_file, file_signature, sig_scheme, PUB_KEY,
                                       concatenate_strings=CONCATENATE_STRINGS)
        start_verify = timer()
        result_verify, _ = verify_raw(*parameters_verify)
        end_verify = timer()

        # locate (|I| = 1)
        parameters_locate = pre_verify(locate_file, file_signature, sig_scheme, PUB_KEY,
                                       concatenate_strings=CONCATENATE_STRINGS)
        start_locate = timer()
        result_locate, _ = verify_raw(*parameters_locate)
        end_locate = timer()

        if not result_raw:
            raise Exception("The signature is not valid! - raw")

        if not result_verify:
            raise Exception("The signature is not valid! - verify")

        if not result_locate:
            raise Exception("The signature is not valid! - locate")

        if i == 0:
            data_structure[key_data]['sign'] = to_ms(start_signature, end_signature)
            data_structure[key_data]['locate'] = to_ms(start_locate, end_locate)
            data_structure[key_data]['verify'] = to_ms(start_verify, end_verify)
            data_structure[key_data]['verify_raw'] = to_ms(start_verify_raw, end_verify_raw)
        else:
            data_structure[key_data]['sign'] = (data_structure[key_data]['sign'] + to_ms(start_signature,
                                                                                         end_signature)) / 2
            data_structure[key_data]['locate'] = (data_structure[key_data]['locate'] + to_ms(start_locate, end_locate)) / 2
            data_structure[key_data]['verify'] = (data_structure[key_data]['verify'] + to_ms(start_verify, end_verify)) / 2
            data_structure[key_data]['verify_raw'] = ((data_structure[key_data]['verify_raw'] +
                                                       to_ms(start_verify_raw, end_verify_raw)) / 2)


@app.command()
def table_from_file(path_top: str = OUTPUT_JSON_TOP, path_bottom: str = OUTPUT_JSON_BOTTOM):
    read_from_json(path_top, path_bottom)
    generate_latex_table()


def read_from_json(path_top: str, path_bottom: str):
    global top_data, bottom_data

    with open(path_top, "r") as file:
        top_data = json.load(file)

    with open(path_bottom, "r") as file:
        bottom_data = json.load(file)


def generate_output():
    global top_data, bottom_data

    with open(OUTPUT_JSON_TOP, "w") as file:
        file.write(json.dumps(top_data, indent=4))

    with open(OUTPUT_JSON_BOTTOM, "w") as file:
        file.write(json.dumps(bottom_data, indent=4))


def generate_latex_table():
    global top_data, bottom_data

    def data_to_body(data_structure, body_now, is_bottom=False):
        counter = 0
        for key, value in data_structure.items():
            d = value['d']
            k = value['k']
            q = value['q']
            t = value['t']
            n = value['n']

            if k is None and q is None:
                k = '-'
                q = '-'

            message_size = value['message_size']
            signature_size = value['signature_size']
            sign = value['sign']
            locate = value['locate']
            verify_time = value['verify']
            verify_raw_time = value['verify_raw']

            if is_bottom:
                if counter == 0:
                    body_now += '''
                    \t%s & %s & %s & %s & \\multirow{4}{*}{%s} & \\multirow{4}{*}{%s} & %s & %s & %s & %s & %s \\\\
                    ''' % (d, k, q, t, n, message_size, signature_size, sign, locate, verify_time, verify_raw_time)
                else:
                    body_now += (
                        f'\t{d} & {k} & {q} & {t} &  &  & {signature_size} & {sign} & {locate} & {verify_time} &'
                        f'{verify_raw_time} \\\\\n')
            else:
                body_now += (
                    f'\t{d} & {k} & {q} & {t} & {n} & {message_size} & {signature_size} & {sign} & {locate} &'
                    f'{verify_time} & {verify_raw_time} \\\\\n')
            counter += 1
        return body_now

    header = '''
    \\begin{table*}[htbp]
        \\setlength{\\tabcolsep}{10pt}
        \\centering
        \\caption{%s}
        \\begin{tabular}{rrrrrrrrrrr}
            \\toprule
            \\multicolumn{5}{c}{Parameters of $\\M$} & \\multicolumn{2}{c}{Size  (kB)} & \\multicolumn{4}{c}{Time (ms)} 
            \\\\
            \\cmidrule(lr){1-5} \\cmidrule(lr){6-7} \\cmidrule(lr){8-11}
            $d$ & $k$ & $q$ & $t$ & $n$ & $m$ & $\\sigma$ & \\texttt{Sig} & \\texttt{Ver$_1$} & \\texttt{Ver$_0$} &
            $\\Sigma$.\\texttt{Ver} \\\\
            \\midrule
    ''' % TABLE_CAPTION

    footer = '''
        \\bottomrule
      \\end{tabular}
      \\label{%s}
    \\end{table*}
    ''' % LABEL_LATEX_TABLE

    body = ''
    body = data_to_body(top_data, body)
    body += '\t\\midrule\n'
    body = data_to_body(bottom_data, body, True)

    with open(OUTPUT_TABLE, "w") as file:
        file.write(header)
        file.write(body)
        file.write(footer)


if __name__ == "__main__":
    app()
