from typing import List, Union

from mtsssigner.blocks.Block import Block
from mtsssigner.blocks.Parser import Parser

import json


class JSONParser(Parser):
    def __init__(self, path: str):
        super().__init__(path)
        self.content = None
        self.data = None

    def _iterate_item(self, key: Union[None, str], value: any, level: int = 1):
        if isinstance(value, dict):
            if key is not None:
                block = Block(name=key, level=level)
                self.blocks.append(block)

            for key_now, value_now in value.items():
                self._iterate_item(key_now, value_now, level + 1)

        elif isinstance(value, list):
            block = Block(name=key, level=level)
            self.blocks.append(block)

            for item in value:
                self._iterate_item(None, item, level + 1)
        elif isinstance(value, str):
            block = Block(name=key, content=value, level=level)
            self.blocks.append(block)

    def parse(self) -> List[Block]:
        self.blocks = []

        if self.content is None:
            self.content = self.get_text_from_path()

        self.data = json.loads(self.content)

        for key, value in self.data.items():
            self._iterate_item(key, value, 1)

        return self.blocks

    def get_block(self, element: any, level: int = 0) -> Block:
        pass

    def get_content(self) -> Union[str, bytes]:
        if self.content is None:
            self.content = self.get_text_from_path()

        return self.content
