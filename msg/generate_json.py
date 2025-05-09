from itertools import count

import typer

app = typer.Typer()


@app.command()
def generate_json(output_file, max_size):
    counter = count()

    with open(output_file, 'w') as file:
        file.write("{\n")
        while file.tell() <= max_size:
            file.write(f"\t\"{next(counter)}\": \"content\",\n")
        file.write("}")


@app.command()
def generate_n(output_file: str, n: int):
    counter = count()

    with open(output_file, 'w') as file:
        file.write("{\n")
        for i in range(n):
            if i == n - 1:
                file.write(f"\t\"{next(counter)}\": \"content\"\n")
            else:
                file.write(f"\t\"{next(counter)}\": \"content\",\n")
        file.write("}\n")


n_s = [100, 1000, 10000, 100000]

if __name__ == "__main__":
    for n_ in n_s:
        generate_n(f"n/json/{n_}.json", n_)
