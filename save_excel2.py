import pandas as pd
import json
import re
from logger_config import get_logger

# 로거 설정
logger = get_logger("save_excel2")


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


def save_to_excel_v2(excel_file_path, item_name, data):
    """
    새로운 JSON 양식에 맞춰 엑셀 파일의 특정 행에 산업 데이터를 저장하는 함수
    
    새로운 필드 포함:
    - isEstimated: 추정 여부 (추정 | 실제금액)
    - estimateReason: 추정 근거
    - references: 출처 URL (기존과 동일)
    - market_size: 시장 규모 (기존과 동일)
    
    Args:
        excel_file_path (str): 엑셀 파일 경로
        item_name (str): 물품명
        data (dict): JSON 형태의 파싱된 데이터
    
    Returns:
        bool: 저장 성공 여부
    """
    
    # 엑셀 파일 읽기
    logger.debug(f"엑셀 파일 읽기: {excel_file_path}")
    df = pd.read_excel(excel_file_path)
    row_index = find_item_row(excel_file_path, item_name)

    if row_index is None:
        logger.error(f"'{item_name}' 항목을 찾을 수 없습니다.")
        return False

    logger.info(f"'{item_name}' 데이터를 엑셀 파일 {row_index + 1}행에 저장 시작")
    logger.debug(f"파싱된 데이터: {data}")

    if data is None:
        logger.error("데이터 파싱에 완전히 실패했습니다.")
        return False
    
    try:
        # 필요한 모든 열이 존재하는지 확인하고, 없으면 추가
        required_columns = [
            # 시장 규모
            '국내 산업규모 (2022)', '국내 산업규모 (2023)', '국내 산업규모 (2024)',
            '해외 산업규모 (2022)', '해외 산업규모 (2023)', '해외 산업규모 (2024)',
            # 추정 여부
            '국내 추정여부 (2022)', '국내 추정여부 (2023)', '국내 추정여부 (2024)',
            '해외 추정여부 (2022)', '해외 추정여부 (2023)', '해외 추정여부 (2024)',
            # 추정 근거
            '국내 추정근거 (2022)', '국내 추정근거 (2023)', '국내 추정근거 (2024)',
            '해외 추정근거 (2022)', '해외 추정근거 (2023)', '해외 추정근거 (2024)',
            # 출처
            '출처 (국내 2022)', '출처 (국내 2023)', '출처 (국내 2024)',
            '출처 (해외 2022)', '출처 (해외 2023)', '출처 (해외 2024)'
        ]
        
        # 없는 열들을 찾아서 추가
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.info(f"누락된 열 {len(missing_columns)}개 추가: {missing_columns}")
            for col in missing_columns:
                df[col] = ""  # 빈 열 추가
        
        # 모든 필요한 열을 object(문자열) 타입으로 설정 (pandas 경고 방지)
        for col in required_columns:
            if col in df.columns:
                df[col] = df[col].astype('object')
        
        # 1. 시장 규모 데이터 저장
        if 'market_size' in data:
            # 국내 시장 규모
            if '국내' in data['market_size']:
                domestic_market = data['market_size']['국내']
                for year in ['2022', '2023', '2024']:
                    if year in domestic_market and domestic_market[year]:
                        column_name = f'국내 산업규모 ({year})'
                        # 이제 열이 항상 존재하므로 조건문 제거
                        df.loc[row_index, column_name] = str(domestic_market[year])
                        logger.debug(f"저장됨: {column_name} = {domestic_market[year]}")
            
            # 해외 시장 규모
            if '해외' in data['market_size']:
                overseas_market = data['market_size']['해외']
                for year in ['2022', '2023', '2024']:
                    if year in overseas_market and overseas_market[year]:
                        column_name = f'해외 산업규모 ({year})'
                        df.loc[row_index, column_name] = str(overseas_market[year])
                        logger.debug(f"저장됨: {column_name} = {overseas_market[year]}")
        
        # 2. 추정 여부 데이터 저장
        if 'isEstimated' in data:
            # 국내 추정 여부
            if '국내' in data['isEstimated']:
                domestic_estimated = data['isEstimated']['국내']
                for year in ['2022', '2023', '2024']:
                    if year in domestic_estimated and domestic_estimated[year]:
                        column_name = f'국내 추정여부 ({year})'
                        df.loc[row_index, column_name] = str(domestic_estimated[year])
                        logger.debug(f"저장됨: {column_name} = {domestic_estimated[year]}")
            
            # 해외 추정 여부
            if '해외' in data['isEstimated']:
                overseas_estimated = data['isEstimated']['해외']
                for year in ['2022', '2023', '2024']:
                    if year in overseas_estimated and overseas_estimated[year]:
                        column_name = f'해외 추정여부 ({year})'
                        df.loc[row_index, column_name] = str(overseas_estimated[year])
                        logger.debug(f"저장됨: {column_name} = {overseas_estimated[year]}")
        
        # 3. 추정 근거 데이터 저장
        if 'estimateReason' in data:
            # 국내 추정 근거
            if '국내' in data['estimateReason']:
                domestic_reason = data['estimateReason']['국내']
                for year in ['2022', '2023', '2024']:
                    if year in domestic_reason and domestic_reason[year]:
                        column_name = f'국내 추정근거 ({year})'
                        # 긴 텍스트는 200자로 제한
                        reason_text = str(domestic_reason[year])
                        if len(reason_text) > 200:
                            reason_text = reason_text[:200] + "..."
                        df.loc[row_index, column_name] = reason_text
                        logger.debug(f"저장됨: {column_name} = {reason_text[:50]}...")
            
            # 해외 추정 근거
            if '해외' in data['estimateReason']:
                overseas_reason = data['estimateReason']['해외']
                for year in ['2022', '2023', '2024']:
                    if year in overseas_reason and overseas_reason[year]:
                        column_name = f'해외 추정근거 ({year})'
                        reason_text = str(overseas_reason[year])
                        if len(reason_text) > 200:
                            reason_text = reason_text[:200] + "..."
                        df.loc[row_index, column_name] = reason_text
                        logger.debug(f"저장됨: {column_name} = {reason_text[:50]}...")
        
        # 4. 참고자료(출처) 저장
        if 'references' in data:
            # 국내 참고자료
            if '국내' in data['references']:
                domestic_refs = data['references']['국내']
                for year in ['2022', '2023', '2024']:
                    if year in domestic_refs and domestic_refs[year]:
                        column_name = f'출처 (국내 {year})'
                        # 참조 정보도 200자로 제한
                        ref_text = str(domestic_refs[year])
                        # if len(ref_text) > 200:
                        #     ref_text = ref_text[:200] + "..."
                        df.loc[row_index, column_name] = ref_text
                        logger.debug(f"저장됨: {column_name} = {ref_text[:50]}...")
            
            # 해외 참고자료
            if '해외' in data['references']:
                overseas_refs = data['references']['해외']
                for year in ['2022', '2023', '2024']:
                    if year in overseas_refs and overseas_refs[year]:
                        column_name = f'출처 (해외 {year})'
                        ref_text = str(overseas_refs[year])
                        # if len(ref_text) > 200:
                        #     ref_text = ref_text[:200] + "..."
                        df.loc[row_index, column_name] = ref_text
                        logger.debug(f"저장됨: {column_name} = {ref_text[:50]}...")
        
        # 엑셀 파일 저장
        df.to_excel(excel_file_path, index=False)
        logger.info(f"'{item_name}' 데이터가 {row_index + 1}행에 성공적으로 저장되었습니다.")
        
        # 저장된 데이터 요약 로그
        saved_fields = []
        if 'market_size' in data:
            if data['market_size'].get('국내'):
                saved_fields.append(f"국내 시장규모 {len(data['market_size']['국내'])}개년")
            if data['market_size'].get('해외'):
                saved_fields.append(f"해외 시장규모 {len(data['market_size']['해외'])}개년")
        if 'isEstimated' in data:
            saved_fields.append("추정여부 정보")
        if 'estimateReason' in data:
            saved_fields.append("추정근거 정보")
        if 'references' in data:
            saved_fields.append("참조 정보")
        
        logger.info(f"저장된 필드: {', '.join(saved_fields)}")
        return True
        
    except Exception as e:
        logger.error(f"엑셀 파일 저장 중 오류 발생: {e}")
        return False


