from typing import List, Tuple, Union

from xml.etree import ElementTree

from mtsssigner.blocks.Block import Block


# Contains functions for opening message files and writing their signature
# or correction to files, as well as building blocks from their content or
# rebuilding the message from the generated blocks according to file type.

def get_raw_message(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


# Builds a list of blocks and content string from a txt file.
# For txt files, each block is a line of text.
def __get_message_and_blocks_from_txt_file(txt_file_path: str, message: str = None) -> Tuple[str, List[str]]:
    if not message:
        message = get_raw_message(txt_file_path)
    return message, message.split("\n")


# Rebuilds the original txt message from its blocks.
def __rebuild_txt_content_from_blocks(blocks: List[Block]) -> str:
    return "\n".join([str(block) for block in blocks])


# Builds a list of blocks and content string from a xml file. For
# xml files, each block is either a singular tag or pair of tags
# (start/end), while maitaining the inheritance structure of the
# original file. The process of building the blocks strips the file of identation.
def __get_message_and_blocks_from_xml_file(xml_file_path: str, message: str = None) -> Tuple[str, List[str]]:
    if not message:
        message = get_raw_message(xml_file_path)
    message = ElementTree.canonicalize(message)
    message = message.replace("\n", "")
    message = message.replace("\t", "")
    delimiter = "<"
    blocks = [delimiter + block for block in message.split(delimiter)]
    index = 1
    grouped_blocks = [blocks[1]]
    while index < len(blocks[1:]):
        if blocks[index][:2] == "</" and blocks[index + 1][:2] == "</":
            grouped_blocks.append(blocks[index].rstrip())
            grouped_blocks.append(blocks[index + 1].rstrip())
            index += 2
        elif blocks[index + 1][:2] == "</":
            grouped_tag = blocks[index] + blocks[index + 1]
            grouped_blocks.append(grouped_tag.rstrip())
            index += 2
        else:
            grouped_blocks.append(blocks[index].rstrip())
            index += 1
    return message, grouped_blocks


# Rebuilds the original xml message from its blocks.
# Considering the current correction algorithm, will not
# be used in practice since the blocks from an xml file
# usually contain too many characters to correct.
def __rebuild_xml_content_from_blocks(blocks: List[str], ignore_identation=True) -> Union[str, bytes]:
    unindented_xml = "".join(blocks)
    if ignore_identation:
        return unindented_xml
    xml_tree = ElementTree.fromstring(unindented_xml)
    ElementTree.indent(xml_tree, space="\t\t")
    return ElementTree.tostring(xml_tree)


# Rebuilds the original message from its blocks and given file type.
def rebuild_content_from_blocks(blocks: List[str], file_type: str) -> str:
    if file_type == "txt":
        content = __rebuild_txt_content_from_blocks(blocks)
    elif file_type == "xml":
        content = __rebuild_xml_content_from_blocks(blocks)
    else:
        raise ValueError("Unsupported file type (must be txt or xml)")
    return content


# Builds a list of blocks and content string from a file.
# The method of blocking is determined by the file extension.
def get_message_and_blocks_from_file(message_file_path: str, message: str = None) -> Tuple[str, List[str]]:
    file_type = message_file_path[-3:]
    if file_type == "txt":
        message, blocks = __get_message_and_blocks_from_txt_file(message_file_path, message)
    elif file_type == "xml":
        message, blocks = __get_message_and_blocks_from_xml_file(message_file_path, message)
    else:
        raise ValueError("Unsupported file type (must be txt or xml)")
    return message, blocks


# Gets the file path to write the message signature to,
# according to the original path of the message.
def get_signature_file_path(message_file_path: str, is_raw: bool = False) -> str:
    return message_file_path.rsplit(".", 1)[0] + f"_signature.{'mts' if not is_raw else 'raw'}"


# Gets the file path to write the message correction to,
# according to the original path of the message.
def get_correction_file_path(message_file_path: str) -> str:
    file_type = message_file_path[-3:]
    return message_file_path.rsplit(".", 1)[0] + f"_corrected.{file_type}"


# Writes the binary signature to a file, according
# to the original path of the message.
def write_signature_to_file(signature: Union[bytearray, bytes], message_file_path: str, is_raw: bool = False):
    signature_file_path = get_signature_file_path(message_file_path, is_raw)
    with open(signature_file_path, "wb") as signature_file:
        signature_file.write(signature)


# Writes the correction of a modified message to a file,
# according to the original path of the message.
def write_correction_to_file(message_file_path: str, content: str):
    correction_file_path = get_correction_file_path(message_file_path)
    with open(correction_file_path, "w", encoding="utf-8") as correction_file:
        correction_file.write(content)


def write_cff_to_file(t: int, n: int, d: int, cff: List[List[int]]) -> None:
    with open(f"cffs/{d}-CFF({t}, {n}).txt", "w", encoding="utf-8") as file:
        for line in cff:
            file.write(" ".join([str(number) for number in line]) + "\n")


def read_cff_from_file(t: int, n: int, d: int) -> List[List[int]]:
    with open(f"cffs/{d}-CFF({t}, {n}).txt", "r", encoding="utf-8") as file:
        cff_lines = file.readlines()
    cff = []
    for line in cff_lines:
        cff.append([int(number) for number in line.split(" ")])
    return cff
