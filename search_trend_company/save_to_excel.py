from logger_config import setup_logger
import pandas as pd
logger = setup_logger(__name__)

def save_to_excel(row, parsed_data) -> pd.Series:
    try:
        row['기업명'] = str(parsed_data['company_name'])
        row['기업소개'] = str(parsed_data['company_description'])
        row['홈페이지'] = str(parsed_data['company_url'])
        row['주력제품'] = str(parsed_data['company_best_product'])
        row['주력제품특징'] = str(parsed_data['company_best_product_description'])
        row['제품링크'] = str(parsed_data['company_best_product_url'])
        logger.info(f"트렌드 기업 정보 저장 완료: {row['기업명']}")
        return row
    except Exception as e:
        logger.error(f"트렌드 기업 정보 저장 중 오류 발생: {e}")
        return None
   