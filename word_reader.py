from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_block_items(parent):
    """
    Generate a reference to each paragraph and table child within *parent*,
    in document order. Each returned value is an instance of either Table or
    Paragraph.
    """
    for child in parent.element.body:
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def read_text_and_tables_from_word(file_path):
    doc = Document(file_path)
    content_texts = []
    merged_cells = set()

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            if block.text.strip():  # 过滤掉空白段落
                content_texts.append(block.text)
        elif isinstance(block, Table):
            for row in block.rows:
                row_text = []
                for cell in row.cells:
                    cell_key = (cell._tc, cell.text)  # 使用单元格的标识符和其文本作为键
                    if cell_key not in merged_cells:
                        merged_cells.add(cell_key)
                        row_text.append(cell.text.strip())
                    else:
                        row_text.append('')  # 避免重复内容
                content_texts.append('\t'.join(row_text))  # 使用Tab分隔各个单元格的内容

    return '\n'.join(content_texts)  # 使用换行符分隔每段和每行表格内容
