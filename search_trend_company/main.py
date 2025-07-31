import pandas as pd
from gemini_api import get_trend_companies_with_gemini, parse_trend_companies_with_gemini
import time
from save_to_excel import save_to_excel
from logger_config import setup_logger

logger = setup_logger(__name__)

not_completed_rows = [  
    50, 84, 122, 125, 126, 134, 139, 144, 151, 154, 158, 174, 182, 184, 187,
    211, 213, 217, 232, 240, 245, 256, 260, 269, 284, 300, 311, 312, 317, 332, 333,
    338, 340, 342, 343, 350, 360, 370, 374, 387, 388, 389, 400, 429, 445, 449, 455,
    456, 504, 512, 514, 515, 523, 551, 558, 562, 565, 594, 603, 620, 640, 641, 644,
    658, 666, 673, 675, 679, 680, 688, 690, 695, 703, 708, 715, 718, 735, 736, 746,
    747, 764, 765, 791, 804, 810, 822, 825, 835, 859, 883, 884, 885, 896, 897, 898,
    899, 906, 911, 916, 918, 920, 922, 923, 926, 932, 937, 952, 954, 955, 959, 966,
    969, 1025, 1027, 1028, 1041, 1042, 1045, 1049, 1052, 1054, 1071, 1074, 1089, 1091,
    1094, 1115, 1120, 1141, 1142, 1143, 1145, 1157, 1167, 1171, 1194, 1215, 1248, 1280
]


if __name__ == "__main__":

    not_completed_rows = [i - 2 for i in not_completed_rows]

    try:    
        df = pd.read_excel("item_info_trend.xlsx", sheet_name="Sheet1")
        df.astype(object)
        for index, row in df.iterrows():
            if index not in not_completed_rows:
                continue
            try:
                logger.info(f"{index}:{row['code_name']}트렌드 기업 정보 조회 시작")
                trend_companies = get_trend_companies_with_gemini(row['code_name'], row['개념설명'])
            
                parsed_data = parse_trend_companies_with_gemini(trend_companies)
                update_row = save_to_excel(row, parsed_data)
                
                df.loc[index] = update_row
                df.to_excel("item_info_trend.xlsx", sheet_name="Sheet1", index=False)
                logger.info(f"트렌드 기업 정보 저장 완료: {row['code_name']}: {index}")
                time.sleep(10)
            except Exception as e:
                logger.error(f"{index}:트렌드 기업 정보 오류 발생: {e}")
                continue
    except Exception as e:
        logger.error(e)
