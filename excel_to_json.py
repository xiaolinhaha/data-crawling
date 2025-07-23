import json

import pandas as pd

# 读取 Excel 文件
def read_excel(file_path):
    df = pd.read_excel(file_path)
    # 将 DataFrame 转换为 JSON 字符串
    json_str = df.to_json(orient='records', force_ascii=False)
    return json_str