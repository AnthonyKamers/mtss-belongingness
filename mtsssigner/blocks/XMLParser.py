from typing import List, Union
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from mtsssigner.blocks.Block import Block
from mtsssigner.blocks.Parser import Parser


class XMLParser(Parser):
    def __init__(self, path: str):
        super().__init__(path)
        self.root: Union[None, Element] = None
        self.content = None

    def _iterate_element(self, element: ElementTree.Element, level: int = 0):
        block = self.get_block(element, level)
        self.blocks.append(block)
        for child in element:
            self._iterate_element(child, level + 1)

    def _parse_file(self):
        self.root = ElementTree.parse(self.path).getroot()

    def parse(self) -> List[Block]:
        if self.root is None:
            self._parse_file()

        self.blocks = []

        self.blocks.append(self.get_block(self.root, 1))
        for element in self.root:
            self._iterate_element(element, 2)

        return self.blocks

    def get_block(self, element: ElementTree.Element, level: int = 0) -> Block:
        return Block(content=element.text, name=element.tag, attributes=element.attrib, level=level)

    def get_content(self) -> Union[str, bytes]:
        if self.root is None:
            self._parse_file()

        if self.root is not None:
            self.content = ElementTree.tostring(self.root)

        if self.content:
            return self.content
