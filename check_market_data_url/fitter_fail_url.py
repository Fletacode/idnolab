import json
import pandas as pd

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_index_from_col_name(col_name):
    d = {
        "국내 2022": 6,
        "국내 2023": 10,
        "국내 2024": 14,
        "해외 2022": 18,
        "해외 2023": 22,
        "해외 2024": 26,
    }
    return int(d[col_name])

def load_excel_file(file_path):
    df = pd.read_excel(file_path)
    return df

def get_url_from_excel_file(df, row_idx, col_idx):
    return df.iloc[row_idx, col_idx]

if __name__ == "__main__":
    file_path = 'url_validation_result_20250719_171042.json'
    data = load_json_file(file_path)
    df = load_excel_file('item_info_v0.xlsx')

    data = data['실패한_URL']

    for key, value in data.items():
        for item in value:
            url = item['URL']
            str = item['출처']
            # row_idx 추출
            row_idx = int(str.split('[')[1].split(']')[0])
            # 국내 2022, 해외 2022 등 출처 추출
            col_name = str.split('(')[1].split(')')[0]
            col_idx = get_index_from_col_name(col_name)
            # print(row_idx, col_idx, col_name)
            row = get_url_from_excel_file(df, row_idx, col_idx)
            print(row)
