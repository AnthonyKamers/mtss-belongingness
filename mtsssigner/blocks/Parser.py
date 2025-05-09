from abc import ABC, abstractmethod
from typing import List, Union

from mtsssigner.blocks.Block import Block


class Parser(ABC):
    def __init__(self, path: str):
        self.path: str = path
        self.blocks: List[Block] = []

    @abstractmethod
    def parse(self) -> List[Block]:
        pass

    @abstractmethod
    def get_block(self, element: any, level: int = 0) -> Block:
        pass

    @abstractmethod
    def get_content(self) -> Union[str, bytes]:
        pass

    def get_blocks(self) -> List[Block]:
        return self.blocks

    def get_amount_blocks(self) -> int:
        return len(self.blocks)

    def get_text_from_path(self) -> str:
        with open(self.path, 'r') as file:
            return file.read()

    def get_bytes_from_path(self) -> bytes:
        with open(self.path, 'rb') as file:
            return file.read()
