import pandas as pd
import json
import re
from logger_config import get_logger

# 로거 설정
logger = get_logger("save_excel")



def find_item_row(excel_file_path, item_name, column_name='Unnamed: 1'):
    """
    엑셀 파일의 B열에서 특정 물품명의 행 인덱스를 찾는 함수
    
    Args:
        excel_file_path (str): 엑셀 파일 경로
        item_name (str): 찾을 물품명
        column_name (str): 검색할 열 이름 (기본값: 'Unnamed: 1' - B열)
    
    Returns:
        int or None: 찾은 행의 인덱스 (0부터 시작), 없으면 None
    """
    logger.info(f"엑셀 파일에서 '{item_name}' 항목 검색 시작: {excel_file_path}")
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
            found_index = item_rows.index[0]  # 첫 번째 매칭 행의 인덱스 반환
            logger.info(f"'{item_name}' 항목을 B열의 {found_index + 1}행에서 찾았습니다.")
            return found_index
        else:
            logger.warning(f"'{item_name}' 항목을 B열에서 찾을 수 없습니다.")
            return None
            
    except Exception as e:
        logger.error(f"B열에서 항목 찾기 중 오류 발생: {e}")
        return None


def save_to_excel(excel_file_path, item_name, data):
    """
    엑셀 파일의 특정 행에 산업 데이터를 저장하는 함수
    
    Args:
        excel_file_path (str): 엑셀 파일 경로
        row_index (int): 저장할 행 인덱스 (0부터 시작)
        item_name (str): 물품명
        parsed_json_data (str): JSON 형태의 파싱된 데이터
    
    Returns:
        bool: 저장 성공 여부
    """
    
    
    
    # 엑셀 파일 읽기
    logger.debug(f"엑셀 파일 읽기: {excel_file_path}")
    df = pd.read_excel(excel_file_path)
    row_index = find_item_row(excel_file_path, item_name)

    logger.info(f"'{item_name}' 데이터를 엑셀 파일 {row_index + 1}행에 저장 시작")
    
    logger.debug(f"파싱된 데이터: {data}")

    if data is None:
        logger.error("데이터 파싱에 완전히 실패했습니다.")
        return False
    
    # 열 이름 정의
    columns = {
        '국내 산업규모 (2022)': '국내 산업규모 (2022)',
        '출처 (국내 2022)': '출처 (국내 2022)',
        '국내 산업규모 (2023)': '국내 산업규모 (2023)', 
        '출처 (국내 2023)': '출처 (국내 2023)',
        '국내 산업규모 (2024)': '국내 산업규모 (2024)',
        '출처 (국내 2024)': '출처 (국내 2024)',
        '해외 산업규모 (2022)': '해외 산업규모 (2022)',
        '출처 (해외 2022)': '출처 (해외 2022)',
        '해외 산업규모 (2023)': '해외 산업규모 (2023)',
        '출처 (해외 2023)': '출처 (해외 2023)',
        '해외 산업규모 (2024)': '해외 산업규모 (2024)',
        '출처 (해외 2024)': '출처 (해외 2024)',
    }
    
    try:
        # 데이터 매핑 및 저장
        # 국내 데이터 저장
        if 'market_size' in data and '국내' in data['market_size']:
            domestic_market = data['market_size']['국내']
            for year in ['2022', '2023', '2024']:
                if year in domestic_market and domestic_market[year]:
                    column_name = f'국내 산업규모 ({year})'
                    if column_name in df.columns:
                        df.loc[row_index, column_name] = domestic_market[year]
        
        # 국내 참고자료 저장
        if 'references' in data and '국내' in data['references']:
            domestic_refs = data['references']['국내']
            for year in ['2022', '2023', '2024']:
                if year in domestic_refs and domestic_refs[year]:
                    column_name = f'출처 (국내 {year})'
                    if column_name in df.columns:
                        df.loc[row_index, column_name] = domestic_refs[year]
        
        # 해외 데이터 저장
        if 'market_size' in data and '해외' in data['market_size']:
            overseas_market = data['market_size']['해외']
            for year in ['2022', '2023', '2024']:
                if year in overseas_market and overseas_market[year]:
                    column_name = f'해외 산업규모 ({year})'
                    if column_name in df.columns:
                        df.loc[row_index, column_name] = overseas_market[year]
        
        # 해외 참고자료 저장
        if 'references' in data and '해외' in data['references']:
            overseas_refs = data['references']['해외']
            for year in ['2022', '2023', '2024']:
                if year in overseas_refs and overseas_refs[year]:
                    column_name = f'출처 (해외 {year})'
                    if column_name in df.columns:
                        df.loc[row_index, column_name] = overseas_refs[year]
        
        # 엑셀 파일 저장
        df.to_excel(excel_file_path, index=False)
        logger.info(f"'{item_name}' 데이터가 {row_index + 1}행에 성공적으로 저장되었습니다.")
        return True
        
    except Exception as e:
        logger.error(f"엑셀 파일 저장 중 오류 발생: {e}")
        return False


    
    