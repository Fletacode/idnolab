from logger_config import setup_logger
import pandas as pd
logger = setup_logger(__name__)

def save_to_excel(row, parsed_data) -> pd.Series:
    try:
        row['회사명'] = str(parsed_data['domestic_company']['company_name'])
        row['회사소개'] = str(parsed_data['domestic_company']['company_description'])
        row['회사 홈페이지'] = str(parsed_data['domestic_company']['company_url'])
        row['주력제품명'] = str(parsed_data['domestic_company']['company_best_product'])
        row['주력제품 특징'] = str(parsed_data['domestic_company']['company_best_product_description'])
        row['자료 출처'] = str(parsed_data['domestic_company']['company_best_product_url'])

        
        # 글로벌 기업 정보 저장
        row['글로벌_회사명'] = str(parsed_data['global_company']['company_name'])
        row['글로벌_회사소개'] = str(parsed_data['global_company']['company_description']) 
        row['글로벌_회사_홈페이지'] = str(parsed_data['global_company']['company_url'])
        row['글로벌_주력제품명'] = str(parsed_data['global_company']['company_best_product'])
        row['글로벌_주력제품_특징'] = str(parsed_data['global_company']['company_best_product_description'])
        row['글로벌_자료출처'] = str(parsed_data['global_company']['company_best_product_url'])

        logger.debug(f"글로벌 트렌드 기업 정보 저장 완료: {row['글로벌_회사명']}")
        return row
    except Exception as e:
        logger.error(f"트렌드 기업 정보 저장 중 오류 발생: {e}")
        return None
   