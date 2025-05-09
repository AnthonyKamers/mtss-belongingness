from xml.etree import ElementTree


def main():
    xml = ElementTree.parse("./test.xml")

    root = xml.getroot()
    print(f'- {root.tag} | {root.attrib} | {root.text}')
    for el in xml.getroot():
        print(f'-- {el.tag} | {el.attrib} | {el.text}')
        for el1 in el:
            print(f'--- {el1.tag} | {el1.attrib} | {el1.text}')


if __name__ == "__main__":
    main()
