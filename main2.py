import pandas as pd
import time
import os
import json
from save_excel import save_to_excel, find_item_row, parse_industry_data_with_gemini
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
from logger_config import get_logger

# .env 파일에서 환경변수 로드
load_dotenv()

# 로거 설정
logger = get_logger("main")

class MarketSize(BaseModel):
    market_size: list[str]
    references: list[str]

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

# Gemini 클라이언트 초기화 (v1alpha API 사용으로 프리뷰 모델 접근)
client = genai.Client(
    api_key=GEMINI_API_KEY
)



def get_industry_data_with_gemini(item_name, max_retries=3):
    """
    Gemini API를 사용하여 특정 물품의 국내, 해외 산업 규모 데이터를 요청
    """
    
    logger.info(f"'{item_name}' 항목에 대한 Gemini API 호출 시작")
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"API 호출 시도 {attempt + 1}/{max_retries}")
            response = client.models.generate_content(
                model="gemini-2.5-pro-preview-06-05",
                contents= f"""당신은 산업 분석 전문가입니다. 최신 데이터와 정확한 정보를 제공해주세요.

                        '{item_name}' 관련 한국과 해외 년도별 시장규모를 제공해주세요.
                        market_size는 반드시 원화이거나 달러단위의 시장규모 추이 데이터이여야 합니다. 시장규모 추이 데이터가 없다면 비어 있는 문자열로 표시해주세요.
                        백분율은 포함하지 마세요.
                        출하량을 포함하지 마세요.
                        부가 설명 없이 URL만 제공해주세요.
                        
                        {{
                            "market_size": {{
                                "Korea": {{"2022":"8,100,000,000","2023":"110,000,000,000","2024":"120,000,000,000"}},
                                "Overseas": {{"2022":"8,100,000,000","2023":"110,000,000,000","2024":"120,000,000,000"}}
                            }},
                            
                            "references": {{
                                "Korea": {{"2022":"참고자료URL","2023":"참고자료URL","2024":"참고자료URL"}},
                                "Overseas": {{"2022":"참고자료URL","2023":"참고자료URL","2024":"참고자료URL"}}   
                            }}
                        }}

                        가능한 한 구체적인 수치와 신뢰할 수 있는 출처를 제공해주세요.
                        데이터 출처는 년도별로 줄바꿈으로 구분해주세요.
                        한국,해외,2022,2023,2024년 모든 데이터를 찾아야 할 필요는 없습니다.
                                            
                                            """,            
                config={
                    "response_mime_type": "application/json",
                    "response_schema": list[MarketSize]
                }
            )
            
            logger.info(f"'{item_name}' API 호출 성공")
            logger.debug(f"응답 길이: {len(response.text)} 문자")
            return response.text
                
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"API 호출 오류 발생: {e}")
                logger.info(f"재시도 중... (시도 {attempt + 1}/{max_retries})")
                time.sleep(5)
                continue
            else:
                logger.error(f"API 요청 최종 실패: {str(e)}")
                return f"API 요청 오류: {str(e)}"
    
    logger.error("최대 재시도 횟수 초과")
    return "최대 재시도 횟수 초과"

def list_available_models():
    """
    사용 가능한 Gemini 모델 목록을 확인
    """
    logger.info("사용 가능한 Gemini 모델 목록 조회 시작")
    try:
        print("사용 가능한 Gemini 모델 목록:")
        print("=" * 50)
        
        for model in client.models.list():
            print(f"모델명: {model.name}")
            if hasattr(model, 'display_name'):
                print(f"표시명: {model.display_name}")
            if hasattr(model, 'description'):
                print(f"설명: {model.description}")
            print("-" * 30)
            
    except Exception as e:
        logger.error(f"모델 목록 조회 중 오류 발생: {e}")
        print(f"모델 목록 조회 중 오류 발생: {e}")

if __name__ == "__main__":
    excel_file_path = 'item_info2.xlsx'
    logger.info("프로그램 시작")
    # list_available_models()
    # 테스트용 - 하나의 아이템만 실행
    # print("Gemini API 테스트 시작")
    # print("=" * 50)
    # logger.info("Gemini API 테스트 시작")
    
    # test_item = '헤드셋'
    # test_result = get_industry_data_with_gemini(test_item)
    
    # # 테스트 결과를 엑셀 파일에 저장
    # excel_file_path = 'item_info2.xlsx'
    
    # # 테스트 아이템의 행 찾기
    # row_index = find_item_row(excel_file_path, "헤드셋")
    
    # if row_index is not None:
    #     save_to_excel(excel_file_path, row_index, test_item, test_result)
    #     print("엑셀 파일에 저장 완료!")
    #     logger.info("테스트 데이터 엑셀 저장 완료")
    # else:
    #     print("헤드셋 항목을 찾을 수 없어 엑셀 저장을 건너뜁니다.")
    #     logger.warning("테스트 항목을 찾을 수 없어 엑셀 저장 건너뜀")
    
    
    logger.info("전체 엑셀 파일 처리 시작")
    try:
        # 엑셀 파일 읽기
        logger.info(f"엑셀 파일 읽기: {excel_file_path}")
        df = pd.read_excel(excel_file_path)

        # B열 이름 정의
        column_b_name = 'Unnamed: 1' # B열

        # B열 존재 여부 확인
        if column_b_name not in df.columns:
            error_msg = f"'{column_b_name}' 열이 엑셀 파일에 존재하지 않습니다."
            logger.error(error_msg)
            logger.error(f"엑셀 파일의 실제 열 이름: {df.columns.tolist()}")
            print(f"오류: {error_msg}")
            print(f"엑셀 파일의 실제 열 이름: {df.columns.tolist()}")
        else:
            # B열의 3행부터 물품명 읽기 (인덱스 2부터 시작, 파이썬은 0부터 시작)
            items_from_row3 = df[column_b_name][2:]  # 3행부터 끝까지
            
            print("B열의 3행부터 물품명 처리 시작:")
            logger.info("B열의 3행부터 물품명 처리 시작")
            processed_count = 0
            
            for index, item in items_from_row3.items():

                
                result = get_industry_data_with_gemini(item)
                row_index = find_item_row(excel_file_path, item)

                if row_index is not None:
                    save_to_excel(excel_file_path, row_index, item, result)
                    logger.info(f"{item} 엑셀 저장 완료")
                else:
                    logger.info(f"{item} 항목을 찾을 수 없어 엑셀 저장을 건너뜁니다.")
                    
                # API 호출 간격 조절 (요청 제한 방지)
                
                logger.info("API 호출 간격 조절을 위해 3초 대기")
                time.sleep(3)

            final_msg = f"최종 완료! 총 {processed_count}개 처리됨"
            result_msg = f"결과가 '{excel_file_path}' 파일에 저장되었습니다."
            logger.info(final_msg)
            logger.info(result_msg)

    except FileNotFoundError:
        error_msg = f"파일 '{excel_file_path}'을(를) 찾을 수 없습니다."
        print(f"오류: {error_msg}")
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"처리 중 오류 발생: {e}"
        print(f"오류 발생: {e}")
        logger.error(error_msg)

    print("\n처리 완료!")
    logger.info("전체 엑셀 파일 처리 완료")
else:
    print("전체 처리를 건너뜁니다.")
    logger.info("전체 처리를 건너뜀")
