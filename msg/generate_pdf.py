import os

import fpdf
import typer
from pypdf import PdfWriter

FILE_BASE = "pdf/test.pdf"

app = typer.Typer()


# we create new PDFs by merging the same PDF multiple times
@app.command()
def generate_pdf(output_file: str, max_size: int):
    writer = PdfWriter()
    file_size = 0

    while file_size <= max_size:
        writer.append(FILE_BASE)
        writer.write(output_file)

        file_size = os.path.getsize(output_file)
    writer.close()


@app.command()
def generate_n(output_file: str, n: int):
    print(f"it will not generate {n} blocks")

    pdf = fpdf.FPDF(format='letter')
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for i in range(n):
        pdf.cell(200, 10, txt=f"Hello, World! {i}", ln=True)
    pdf.output(output_file)


if __name__ == "__main__":
    app()
