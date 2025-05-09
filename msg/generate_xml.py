import typer

app = typer.Typer()


@app.command()
def generate_xml(output_file: str, max_size: int):
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")

        file.write("<root>\n")
        while file.tell() <= max_size:
            file.write("<a>content</a>\n")
        file.write("</root>")


@app.command()
def generate_n(output_file: str, n: int):
    with open(output_file, 'w') as f:
        f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        f.write("<root>\n")
        for i in range(n - 2):
            f.write("<a>content</a>\n")
        f.write("</root>\n")


if __name__ == '__main__':
    app()
