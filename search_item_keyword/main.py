import pandas as pd
from gemini_api import get_item_keyword_with_gemini, parse_item_keyword_with_gemini
import time
from save_to_excel import save_to_excel
from logger_config import setup_logger

logger = setup_logger(__name__)


if __name__ == "__main__":

    try:    
        df = pd.read_excel("item_info_keyword.xlsx", sheet_name="Sheet1")
        df.astype(object)
        for index, row in df.iterrows():
            if index == 0:
                continue
            try:
                logger.info(f"{index}:{row['code_name']}트렌드 기업 정보 조회 시작")
                item_keyword = get_item_keyword_with_gemini(row['code_name'], row['개념설명'])
            
                parsed_data = parse_item_keyword_with_gemini(item_keyword)
                update_row = save_to_excel(row, parsed_data)
                
                df.loc[index] = update_row
                df.to_excel("item_info_keyword.xlsx", sheet_name="Sheet1", index=False)
                logger.info(f"트렌드 기업 정보 저장 완료: {row['code_name']}: {index}")
                time.sleep(10)
            except Exception as e:
                logger.error(f"{index}:트렌드 기업 정보 오류 발생: {e}")
                continue
    except Exception as e:
        logger.error(e)
