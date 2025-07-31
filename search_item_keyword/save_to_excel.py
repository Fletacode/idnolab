from logger_config import setup_logger
import pandas as pd
logger = setup_logger(__name__)

def save_to_excel(row, parsed_data) -> pd.Series:
    try:
        row['item_keyword_1'] = str(parsed_data['item_keyword_1']['item_keyword'])
        row['item_description_1'] = str(parsed_data['item_keyword_1']['item_description'])
        row['item_url_1'] = str(parsed_data['item_keyword_1']['item_url'])
        row['item_keyword_2'] = str(parsed_data['item_keyword_2']['item_keyword'])
        row['item_description_2'] = str(parsed_data['item_keyword_2']['item_description'])
        row['item_url_2'] = str(parsed_data['item_keyword_2']['item_url'])
        row['item_keyword_3'] = str(parsed_data['item_keyword_3']['item_keyword'])
        row['item_description_3'] = str(parsed_data['item_keyword_3']['item_description'])
        row['item_url_3'] = str(parsed_data['item_keyword_3']['item_url'])

        logger.debug(f"키워드 정보 저장 완료: {row['item_keyword_1']}")
        return row
    except Exception as e:
        logger.error(f"키워드 정보 저장 중 오류 발생: {e}")
        return None
   