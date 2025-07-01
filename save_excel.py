import pandas as pd
import json
import re


def parse_industry_data_with_gemini(response_text):
    """
    Gemini API 응답을 파싱하여 표준 형태로 변환하는 함수
    """

    # print("response_text: ", response_text)
    try:
        # JSON 문자열을 파싱
        if isinstance(response_text, str):
            # JSON 블록만 추출
            json_text = response_text.strip()
            
            # ```json으로 시작하는 경우 JSON 부분만 추출
            if '```json' in json_text:
                start = json_text.find('```json') + 7
                end = json_text.find('```', start)
                if end != -1:
                    json_text = json_text[start:end].strip()
            elif '```' in json_text and '[' in json_text:
                # ```로 감싸진 JSON 블록 추출
                start = json_text.find('[')
                end = json_text.rfind(']') + 1
                if start != -1 and end > start:
                    json_text = json_text[start:end]
            elif '[' in json_text and ']' in json_text:
                # [ ] 사이의 JSON 부분만 추출
                start = json_text.find('[')
                end = json_text.rfind(']') + 1
                if start != -1 and end > start:
                    json_text = json_text[start:end]
            
            parsed_data = json.loads(json_text)
            
            # 새로운 Gemini 응답 형태 처리 (리스트 안에 객체)
            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                first_item = parsed_data[0]
                
                # market_size와 references가 리스트인 경우 처리
                if 'market_size' in first_item and 'references' in first_item:
                    if isinstance(first_item.get('market_size'), list) and isinstance(first_item.get('references'), list):
                        # 리스트 안의 JSON 문자열을 파싱
                        result = {
                            "market_size": {"국내": {}, "해외": {}},
                            "references": {"국내": {}, "해외": {}}
                        }
                        
                        # market_size 처리
                        if first_item['market_size'] and len(first_item['market_size']) > 0:
                            try:
                                market_data = json.loads(first_item['market_size'][0])
                                if 'Korea' in market_data:
                                    result["market_size"]["국내"] = market_data['Korea']
                                if 'Overseas' in market_data:
                                    result["market_size"]["해외"] = market_data['Overseas']
                            except json.JSONDecodeError as e:
                                print(f"market_size 파싱 오류: {e}")
                        
                        # references 처리
                        if first_item['references'] and len(first_item['references']) > 0:
                            try:
                                ref_data = json.loads(first_item['references'][0])
                                if 'Korea' in ref_data:
                                    result["references"]["국내"] = ref_data['Korea']
                                if 'Overseas' in ref_data:
                                    result["references"]["해외"] = ref_data['Overseas']
                            except json.JSONDecodeError as e:
                                print(f"references 파싱 오류: {e}")
                        
                        # print("파싱된 결과:")
                        # print(f"국내 시장 규모: {result['market_size']['국내']}")
                        # print(f"해외 시장 규모: {result['market_size']['해외']}")
                        # print(f"국내 참고자료: {result['references']['국내']}")
                        # print(f"해외 참고자료: {result['references']['해외']}")
                        
                        return result
                    else:
                        # 기존 형태
                        return first_item
            
            # 직접 딕셔너리 형태인 경우
            elif isinstance(parsed_data, dict):
                return parsed_data
            
            # 다른 형태의 데이터도 반환
            return parsed_data
        
        # response_text가 문자열이 아닌 경우
        else:
            return response_text
    except Exception as e:
        print(f"데이터 파싱 중 오류 발생: {e}")
        return None

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
    try:
        df = pd.read_excel(excel_file_path)
        
        # B열 존재 여부 확인
        if column_name not in df.columns:
            print(f"오류: '{column_name}' 열이 존재하지 않습니다.")
            print(f"사용 가능한 열: {df.columns.tolist()}")
            return None
        
        # B열에서 물품명과 일치하는 행 찾기
        item_rows = df[df[column_name] == item_name]
        if not item_rows.empty:
            found_index = item_rows.index[0]  # 첫 번째 매칭 행의 인덱스 반환
            print(f"'{item_name}' 항목을 B열의 {found_index + 1}행에서 찾았습니다.")
            return found_index
        else:
            print(f"'{item_name}' 항목을 B열에서 찾을 수 없습니다.")
            return None
            
    except Exception as e:
        print(f"B열에서 항목 찾기 중 오류 발생: {e}")
        return None


def save_to_excel(excel_file_path, row_index, item_name, parsed_json_data):
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
    df = pd.read_excel(excel_file_path)

    data = parse_industry_data_with_gemini(parsed_json_data)

    # print("data: ", data)

    if data is None:
        print("데이터 파싱에 완전히 실패했습니다.")
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
        print(f"'{item_name}' 데이터가 {row_index + 1}행에 성공적으로 저장되었습니다.")
        return True
        
    except Exception as e:
        print(f"엑셀 파일 저장 중 오류 발생: {e}")
        return False


    
    

