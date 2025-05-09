from typing import List, Union

from mtsssigner.blocks.Block import Block
from mtsssigner.blocks.Parser import Parser


class TXTParser(Parser):
    def __init__(self, path: str):
        super().__init__(path)
        self.content = None

    def parse(self) -> List[Block]:
        if self.content is None:
            self.content = self.get_text_from_path()

        self.blocks = []

        for line in self.content.splitlines():
            self.blocks.append(self.get_block(line))

        return self.blocks

    def get_block(self, element: any, level: int = 0) -> Block:
        return Block(content=element)

    def get_content(self) -> Union[str, bytes]:
        if self.content is None:
            self.content = self.get_text_from_path()

        return self.content
