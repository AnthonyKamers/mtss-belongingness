from enum import Enum
from typing import List

from mtsssigner.blocks.Block import Block
from mtsssigner.blocks.TXTParser import TXTParser


class DELIMITER(Enum):
    BREAK_LINE = "\n"
    COMMA = ","
    SEMICOLON = ";"


class CSVParser(TXTParser):
    def __init__(self, path: str):
        super().__init__(path)
        self.delimiter = DELIMITER.BREAK_LINE

    def set_delimiter(self, delimiter: DELIMITER):
        self.delimiter = delimiter

    def parse(self) -> List[Block]:
        if self.delimiter == DELIMITER.BREAK_LINE:
            return super().parse()

        self.blocks = []

        if self.content is None:
            self.content = self.get_text_from_path()

        for line in self.content.split(self.delimiter.value):
            self.blocks.append(self.get_block(line))

        return self.blocks
