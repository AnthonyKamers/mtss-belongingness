from timeit import default_timer as timer

import matplotlib.pyplot as plt

from mtsssigner.utils.file_and_block_utils import *

TEXT_PATH = "msg/correct/hash/"
TEXT_EXTENSION = ".txt"

XML_PATH = "msg/xml/"
XML_EXTENSION = ".xml"

files = ["64", "256", "512", "1024", "4096", "8192", "16384", "32768"]


# https://stackoverflow.com/questions/41383787/round-down-to-2-decimal-in-python
def round_down(value, decimals):
    factor = 1 / (10 ** decimals)
    return (value // factor) * factor


def main():
    values_txt = []
    values_xml = []

    for file in files:
        file_path = TEXT_PATH + file + TEXT_EXTENSION

        start_text = timer()
        get_message_and_blocks_from_file(file_path)
        end_text = timer()
        diff_text = round_down((end_text - start_text) * 1000, 4)
        values_txt.append(diff_text)

        xml_path = XML_PATH + file + XML_EXTENSION
        start_xml = timer()
        get_message_and_blocks_from_file(xml_path)
        end_xml = timer()
        diff_xml = round_down((end_xml - start_xml) * 1000, 4)
        values_xml.append(diff_xml)

    generate_values(values_txt, values_xml)
    # generate_graph(values_txt, values_xml)


def generate_values(data_txt, data_xml):
    for file in files:
        print(file, end=" ")
        print(data_txt[files.index(file)], end=" ")
        print(data_xml[files.index(file)], end=" ")
        print()


def generate_graph(data_txt, data_xml):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    ax.plot(files, data_txt, 'g', label="TXT")
    ax.plot(files, data_xml, 'r', label="XML")
    ax.legend()

    ax.set_yscale('log')

    ax.set_ylabel('Time (ms)')
    ax.set_xlabel('Number of blocks n')
    ax.set_title("DivideBlocks algorithm efficiency")

    # plt.show()
    plt.savefig("divide_blocks_efficiency.png", bbox_inches='tight')


if __name__ == '__main__':
    main()
