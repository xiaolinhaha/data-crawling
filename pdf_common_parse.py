import pdfplumber
import logging

logger = logging.getLogger(__name__)
pdf_all_info_result = ''


def extract_information_from_pdf(pdf_path):
    global pdf_all_info_result
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        # 创建一个空的列表用于存储信息
        extracted_data = []

        for page_number in range(total_pages):
            page = pdf.pages[page_number]

            # 提取文本内容
            text = page.extract_text()
            extracted_data.append(text)
    text = '\n'.join(extracted_data)
    logger.info(f'改变前的pdf_wff_result数据[{pdf_all_info_result}]')
    pdf_all_info_result = text
    logger.info(f'改变后的pdf_wff_result数据[{pdf_all_info_result}]')
    return text


if __name__ == '__main__':
    pdf_path = 'file/20220819110548761.pdf'
    text1 = extract_information_from_pdf(pdf_path)
    print(text1)
