import math
from abc import ABC
from typing import Union, List

import matplotlib.pyplot as plt
import numpy

from mtsssigner.blocks.Block import Block
from mtsssigner.blocks.Parser import Parser


# generic abstract class for image files
# this is highly based on the repository
# https://github.com/micoluo/Modification-Digital-Signature-Scheme-Using-Combinatorial-Group-Testing
# we made it generic for other image formats (e.g. pgm, bmp, png)
class ImageParser(Parser, ABC):
    def __init__(self, path: str):
        super().__init__(path)
        self.block_size: Union[None, int] = None
        self.image: Union[None, numpy.ndarray] = None

    def set_block_size(self, block_size: int):
        self.block_size = block_size

    def parse(self) -> List[Block]:
        self.blocks = []

        if self.block_size is None:
            raise Exception("Block size is not set (ImageParser requires it)")

        if self.image is None:
            self.get_content()

        if len(self.image.shape) == 2:
            width, height = self.image.shape
        else:
            width, height, _ = self.image.shape

        # handle case where block_size is larger than image
        # we only create one block covering the entire image
        if self.block_size > width or self.block_size > height:
            self.block_size = max(width, height)

        block_rows = math.floor((width + self.block_size - 1) / self.block_size)
        block_columns = math.floor((height + self.block_size - 1) / self.block_size)

        # iterate over each block
        for i in range(block_rows):
            for j in range(block_columns):
                # calculate indexes for the block
                start_row = i * self.block_size
                end_row = min(start_row + self.block_size, block_rows)
                start_column = j * self.block_size
                end_column = min(start_column + self.block_size, block_columns)

                block_content = b''

                # iterate over elements and store pixels for determined block
                for row in range(start_row, end_row):
                    for column in range(start_column, end_column):
                        block_content += self.image[row][column].tobytes()

                self.blocks.append(Block(name=f"{i}_{j}", content=block_content))

        return self.blocks

    def get_block(self, element: any, level: int = 0) -> Block:
        pass

    def get_content(self) -> Union[str, bytes]:
        if self.image is None:
            self.image = plt.imread(self.path)

        return self.image.tobytes()
