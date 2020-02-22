from app.main.util.envNames import ALLOWED_EXTENSIONS
from datetime import datetime

from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table, _Row
from docx.text.paragraph import Paragraph

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine

from typing import Text


def allowedFile(filename: str) -> bool:
    return giveTypeOfFile(filename) in ALLOWED_EXTENSIONS


def giveTypeOfFile(filename: str) -> str:
    return '.' in filename and filename.rsplit('.', 1)[1].lower()


def giveFileNameUnique(filename: str, fileType: str) -> str:
    # filename = filename + str(datetime.now().timestamp())
    # sha = hashlib.sha256(filename.encode())
    # return sha.hexdigest() + "." + fileType
    return str(datetime.now().timestamp()).replace(".", "") + "." + fileType


def encode(text: str):
    return "*" * len(text)


def markInHtml(text: str):
    return '<mark style="background: #7aecec;">' + text + '</mark>'


def itemIterator(parent):
    """
    Generate a reference to each paragraph and table child within *parent*,
    in document order. Each returned value is an instance of either Table or
    Paragraph. *parent* would most commonly be a reference to a main
    Document object, but also works for a _Cell object, which itself can
    contain paragraphs and tables.
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    elif isinstance(parent, _Row):
        parent_elm = parent._tr
    else:
        raise ValueError("something's not right")
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def readPdf(path:str) -> Text:
    fp = open(path, 'rb')
    parser = PDFParser(fp)
    fp.close()
    doc = PDFDocument()
    parser.set_document(doc)
    doc.set_parser(parser)
    doc.initialize('')
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    laparams.char_margin = 1.0
    laparams.word_margin = 1.0
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in doc.get_pages():
        interpreter.process_page(page)
        layout = device.get_result()
        for lt_obj in layout:
            if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
                text = lt_obj.get_text()
                if text:
                    yield text