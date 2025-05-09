from typing import List, Union
from Crypto.Hash import SHA256

import pikepdf

from mtsssigner.blocks.Block import Block
from mtsssigner.blocks.Parser import Parser


class PDFParser(Parser):
    def __init__(self, path: str):
        super().__init__(path)
        self.passed: List[pikepdf.Object] = []
        self.pdf = None
        self.content = None

    def _iterate_element(self, object_pdf: pikepdf.Object, level: int = 1, prev_dict_block: Union[None, Block] = None):
        if object_pdf in self.passed:
            return

        self.passed.append(object_pdf)

        if isinstance(object_pdf, pikepdf.Dictionary):
            for key, _ in object_pdf.items():
                block = Block(name=key, level=level)
                self.blocks.append(block)

                self._iterate_element(object_pdf[key], level + 1, block)
        elif isinstance(object_pdf, pikepdf.Array):
            for item in object_pdf:
                self._iterate_element(item, level + 1, prev_dict_block)
        elif isinstance(object_pdf, pikepdf.Stream):
            # we take the hash of the stream to avoid difficulties with the content
            # for example, if the content is a binary file, it will be difficult to read it
            # as we take the hash of the stream, we can choose a hash function of our choice,
            # in this case, we will use SHA256
            content_stream = SHA256.new(object_pdf.read_raw_bytes()).digest().hex()

            block = Block(name="Stream", content=content_stream, level=level)
            self.blocks.append(block)

            for key, _ in object_pdf.items():
                block = Block(name=key, level=level+1)
                self.blocks.append(block)

                self._iterate_element(object_pdf[key], level + 2, block)
        else:
            # it is a final value of a dictionary, just update the previous block content
            prev_dict_block.content = str(object_pdf)

    def parse(self) -> List[Block]:
        self.blocks = []
        self.passed = []

        if self.pdf is None:
            self.pdf = pikepdf.open(self.path)

        for object_pdf in self.pdf.objects:
            self._iterate_element(object_pdf, 1, None)

        return self.blocks

    def get_block(self, element: any, level: int = 0) -> Block:
        pass

    def get_content(self) -> Union[str, bytes]:
        if not self.content:
            self.content = self.get_bytes_from_path()

        return self.content
