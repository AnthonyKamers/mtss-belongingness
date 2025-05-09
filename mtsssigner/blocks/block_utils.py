from enum import Enum

from mtsssigner.blocks.CSVParser import CSVParser
from mtsssigner.blocks.ImageParser import ImageParser
from mtsssigner.blocks.JSONParser import JSONParser
from mtsssigner.blocks.PDFParser import PDFParser
from mtsssigner.blocks.Parser import Parser
from mtsssigner.blocks.TXTParser import TXTParser
from mtsssigner.blocks.XMLParser import XMLParser


class EXTENSION(Enum):
    TXT = "txt"
    XML = "xml"
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"

    # images
    PGM_IMAGE = "pgm"
    BITMAP_IMAGE = "bmp"
    PNG_IMAGE = "png"


MAPPING_EXTENSION_PARSER = {
    EXTENSION.TXT: TXTParser,
    EXTENSION.CSV: CSVParser,
    EXTENSION.XML: XMLParser,
    EXTENSION.PDF: PDFParser,
    EXTENSION.JSON: JSONParser,

    # images
    EXTENSION.PGM_IMAGE: ImageParser,
    EXTENSION.BITMAP_IMAGE: ImageParser,
    EXTENSION.PNG_IMAGE: ImageParser
}

DEFAULT_IMAGE_BLOCK_SIZE = 20


def get_extension_file(file_path: str) -> str:
    return file_path.rsplit(".", 1)[1]


def get_parser_for_file(file_path: str) -> Parser:
    extension = get_extension_file(file_path)
    parser = MAPPING_EXTENSION_PARSER[EXTENSION(extension)](file_path)
    return parser
