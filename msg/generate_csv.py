"""Use to generate a large CSV file for testing purposes. Will write CSV data to STDOUT
Usage: python make-test-csv.py 512000000   # Make a ~512mb CSV file
Taken from https://gist.github.com/shevron/e466b7f2947aa531a3e26bc970175233
"""
import csv
from enum import Enum
from itertools import count

import typer

DEFAULT_LINE = "0" * 8
app = typer.Typer()


class TypeBlock(Enum):
    BREAK_LINE = "breakline"
    COMMA = "comma"
    SEMICOLON = "semicolon"


def make_csv_row(counter, row_width, zero_fill=8):
    return [str(next(counter)).zfill(zero_fill) for _ in range(row_width)]


@app.command()
def generate_csv(output_file: str, max_size: int, row_width=100):
    file = open(output_file, 'w')
    writer = csv.writer(file)
    c = count()
    while True:
        writer.writerow(make_csv_row(c, row_width))
        if file.tell() >= max_size:
            break


@app.command()
def generate_n(output_file: str, n: int, type_division: TypeBlock):
    if type_division == TypeBlock.BREAK_LINE:
        with open(output_file, 'w') as f:
            for _ in range(n):
                f.write(f"{DEFAULT_LINE}\n")
    elif type_division in (TypeBlock.COMMA, TypeBlock.SEMICOLON):
        divisor = "," if TypeBlock.COMMA else ";"
        with open(output_file, 'w') as f:
            for i in range(n):
                string = f"{DEFAULT_LINE}{divisor}"
                if i == n - 1:
                    f.write(f"{DEFAULT_LINE}")
                else:
                    f.write(string)
                # each 10 lines, break line
                if i % 10 == 0 and i != 0:
                    f.write("\n")


if __name__ == '__main__':
    app()
