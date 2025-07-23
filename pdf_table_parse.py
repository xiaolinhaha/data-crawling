import pdfplumber
import re
from operator import itemgetter
from datetime import datetime


# page_chars最尾部的非空字符
def tail_not_space_char(page_chars):
    i = -1
    while page_chars[i].get('text').isspace():
        i = i - 1
        # print(page_chars[i].get('text'), i)
    return page_chars[i]


# 返回列表最头部的非空字符
def head_not_space_char(page_chars):
    i = 0
    while page_chars[i].get('text').isspace():
        i += 1
        # print(page_chars[i].get('text'), i)
    return page_chars[i]


# 将pdf表格数据抽取到文件中
def extract_tables(input_file_path):
    # 读取pdf文件，保存为pdf实例
    pdf = pdfplumber.open(input_file_path)

    # 存储每个页面最底部字符的y0坐标
    y0_bottom_char = []
    # 存储每个页面最底部表格中最底部字符的y0坐标
    y0_bottom_table = []
    # 存储每个页面最顶部字符的y1坐标
    y1_top_char = []
    # 存储每个页面最顶部表格中最顶部字符的y1坐标
    y1_top_table = []
    # 存储所有页面内的表格文本
    text_all_table = []
    # 访问每一页

    for page in pdf.pages:
        # table对象，可以访问其row属性的bbox对象获取坐标
        table_objects = page.find_tables()
        text_table_current_page = page.extract_tables()
        if text_table_current_page:
            text_all_table.append(text_table_current_page)
            # 获取页面最底部非空字符的y0
            y0_bottom_char.append(tail_not_space_char(page.chars).get('y0'))
            # 获取页面最底部表格中最底部字符的y0，table对象的bbox以左上角为原点，而page的char的坐标以左下角为原点，可以用page的高度减去table对象的y来统一
            y0_bottom_table.append(page.bbox[3] - table_objects[-1].bbox[3])
            # 获取页面最顶部字符的y1
            y1_top_char.append(head_not_space_char(page.chars).get('y1'))
            # 获取页面最顶部表格中最底部字符的y1
            y1_top_table.append(page.bbox[3] - table_objects[0].bbox[1])

    # 处理跨页面表格，将跨页面表格合并，i是当前页码，对于连跨数页的表，应跳过中间页面，防止重复处理
    i = 0
    while i < len(text_all_table):
        # print("处理页面{0}/{1}".format(i + 1, len(text_all_table)))
        # 判断当前页面是否以表格结尾且下一页面是否以表格开头，若都是则说明表格跨行，进行表格合并
        # j是要处理的页码，一般情况是当前页的下一页，对于连跨数页情况，也可以是下下一页,跨页数为k
        # 若当前页是最后一页就不用进行处理
        if i + 1 >= len(text_all_table):
            break
        j = i + 1
        k = 1
        # 要处理的页为空时退出
        while text_all_table[j]:
            if y0_bottom_table[i] <= y0_bottom_char[i] and y1_top_table[j] >= y1_top_table[j]:
                # 当前页面最后一个表与待处理页面第一个表合并
                text_all_table[i][-1] = text_all_table[i][-1] + text_all_table[j][0]
                text_all_table[j].pop(0)
                # 如果待处理页面只有一个表，就要考虑下下一页的表是否也与之相连
                if not text_all_table[j] and j + 1 < len(text_all_table) and text_all_table[j + 1]:
                    k += 1
                    j += 1
                else:
                    i += k
                    break
            else:
                i += k
                break

    parse_result = []
    for page_num, page in enumerate(text_all_table):
        for table_num, table in enumerate(page):
            if table:
                parse_result.extend(print_table(table))
    text = '\n'.join(parse_result)
    return text