def create_sample_data():
    """
    새로운 JSON 양식의 샘플 데이터 생성 (테스트용)
    
    Returns:
        dict: 샘플 데이터
    """
    return {
        "market_size": {
            "국내": {
                "2022": "420000000000",
                "2023": "450000000000", 
                "2024": "469200000000"
            },
            "해외": {
                "2022": "3000000000",
                "2023": "3306000000",
                "2024": "3655248000"
            }
        },
        "isEstimated": {
            "국내": {
                "2022": "추정",
                "2023": "추정",
                "2024": "실제금액"
            },
            "해외": {
                "2022": "추정",
                "2023": "추정", 
                "2024": "추정"
            }
        },
        "estimateReason": {
            "국내": {
                "2022": "머큐리 단말사업부문 매출과 시장 점유율 기반 추정",
                "2023": "전년 대비 성장률 10.6% 적용",
                "2024": ""
            },
            "해외": {
                "2022": "글로벌 네트워크 장비 시장 내 공유기 비중 고려한 추정",
                "2023": "연평균 성장률 12% 적용",
                "2024": "Wi-Fi 7 기술 도입 영향 반영한 추정"
            }
        },
        "references": {
            "국내": {
                "2022": "https://ssl.pstatic.net/imgstock/upload/research/company/1636600850257.pdf",
                "2023": "https://m.ddaily.co.kr/page/view/2024061316375099072",
                "2024": "https://v.daum.net/v/Wun1pAaV8I"
            },
            "해외": {
                "2022": "https://www.grandviewresearch.com/industry-analysis/wireless-router-market",
                "2023": "https://www.grandviewresearch.com/industry-analysis/wireless-router-market",
                "2024": "https://www.grandviewresearch.com/industry-analysis/wireless-router-market"
            }
        }
    }


# 테스트 함수
def test_save_excel_v2():
    """
    save_excel_v2 함수 테스트
    """
    logger.info("save_excel_v2 테스트 시작")
    
    # 샘플 데이터 생성
    sample_data = create_sample_data()
    
    # 테스트 실행
    excel_file = 'item_info3.xlsx'
    item_name = '공유기'
    
    success = save_to_excel_v2(excel_file, item_name, sample_data)
    
    if success:
        logger.info("✅ save_excel_v2 테스트 성공!")
    else:
        logger.error("❌ save_excel_v2 테스트 실패!")
    
    return success


if __name__ == "__main__":
    # 테스트 실행
    test_save_excel_v2()
