from generate_json import generate_json
from generate_txt import generate_txt
from generate_csv import generate_csv
from generate_xml import generate_xml
from generate_pdf import generate_pdf

FOLDER_SAVE = "bytes"
order = ['json', 'txt', 'csv', 'xml', 'pdf']
generators = [generate_json, generate_txt, generate_csv, generate_xml, generate_pdf]
sizes = [100, 1000, 10000, 100000, 1000000, 10000000]


def main():
    for size in sizes:
        for i, generator in enumerate(generators):
            extension = order[i]
            filename = f'{FOLDER_SAVE}/{extension}/{size}.{extension}'

            generator(filename, size)
            print(f'{order[i]} {size} generated')


if __name__ == "__main__":
    main()
