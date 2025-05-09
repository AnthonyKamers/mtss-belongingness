import re
import json
from timeit import default_timer as timer

import typer

from performance_utils import to_ms
from belongingness_protocol import client_1, client_2, server, clear_globals
from mtsssigner.blocks.block_utils import get_parser_for_file
from mtsssigner.cffs.cff_utils import parse_file, ignore_columns_cff
from mtsssigner.signature_scheme import ALGORITHM, HASH, SigScheme
from mtsssigner.signer import sign
from mtsssigner.utils.file_and_block_utils import write_signature_to_file, read_cff_from_file
from sig_ver_all import PATH_KEY, PATH_MSG, FILES, D_FILES, T_FILES, N_CFF_FILES

QTD_ITERATION = 100
CONCATENATE_STRINGS = True

TABLE_NAME = "belongingness-performance"
OUTPUT_JSON = f"performance/output/{TABLE_NAME}.json"
OUTPUT_TABLE = f"performance/output/{TABLE_NAME}.tex"
LABEL_TABLE = f"table:{TABLE_NAME}"
TABLE_CAPTION = '''Performance overview for the MTSS belongingness protocol. The network delay and the network bandwidth
are not considered; these results are obtained offline. The CFFs for each file are the same as used in Tables 2 and 3. Text
files were used for simplicity. Signed with $\\Sigma$ as ML-DSA level I, and $\\H$ as BLAKE2b.'''

algorithm = ALGORITHM.DILITHIUM2
hash_func = HASH.BLAKE2B
priv = PATH_KEY + "dilithium_2_priv.key"
pub = PATH_KEY + "dilithium_2_pub.key"

BLOCK_MESSAGE = "00000000"
INDEX_BLOCK = 0

PATH_BLOCKS_DATA = 'blocks_data/'
CHANGED_BLOCK = "11111111"

data = {}

app = typer.Typer()


@app.command()
def run():
    # necessary to call before the tests
    parse_file()

    for k, file in enumerate(FILES):
        print(f'running file {file}')

        path_file = PATH_MSG + file
        d = D_FILES[k]
        t = T_FILES[k]
        n_expected = N_CFF_FILES[k]
        n_from_file = int(file.split(".")[0])

        sig_scheme = SigScheme(algorithm, hash_func)

        # sign
        signature = sign(sig_scheme, path_file, priv, d, save_blocks=True, concatenate_strings=CONCATENATE_STRINGS)
        write_signature_to_file(signature, path_file, False)

        # parser
        parser = get_parser_for_file(path_file)
        hash_message = sig_scheme.get_digest(parser.get_content()).hex()

        # check performance for each file and each modified file
        # |I| = 0
        protocol_performance(hash_message, file, 0)

        # now, we are going to change, in the server side, one block of the file and then, two blocks
        # for that, we need to take the CFFs and the blocks
        cff = read_cff_from_file(t, n_expected, d)

        if n_expected > n_from_file:
            cff = ignore_columns_cff(cff, n_expected - n_from_file)

        # we are going to find the first two rows that the first column is 1
        rows_1 = []
        for row in cff:
            for index_in_row, column in enumerate(row):
                if index_in_row == 0 and column == 1:
                    rows_1.append(row)
                    if len(rows_1) == 2:
                        break

        # in this row, I need to identify the first column that is 1 (except for the first)
        index_element = find_index_element(rows_1[0])

        # now, we are going to replace this element in the server side (blocks_data/)
        modify_server_json(hash_message, index_element)

        # now, we run again the performance protocol (with |I| = 1)
        protocol_performance(hash_message, file, 1)

        # repeat the procedure for |I| = 2
        index_element = find_index_element(rows_1[1])
        modify_server_json(hash_message, index_element)
        protocol_performance(hash_message, file, 2)

    generate_output()
    generate_table_latex()


def find_index_element(row):
    index_element = 0
    for k, element in enumerate(row):
        if k == 0:
            continue

        if element == 1:
            index_element = k

    return index_element


