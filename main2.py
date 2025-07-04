import pandas as pd
import time
import os
import json
from save_excel import save_to_excel
from save_excel2 import save_to_excel_v2
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
from logger_config import get_logger
from gemini_api import get_industry_data_with_gemini, parse_industry_data_with_gemini
from perpleity_api import PerplexityMarketResearch
# .env 파일에서 환경변수 로드
load_dotenv()

# 로거 설정
logger = get_logger("main")




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
    excel_file_path = 'item_info3.xlsx'
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
                if index <= 170:
                    continue
                # result = get_industry_data_with_gemini(item)
                # data = parse_industry_data_with_gemini(result)
                data = PerplexityMarketResearch().research_parse(item)
                
                save_to_excel_v2(excel_file_path, item, data)
                logger.info(f"{item} 엑셀 저장 완료")
            
                # API 호출 간격 조절 (요청 제한 방지)
                logger.info("API 호출 간격 조절을 위해 10초 대기")
                time.sleep(10)

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
