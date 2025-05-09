import pprint
from timeit import default_timer as timer
from typing import Tuple

# performance_utils must be imported first, so it can set the correct path
from performance_utils import to_ms

from mtsssigner.blocks.CSVParser import DELIMITER, CSVParser
from mtsssigner.blocks.ImageParser import ImageParser
from mtsssigner.blocks.block_utils import get_parser_for_file

QTD_ITERATION = 100
OUTPUT_FILE = 'performance/output/divide_blocks_efficiency.txt'
FOLDER_RELATIVE_ROOT = 'msg/bytes'
order = ['json', 'txt', 'csv', 'xml', 'pdf', 'png']
sizes = [100, 1000, 10000, 100000, 1000000, 10000000]
IMAGE_BLOCK_SIZE = 20
CSV_DELIMITER = DELIMITER.BREAK_LINE


def generate_output(output: dict[str, Tuple[float, int]]) -> None:
    string = f'bytes json json_n txt txt_n csv csv_n xml xml_n pdf pdf_n png png_n\n'

    for size in sizes:
        string += f'{size}'
        for extension in order:
            filename = f'{size}.{extension}'
            time, amount_blocks = output[filename]

            string += f' {time} {amount_blocks}'
        string += '\n'

    with open(OUTPUT_FILE, 'w') as file:
        file.write(string)


def main():
    output = {}
    for iteration in range(QTD_ITERATION):
        for extension in order:
            for size in sizes:
                filename = f'{size}.{extension}'
                filepath = f'{FOLDER_RELATIVE_ROOT}/{extension}/{filename}'

                parser = get_parser_for_file(filepath)

                # additional information to parser's
                if isinstance(parser, ImageParser):
                    parser.set_block_size(IMAGE_BLOCK_SIZE)
                elif isinstance(parser, CSVParser):
                    parser.set_delimiter(CSV_DELIMITER)

                # measure time
                start = timer()
                parser.parse()
                end = timer()

                amount_blocks = parser.get_amount_blocks()

                # put into output
                if iteration == 0:
                    # if it is the first iteration, create a new entry
                    output[filename] = (to_ms(start, end), amount_blocks)
                else:
                    # if it is not the first iteration, take the average between the previous and the current
                    output[filename] = ((output[filename][0] + to_ms(start, end)) / 2, amount_blocks)
        print(f'Iteration {iteration + 1} finished')

    generate_output(output)


if __name__ == "__main__":
    main()
