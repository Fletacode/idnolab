import pandas as pd

if __name__ == "__main__":
    df = pd.read_excel("item_info_trend.xlsx", sheet_name="Sheet1")
    df.astype(object)
    for index, row in df.iterrows():
        if index > 3:
            continue
        print(row['code_name'])
        print(row['개념설명'])
        print(row['기업명'])
        print(row['기업소개'])
        print(row['홈페이지'])
        print(row['주력제품'])
        print(row['주력제품특징'])
        print(row['제품링크'])