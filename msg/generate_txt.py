from itertools import count
from typing import Union

import typer

DEFAULT_LINE = "0" * 8 + "\n"

app = typer.Typer()


def write_line(counter, row_width, zero_fill=8):
    return "\n".join([str(next(counter)).zfill(zero_fill) for _ in range(row_width)])


def write_one_line(counter, row_width, zero_fill=8):
    return ",".join([str(next(counter)).zfill(zero_fill) for _ in range(row_width)])


@app.command()
def generate_txt(output_file: str, max_size: int, lines: Union[int, None] = None, row_width: int = 100):
    counter = count()
    counter_lines = 1

    with open(output_file, 'w') as f:
        while f.tell() <= max_size:
            if lines:
                if counter_lines == lines:
                    content = write_one_line(counter, row_width)
                else:
                    content = DEFAULT_LINE
                    counter_lines += 1
            else:
                content = write_line(counter, row_width)

            f.write(content)


@app.command()
def generate_n(output_file: str, n: int):
    with open(output_file, 'w') as f:
        for _ in range(n):
            f.write(DEFAULT_LINE)


# filename size_bytes lines
if __name__ == '__main__':
    app()
