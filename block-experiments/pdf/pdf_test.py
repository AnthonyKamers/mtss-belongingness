import pikepdf

from io import BytesIO, TextIOWrapper, StringIO

import pymupdf
# from pdfminer.high_level import extract_text, extract_pages
# from pdfminer.layout import LTTextContainer

from rlextra.pageCatcher.pdfexplorer import PdfExplorer
from reportlab.pdfgen.canvas import Canvas

import pdfquery

import pdftotext

import pypdf

import xmptools

import pdfplumber

from borb.pdf import PDF, Document

import zlib


def main():
    # # pdfminer
    # for page_layout in extract_pages('test-pdf.pdf'):
    #     for element in page_layout:
    #         if isinstance(element, LTTextContainer):
    #             print(element.get_text())
    #
    # # pikepdf
    # with pikepdf.open('test-pdf.pdf') as pdf:
    #     for page in pdf.pages:
    #         print(page)
    #
    # # reportlab / rlextra
    # # canvas = Canvas("test-pdf.pdf", pageCompression=0)
    # # pdfData = canvas.getpdfdata()
    # explorer = PdfExplorer('test-pdf.pdf')
    # page1text = explorer.getText(0)
    # print(page1text)

    # OBJECT_LIST_INSTANCE = pikepdf._core._ObjectList()
    # OBJECT_INSTANCE = pikepdf._core._Object()

    # passed = []
    #
    # def iterate_keys(object_pdf_now, num_iterate):
    #     if object_pdf_now in passed:
    #         return
    #
    #     passed.append(object_pdf_now)
    #     if isinstance(object_pdf_now, pikepdf.Dictionary):
    #         for key_now in object_pdf_now.keys():
    #             print(f'{num_iterate * "-"} {key_now}')
    #             iterate_keys(object_pdf_now[key_now], num_iterate + 1)
    #
    #     elif isinstance(object_pdf_now, pikepdf.Array):
    #         for item in object_pdf_now:
    #             iterate_keys(item, num_iterate + 1)
    #     elif isinstance(object_pdf_now, pikepdf.Stream):
    #         try:
    #             content_stream = TextIOWrapper(BytesIO(object_pdf_now.read_bytes())).read()
    #         except UnicodeDecodeError:
    #             content_stream = object_pdf_now.read_bytes().decode('utf-8', errors='replace')
    #
    #         print(f'{num_iterate * "-"} {content_stream}')
    #
    #         for key in object_pdf_now.keys():
    #             print(f'{(num_iterate + 1) * "-"} {key}')
    #             iterate_keys(object_pdf_now[key], num_iterate + 2)
    #     else:
    #         print(f'{num_iterate * "-"} {str(object_pdf_now)}')
    #
    # with pikepdf.open('pdf/pdf-sample.pdf') as pdf:
    #     for object_pdf in pdf.objects:
    #         iterate_keys(object_pdf, 1)

    #     tree = pikepdf.NameTree(pdf.Root)
    #     for key in tree.keys():
    #         print(key)

    # for object_pdf in pdf.Root:
    #     teste = pdf.Root[object_pdf]
    #     print(type(teste))

    # pdfquery
    pdf = pdfquery.PDFQuery('test-1.pdf')
    pdf.load()
    pdf.tree.write('test-1.xml', pretty_print=True)

    # pdftotext
    # with open('test-pdf.pdf', 'rb') as f:
    #     pdf = pdftotext.PDF(f)
    #     for page in pdf:
    #         print(page)

    # xmptools
    # xmp = xmptools.XMPMetadata.fromPDF('test-pdf.pdf')
    # print(xmp)

    # pypdf
    # fd = open("test-pdf.pdf", "rb")
    # reader = pypdf.PdfReader(fd)
    # meta = reader.xmp_metadata
    # print(meta)

    # pymupdf
    # document = pymupdf.open('test-pdf.pdf')
    # for page in document:
    #     text = page.get_text().encode('utf-8')
    #     print(text)

    # pdfplumber
    # with pdfplumber.open('test-pdf.pdf') as pdf:
    #     first_page = pdf.pages[0]
    #     text = first_page.extract_text()
    #     print(text)

    # borb
    # with open('test-pdf.pdf', 'rb') as file:
    #     pdf = PDF.loads(file)
    #     print(pdf.get_document_info().get_creator())


if __name__ == '__main__':
    main()