def merge_same(data):
    records = []
    for month, info in data.items():
        date = datetime.strptime(month, "%Y年%m月")
        type_, amount = info.split(' 逾期金额：')
        type_ = type_.split('逾期类型：')[1]
        records.append((date, type_, amount))

    # Sort the records primarily by date
    records.sort(key=itemgetter(0))

    # Then group the records by continuity and type and amount
    merged_data = []
    group = [records[0]]
    for prev_record, record in zip(records, records[1:]):
        prev_year, prev_month = prev_record[0].year, prev_record[0].month
        curr_year, curr_month = record[0].year, record[0].month
        if not (curr_year - prev_year == 1 and curr_month == 1 and prev_month == 12) and not (
                curr_year == prev_year and curr_month - prev_month == 1) or record[1:] != prev_record[1:]:
            if len(group) > 1:
                merged_data.append(group[0][0].strftime("%Y年%m月") + '至' + group[-1][0].strftime(
                    "%Y年%m月") + ', ' + '逾期类型：{}'.format(group[0][1]) + ', ' + '逾期金额：{}'.format(group[0][2]))
            elif len(group) == 1:
                merged_data.append(group[0][0].strftime("%Y年%m月") + ', ' +
                                   '逾期类型：{}'.format(group[0][1]) + ', ' + '逾期金额：{}'.format(group[0][2]))
            group = [record]
        else:
            group.append(record)

    if group:  # handle the last group
        if len(group) > 1:
            merged_data.append(group[0][0].strftime("%Y年%m月") + '至' + group[-1][0].strftime(
                "%Y年%m月") + ', ' + '逾期类型：{}'.format(group[0][1]) + ', ' + '逾期金额：{}'.format(group[0][2]))
        elif len(group) == 1:
            merged_data.append(group[0][0].strftime("%Y年%m月") + ', ' +
                               '逾期类型：{}'.format(group[0][1]) + ', ' + '逾期金额：{}'.format(group[0][2]))
    return merged_data


def process_repay_record(data):
    # Extract months
    try:
        months = data[1][1:]
        # Rearrange data in pairs of years, month type and overdue amount
        data_pairs = [(data[i], data[i + 1]) for i in range(2, len(data), 2)]
        results = {}
        for pair in data_pairs:
            year = pair[0][0]
            for month, month_type, overdue_amount in zip(months, pair[0][1:], pair[1][1:]):
                if month_type is not None and month_type != '' and overdue_amount is not None:
                    results[f"{year}年{month}月"] = f"逾期类型：{month_type} 逾期金额：{overdue_amount.replace(',', '')}"
        merge_result = merge_same(results)
        return True, merge_result
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Original data:")
        for row in data:
            print(row)
        return False


def print_table(table):
    i = 0
    all_result = []
    while i < len(table):
        record_flag = next((item for item in table[i] if '年' in str(item) and '还款记录' in str(item)), None)
        if record_flag:
            if re.match(r"\d{4}年\d{2}月—\d{4}年\d{2}月的还款记录", record_flag):
                all_result.append(' '.join([item for item in table[i] if item]))  # 打印xxxx年xx月—xxxx年xx月的还款记录
                start_date, end_date = record_flag.split('—')
                end_date = end_date.replace('的还款记录', '')
                start_year = int(start_date[:4])
                end_year = int(end_date[:4])
                res, merge_result = process_repay_record(table[i:i + (end_year - start_year + 1) * 2 + 2])
                if res:
                    i += (end_year - start_year + 1) * 2 + 2  # 跳过处理过的行
                    all_result.extend(merge_result)
                    continue
        all_result.append(' '.join([item.replace('\n', ' ') for item in table[i] if item]))  # 打印未处理的行
        i += 1
    return all_result


if __name__ == '__main__':
    # 抽取表格
    input_file = "/Users/zhangrongqiang/PycharmProjects/ai/api/附件4-2-3-2个人信用报告（授信机构版）_刘锦言.pdf"
    output_excel_path = "/Users/zhangrongqiang/PycharmProjects/ai/api/pdf_ex_result/"

    # text = extract_tables(input_file)
    # print(text)
