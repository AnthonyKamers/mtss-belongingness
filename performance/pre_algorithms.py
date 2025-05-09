from timeit import default_timer as timer

from performance_utils import to_ms
from mtsssigner.blocks.CSVParser import DELIMITER
from mtsssigner.cffs.cff_utils import parse_file
from mtsssigner.signature_scheme import ALGORITHM, SigScheme, HASH
from mtsssigner.signer import pre_sign, sign_raw
from mtsssigner.utils.file_and_block_utils import write_signature_to_file
from mtsssigner.verifier import pre_verify, verify_raw

QTD_ITERATION = 100
CONCATENATE_STRINGS = True
OUTPUT_FILE = 'performance/output/pre_sign_verify_efficiency.txt'

PATH_KEY = "keys/"
PUB_KEY = PATH_KEY + "dilithium_2_pub.key"
PRIV_KEY = PATH_KEY + "dilithium_2_priv.key"
SIG = ALGORITHM.DILITHIUM2
HASH_NOW = HASH.BLAKE2B
PATH_MSG = "msg/n"
FORMATS = ["csv_breakline", "csv_comma", "json", "pdf", "png", "txt", "xml"]
NAME_FORMAT = ["CSV-b", "CSV-c", "JSON", "PDF", "PNG", "TXT", "XML"]
EXT_FORMAT = ["csv", "csv", "json", "pdf", "png", "txt", "xml"]
N_SIZE = [100, 1000, 10000]
D_SIZE = [2, 2, 3]
DEFAULT_IMAGE_SIZE = 20


def main():
    data = {}

    # necessary to call before the tests
    parse_file()

    sig_scheme = SigScheme(SIG, HASH_NOW)

    for k_n, n in enumerate(N_SIZE):
        print(f'running size {n}')
        d_now = D_SIZE[k_n]

        for k, format_now in enumerate(FORMATS):
            ext = EXT_FORMAT[k]
            name_format = NAME_FORMAT[k]

            message_path = f"{PATH_MSG}/{format_now}/{n}"
            message_now = f"{message_path}.{ext}"
            signed_path = f"{message_path}_signature.mts"
            changed_path = f"{message_path}_1.{ext}"

            print(f'running {message_now}...')

            for i in range(QTD_ITERATION):
                if ext == "csv":
                    csv_delimiter = DELIMITER.BREAK_LINE if format_now == "csv_breakline" else DELIMITER.COMMA
                else:
                    csv_delimiter = None

                start_pre_sign = timer()
                pre_arguments_sign = pre_sign(sig_scheme, message_now, PRIV_KEY, d_now,
                                              image_block_size=DEFAULT_IMAGE_SIZE, csv_delimiter=csv_delimiter,
                                              concatenate_strings=CONCATENATE_STRINGS)
                end_pre_sign = timer()

                start_sign = timer()
                signature = sign_raw(*pre_arguments_sign)
                end_sign = timer()

                # save only the first in disk
                if i == 0:
                    write_signature_to_file(signature, message_now)

                start_pre_verify = timer()
                pre_arguments_verify = pre_verify(message_now, signed_path, sig_scheme, PUB_KEY,
                                                  image_block_size=DEFAULT_IMAGE_SIZE, csv_delimiter=csv_delimiter,
                                                  concatenate_strings=CONCATENATE_STRINGS)
                end_pre_verify = timer()

                start_verify = timer()
                result, _ = verify_raw(*pre_arguments_verify)
                end_verify = timer()

                if not result:
                    raise Exception("The signature is not valid! - verify")

                start_pre_locate = timer()
                pre_arguments_locate = pre_verify(changed_path, signed_path, sig_scheme, PUB_KEY,
                                                  image_block_size=DEFAULT_IMAGE_SIZE, csv_delimiter=csv_delimiter,
                                                  concatenate_strings=CONCATENATE_STRINGS)
                end_pre_locate = timer()

                start_locate = timer()
                result_locate, locate = verify_raw(*pre_arguments_locate)
                end_locate = timer()

                if not result_locate:
                    raise Exception("The signature is not valid! - locate")

                # put information to data (considering iterations)
                key_data = f"{n}_{name_format}"
                if key_data not in data:
                    data[key_data] = {
                        "n": n,
                        "format": name_format,
                        "pre_sign": to_ms(start_pre_sign, end_pre_sign),
                        "sign": to_ms(start_sign, end_sign),
                        "pre_verify": to_ms(start_pre_verify, end_pre_verify),
                        "verify": to_ms(start_verify, end_verify),
                        "locate": to_ms(start_locate, end_locate)
                    }
                else:
                    info = data[key_data]
                    info["pre_sign"] = (info['pre_sign'] + to_ms(start_pre_sign, end_pre_sign)) / 2
                    info["sign"] = (info['sign'] + to_ms(start_sign, end_sign)) / 2
                    info["pre_verify"] = (info['pre_verify'] + to_ms(start_pre_verify, end_pre_verify)) / 2
                    info["verify"] = (info['verify'] + to_ms(start_verify, end_verify)) / 2
                    info["locate"] = (info['locate'] + to_ms(start_locate, end_locate)) / 2

    # write the data to a file
    generate_output(data)


def generate_output(data: dict[str, dict[str, int]]) -> None:
    string = f'n format pre-sign sign pre-verify verify locate\n'

    for format_now, info in data.items():
        string += f"{info['n']} {info['format']} {info['pre_sign']} {info['sign']} {info['pre_verify']} {info['verify']} {info['locate']}\n"

    with open(OUTPUT_FILE, "w") as file:
        file.write(string)

    print("The output was generated successfully!")


if __name__ == "__main__":
    main()
