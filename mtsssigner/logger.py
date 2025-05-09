from datetime import datetime
from datetime import timedelta
from typing import List, Callable, Union, Tuple

from mtsssigner.blocks.Block import Block
from mtsssigner.blocks.Parser import Parser
from mtsssigner.utils.file_and_block_utils import get_signature_file_path, get_correction_file_path

LOG_FILE_PATH = "./logs.txt"
enabled = False


def log_program_command(command: List[str], sig_scheme) -> None:
    if not enabled:
        return
    command_str = " ".join(command)
    log_content = ("##############################\n"
                   f"Command: {command_str}\n")
    log_content += f"Signature scheme = {sig_scheme.sig_algorithm}, hash function = {sig_scheme.hash_function}\n"
    __write_to_log_file(log_content)


def log_execution_start(operation: str) -> None:
    if not enabled:
        return
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    log_content = (f"Start time = {current_time}\n"
                   f"Operation: {operation}\n")
    __write_to_log_file(log_content)


def log_error(error: Union[str, Callable]) -> None:
    if not enabled:
        return
    if callable(error):
        __write_to_log_file(error)
    else:
        __write_to_log_file(f"Error: {error}\n")


def log_execution_end(elapsed_time: timedelta) -> None:
    if not enabled:
        return
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    __write_to_log_file((f"End time = {current_time}\n"
                         f"Elapsed time: {elapsed_time}\n"))


def log_signature_parameters(signed_file: str, private_key_file: str, n: int,
                             sig_scheme, d: int, t: int, parser: Parser,
                             q: Union[None, int] = None, k: Union[None, int] = None,
                             n_from_file: Union[None, int] = None) -> None:
    if not enabled:
        return
    log_content = f"Signed file = {signed_file}; Private key file = {private_key_file}\n"
    log_content += f"File supported by the parser: {parser.__class__.__name__}\n"
    if sig_scheme.sig_algorithm == "rsa":
        key_length = f"modulus = {sig_scheme.signature_length_bytes * 8}"
    else:
        key_length = "length = 256; signature length = 512"
    log_content += f"Number of blocks = {n}; Private key {key_length}\n"

    log_content += f"Supplied d = {d}"

    if d > 1:
        log_content += f"Resulting CFF = {d}-CFF({t}, {n}), q = {q}, k = {k}\n"
    else:
        log_content += f"Resulting CFF = {d}-CFF({t}, {n})\n"

    if n_from_file:
        log_content += f"Number of blocks read from file = {n_from_file} | Number expected = {n}\n"

    modifiable_blocks_proportion = round(d / n, 4)
    log_content += f"Proportion of modifiable blocks: {modifiable_blocks_proportion}%\n"
    log_content += f"Blocks:\n{[str(block) for block in parser.get_blocks()]}\n"
    __write_to_log_file(log_content)


def log_nonmodified_verification_result(verified_file: str, public_key_file: str,
                                        sig_scheme, result: bool) -> None:
    if not enabled:
        return
    if sig_scheme.sig_algorithm == "rsa":
        key_length = f"modulus = {sig_scheme.signature_length_bytes * 8}"
    else:
        key_length = "length = 256; signature length = 512"
    log_content = f"Key {key_length}\n"
    log_content += f"Verified file = {verified_file}; Public key file = {public_key_file}\n"
    signature_status = "Valid" if result else "Invalid"
    log_content += f"Signature status: {signature_status}\n"
    if result:
        log_content += "The message was not modified\n"
    __write_to_log_file(log_content)


def log_localization_result(verified_file: str, public_key_file: str, n: int, t: int,
                            d: int, q: int, k: int, result: bool, modified_blocks: List[int],
                            modified_blocks_content: List[Block], parser: Parser) -> None:
    if not enabled:
        return
    log_content = f"Verified file = {verified_file}; Public key file = {public_key_file}\n"
    log_content += f"File supported by the parser: {parser.__class__.__name__}\n"
    log_content += f"Number of blocks = {n}, Number of tests = {t}, Max modifications = {d}\n"
    log_content += f"Resulting CFF = {d}-CFF({t}, {n}), q = {q}, k = {k}\n"
    signature_status = "Valid" if result else "Invalid"
    log_content += (f"Signature status: {signature_status}; Modified_blocks = {modified_blocks};"
                    f" Modified_content = {[str(block) for block in parser.get_blocks()]}\n")
    if len(modified_blocks) <= d:
        localization_result = "complete"
    else:
        localization_result = "incorrect (too many modifications)"
    log_content += f"Localization result: {localization_result}\n"
    __write_to_log_file(log_content)


def log_correction_parameters(s: int, process_pool_size: int) -> None:
    if not enabled:
        return
    __write_to_log_file(
        (f"Max ASCII/UTF-8 (1 byte) characters to correct per block = {s}\n"
         f"Available parallel processes to realize the correction: {process_pool_size}\n")
    )


def log_cff_from_file() -> None:
    if not enabled:
        return
    __write_to_log_file("CFF read from file.\n")


def log_correction_progress(b: int) -> None:
    if not enabled:
        return
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    __write_to_log_file(f"Current time = {current_time}, correction operation number = {b}\n")


def log_block_correction(block_number: int, correction: str = "") -> None:
    if not enabled:
        return
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    if block_number > -1:
        __write_to_log_file((f"({current_time}) Block {block_number} was corrected,"
                             f" correction value = '{correction}'\n"))
    else:
        __write_to_log_file(f"{current_time} : No block could be corrected\n")


def log_collision(block_number: int, collision: str) -> None:
    if not enabled:
        return
    __write_to_log_file(
        f"Collision found for block {block_number}, collision value = '{collision}'\n"
    )


def __write_to_log_file(content: Union[str, Callable]) -> None:
    if not enabled:
        return
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        if callable(content):
            content(file=log_file)
        else:
            log_file.write(content)


def print_localization_result(result: Tuple[bool, List[int]]):
    signature_status = "Signature is valid" if result[0] else "Signature could not be verified"

    if result[0]:
        if len(result[1]) == 0:
            localization_status = "message was not modified"
        else:
            localization_status = f"Modified blocks = {result[1]}"
        print(f"Verification result: {signature_status}; {localization_status}")
    else:
        print(f"Verification result: {signature_status}")


def print_operation_result(enabled_now: bool, operation: str, message_file_path: str,
                           localization_result: Tuple[bool, List[int]] = None):
    if not enabled_now:
        return
    if operation == "sign":
        print(f"Signature written to {get_signature_file_path(message_file_path)}")
    elif operation == "verify":
        print_localization_result(localization_result)
    elif operation == "verify-correct":
        print(f"Correction written to {get_correction_file_path(message_file_path)}")
