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
    excel_file_path = 'item_info_3.xlsx'
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
            numbers = [
    10, 23, 66, 137, 138, 150, 167, 172, 175, 196, 311, 314, 335, 438, 471, 477, 484,
    538, 548, 558, 571, 573, 575, 576, 585, 593, 594, 595, 600, 604, 609, 617, 618,
    625, 628, 642, 644, 662, 667, 678, 685, 694, 695, 698, 702, 705, 708, 711, 717,
    725, 731, 734, 742, 743, 747, 759, 760, 764, 773, 788, 801, 802, 804, 807, 813,
    824, 839, 852, 855, 857, 873, 882, 887, 889, 892, 899, 905, 910, 915, 919, 920,
    925, 930, 937, 938, 943, 948, 954, 956, 957, 963, 966, 970, 972, 974, 976, 980,
    981, 982, 983, 987, 988, 996, 1000, 1011, 1015, 1016, 1026, 1031, 1035, 1036,
    1041, 1044, 1050, 1052, 1054, 1056, 1061, 1064, 1065, 1067, 1070, 1073, 1074,
    1079, 1084, 1088, 1090, 1095, 1114, 1115, 1116, 1121, 1122, 1123, 1129, 1133,
    1138, 1139, 1142, 1145, 1147, 1153, 1154, 1157, 1164, 1171, 1172, 1175, 1179,
    1180, 1186, 1187, 1193, 1195, 1197, 1204, 1205, 1209, 1210, 1215, 1217, 1227,
    1228, 1248, 1254, 1256, 1260, 1261, 1266, 1277, 1278, 1279, 1280, 1281, 1283, 1284
]
            for index, item in items_from_row3.items():
<<<<<<< HEAD
                if index <= 917:
=======
                if index not in numbers:
>>>>>>> a3aca8f (feat: 엑셀 파일 이름 변경 및 불필요한 파일 삭제, .gitignore 업데이트, 트렌드 기업 찾는 코드 추가)
                    continue
                # result = get_industry_data_with_gemini(item)
                # data = parse_industry_data_with_gemini(result)
                data = PerplexityMarketResearch().research_parse(item, excel_file_path)
                
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
