import pandas as pd
from gemini_api import get_trend_companies_with_gemini, parse_trend_companies_with_gemini
import time
from save_to_excel import save_to_excel
from logger_config import setup_logger

logger = setup_logger(__name__)

if __name__ == "__main__":
    try:    
        df = pd.read_excel("item_info_trend.xlsx", sheet_name="Sheet1")
        df.astype(object)
        for index, row in df.iterrows():
            if index < 1:
                continue
            
            trend_companies = get_trend_companies_with_gemini(row['code_name'], row['개념설명'])
           
            parsed_data = parse_trend_companies_with_gemini(trend_companies)
            update_row = save_to_excel(row, parsed_data)
            
            df.loc[index] = update_row
            df.to_excel("item_info_trend.xlsx", sheet_name="Sheet1", index=False)
            time.sleep(100)
    except Exception as e:
        print(e)