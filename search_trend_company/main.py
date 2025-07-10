import pandas as pd
from gemini_api import get_trend_companies_with_gemini
import time

if __name__ == "__main__":
    try:    
        df = pd.read_excel("item_info_trend.xlsx", sheet_name="Sheet1")
        print(df.columns)

        for index, row in df.iterrows():
            if index < 3:
                continue
            
            trend_companies = get_trend_companies_with_gemini(row['code_name'], row['개념설명'])
            print(trend_companies)
            time.sleep(100)
    except Exception as e:
        print(e)