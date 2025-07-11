import pandas as pd
import json
import re
from logger_config import get_logger

# 로거 설정
logger = get_logger("save_excel_gemini")


def find_item_row(excel_file_path, item_name, column_name='code_name') -> pd.Series:
    """
    엑셀 파일의 B열에서 특정 물품명의 행 인덱스를 찾는 함수
    
    Args:
        excel_file_path (str): 엑셀 파일 경로
        item_name (str): 찾을 물품명
        column_name (str): 검색할 열 이름 (기본값: 'Unnamed: 1' - B열)
    
    Returns:
        int or None: 찾은 행의 인덱스 (0부터 시작), 없으면 None
    """
    try:
        df = pd.read_excel(excel_file_path)
        
        # B열 존재 여부 확인
        if column_name not in df.columns:
            logger.error(f"'{column_name}' 열이 존재하지 않습니다.")
            logger.error(f"사용 가능한 열: {df.columns.tolist()}")
            return None
        
        # B열에서 물품명과 일치하는 행 찾기
        item_rows = df[df[column_name] == item_name]
        if not item_rows.empty:
            # print(item_rows.iloc[0])
            return item_rows.iloc[0]
        else:
            logger.error(f"'{item_name}' 항목을 B열에서 찾을 수 없습니다.")
            return None
            
    except Exception as e:
        logger.error(f"B열에서 항목 찾기 중 오류 발생: {e}")
        return None



def save_to_excel_gemini(excel_file_path, item_name, parsed_data) -> pd.Series:
    try:
        row = find_item_row(excel_file_path, item_name)
        row['국내 산업규모 (2022)'] = str(parsed_data['market_size']['domestic']['year_2022'])
        row['국내 산업규모 (2023)'] = str(parsed_data['market_size']['domestic']['year_2023'])
        row['국내 산업규모 (2024)'] = str(parsed_data['market_size']['domestic']['year_2024'])
        row['해외 산업규모 (2022)'] = str(parsed_data['market_size']['overseas']['year_2022'])
        row['해외 산업규모 (2023)'] = str(parsed_data['market_size']['overseas']['year_2023'])
        row['해외 산업규모 (2024)'] = str(parsed_data['market_size']['overseas']['year_2024'])
        row['국내 추정여부 (2022)'] = str(parsed_data['is_estimated']['domestic']['year_2022'])
        row['국내 추정여부 (2023)'] = str(parsed_data['is_estimated']['domestic']['year_2023'])
        row['국내 추정여부 (2024)'] = str(parsed_data['is_estimated']['domestic']['year_2024'])
        row['해외 추정여부 (2022)'] = str(parsed_data['is_estimated']['overseas']['year_2022'])
        row['해외 추정여부 (2023)'] = str(parsed_data['is_estimated']['overseas']['year_2023'])
        row['해외 추정여부 (2024)'] = str(parsed_data['is_estimated']['overseas']['year_2024'])
        row['국내 추정근거 (2022)'] = str(parsed_data['estimate_reason']['domestic']['year_2022'])
        row['국내 추정근거 (2023)'] = str(parsed_data['estimate_reason']['domestic']['year_2023'])
        row['국내 추정근거 (2024)'] = str(parsed_data['estimate_reason']['domestic']['year_2024'])
        row['해외 추정근거 (2022)'] = str(parsed_data['estimate_reason']['overseas']['year_2022'])
        row['해외 추정근거 (2023)'] = str(parsed_data['estimate_reason']['overseas']['year_2023'])
        row['해외 추정근거 (2024)'] = str(parsed_data['estimate_reason']['overseas']['year_2024'])
        row['출처 (국내 2022)'] = str(parsed_data['references']['domestic']['year_2022'])
        row['출처 (국내 2023)'] = str(parsed_data['references']['domestic']['year_2023'])
        row['출처 (국내 2024)'] = str(parsed_data['references']['domestic']['year_2024'])
        row['출처 (해외 2022)'] = str(parsed_data['references']['overseas']['year_2022'])
        row['출처 (해외 2023)'] = str(parsed_data['references']['overseas']['year_2023'])
        row['출처 (해외 2024)'] = str(parsed_data['references']['overseas']['year_2024'])
        df = pd.read_excel(excel_file_path)
        df.loc[row.name] = row
        df.to_excel(excel_file_path, index=False)
        return row
    except Exception as e:
        logger.error(f"산업 데이터 저장 중 오류 발생: {e}")
        return None