def modify_server_json(hash_message: str, index_element: int):
    filename = f"{PATH_BLOCKS_DATA}{hash_message}.json"

    with open(filename, "r") as f:
        blocks = json.load(f)

    blocks[str(index_element)] = CHANGED_BLOCK

    with open(filename, "w") as f:
        f.write(json.dumps(blocks, indent=4))


@app.command()
def table_from_file(path: str = OUTPUT_JSON):
    read_from_json(path)
    generate_table_latex()


def read_from_json(path: str):
    global data

    with open(path, "r") as f:
        data = json.load(f)


def protocol_performance(hash_message: str, filename: str, i_modified: int):
    global data

    for i in range(QTD_ITERATION):
        time_client_1 = 0
        time_client_2 = 0
        time_server_1 = 0
        m_transmitted = 0
        flag = False

        start_client_1 = timer()
        X = client_1(algorithm, hash_func, pub, hash_message, BLOCK_MESSAGE, INDEX_BLOCK)
        end_client_1 = timer()
        time_client_1 += to_ms(start_client_1, end_client_1)

        while not flag:
            start_server = timer()
            Y = server(X)
            end_server = timer()
            time_server_1 += to_ms(start_server, end_server)

            m_transmitted += len(Y[2])

            start_client_2 = timer()
            flag = client_2(X, Y, CONCATENATE_STRINGS)
            end_client_2 = timer()
            time_client_2 += to_ms(start_client_2, end_client_2)

        # clear belongingness protocol globals at each iteration
        clear_globals()

        filename_extension = filename.split(".")[0]
        n_from_filename = filename_extension.split("_")[0]
        key_data = f'{n_from_filename}_{i_modified}'

        # save into data
        if i == 0:
            data[key_data] = {
                "hash": hash_message,
                "blocks_passed": m_transmitted,
                "client_1": time_client_1,
                "server": time_server_1,
                "client_2": time_client_2
            }
        else:
            data[key_data] = {
                "hash": hash_message,
                "blocks_passed": m_transmitted,
                "client_1": round((data[key_data]["client_1"] + time_client_1) / 2, 2),
                "server": round((data[key_data]["server"] + time_server_1) / 2, 2),
                "client_2": round((data[key_data]["client_2"] + time_client_2) / 2, 2)
            }


def generate_output():
    global data

    with open(OUTPUT_JSON, "w") as f:
        f.write(json.dumps(data, indent=4))


def generate_table_latex():
    global data

    header = '''
    \\begin{table}[ht]
    \\setlength{\\tabcolsep}{10pt}
    \\centering
    \\caption{%s}
    \\begin{tabular}{crcccc}
        \\toprule
        &
        \\multicolumn{1}{c}{\\multirow{2}{*}{$n$}} &
            \\multicolumn{1}{c}{\\multirow{2}{*}{$|M|$ transmitted}} &
            \\multicolumn{3}{c}{Time (ms)} \\\\

        \\cmidrule{4-6}
        & & & Step 1 & Step 2 & Step 3 \\\\
    ''' % TABLE_CAPTION

    footer = '''
    \t\\bottomrule
        \\end{tabular}
        \\label{%s}
    \\end{table}
    ''' % LABEL_TABLE

    body = ''

    keys = data.keys()
    for number_I in range(3):
        body += '\\cmidrule{2 - 6}\n'
        body += '\\multirow{3}{*}{\\rotatebox[origin=c]{90}{$|I| = %d$}}\n' % number_I

        lista_keys = []
        for key in keys:
            if key.endswith(f'_{number_I}'):
                lista_keys.append(key)

        for key in lista_keys:
            filename = key.split("_")[0]

            value = data[key]
            body += (f'\t & {filename} & {value["blocks_passed"]} & {value["client_1"]} & {value["server"]} &'
                     f'{value["client_2"]} \\\\\n')

    with open(OUTPUT_TABLE, "w") as f:
        f.write(header)
        f.write(body)
        f.write(footer)


if __name__ == "__main__":
    app()
