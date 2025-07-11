import pandas as pd
import time
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
from logger_config import get_logger
from gemini_api import get_industry_data_with_gemini, parse_industry_data_with_gemini
from save_excel_gemini import save_to_excel_gemini
from perpleity_api import PerplexityMarketResearch
# .env 파일에서 환경변수 로드
load_dotenv()

# 로거 설정
logger = get_logger("main")



if __name__ == "__main__":
    excel_file_path = 'item_info_3.xlsx'
    logger.info("프로그램 시작")

    
    
    logger.info("전체 엑셀 파일 처리 시작")
    try:
        # 엑셀 파일 읽기
        logger.info(f"엑셀 파일 읽기: {excel_file_path}")
        df = pd.read_excel(excel_file_path)

    
        processed_count = 0
        numbers = [
        3, 11, 24, 67, 138, 139, 151, 168, 173, 176, 197, 312, 315, 336, 439, 472,
        478, 485, 539, 549, 559, 572, 574, 576, 577, 586, 594, 595, 596, 601, 605,
        610, 618, 619, 626, 629, 643, 645, 663, 668, 679, 686, 695, 696, 699, 703,
        706, 709, 712, 718, 726, 732, 735, 743, 744, 748, 760, 761, 765, 774, 789,
        802, 803, 805, 808, 814, 825, 840, 853, 856, 858, 874, 883, 888, 890, 893,
        900, 906, 911, 916, 920, 921, 926, 931, 938, 939, 944, 949, 955, 957, 958,
        964, 967, 971, 973, 975, 977, 981, 982, 983, 984, 988, 989, 997, 1001, 1012,
        1016, 1017, 1027, 1032, 1036, 1037, 1042, 1045, 1051, 1053, 1055, 1057, 1062,
        1065, 1066, 1068, 1071, 1074, 1075, 1080, 1085, 1089, 1091, 1096, 1115, 1116,
        1117, 1122, 1123, 1124, 1130, 1134, 1139, 1140, 1143, 1146, 1148, 1154, 1155,
        1158, 1165, 1172, 1173, 1176, 1180, 1181, 1187, 1188, 1194, 1196, 1198, 1205,
        1206, 1210, 1211, 1216, 1218, 1228, 1229, 1249, 1255, 1257, 1261, 1262, 1267,
        1278, 1279, 1280, 1281, 1282, 1284
        ]

        numbers = [i - 2 for i in numbers]

        for index, row in df.iterrows():
            if index not in numbers:
                continue
            try:

                item = row['code_name']
                item_description = row['개념설명']
                result = get_industry_data_with_gemini(item, item_description)
                data = parse_industry_data_with_gemini(result)
                save_to_excel_gemini("item_info_3.xlsx", item, data)
                # data = PerplexityMarketResearch().research_parse(item, excel_file_path)
                # save_to_excel_v2(excel_file_path, item, data)
                logger.info(f"{item}, {index} 엑셀 저장 완료")
                
                # API 호출 간격 조절 (요청 제한 방지)
                time.sleep(10)
            except Exception as e:
                logger.error(f"오류 발생: {e}")
                continue

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
