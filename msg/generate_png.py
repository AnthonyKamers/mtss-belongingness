import typer
from PIL import Image
from math import ceil, sqrt

app = typer.Typer()

BLOCK_SIZE = 20


# $n = \lceil \frac{w}{b} \rceil \times \lceil \frac{h}{b} \rceil$
# b is block_size
@app.command()
def generate_n(output_file: str, n: int):
    size = ceil(sqrt(n * BLOCK_SIZE * BLOCK_SIZE))
    img = Image.new('RGB', (size, size), color='blue')
    img.save(output_file, 'PNG')


if __name__ == "__main__":
    app()
