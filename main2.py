import pandas as pd
import time
import os
import json
from save_excel import save_to_excel, find_item_row, parse_industry_data_with_gemini
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

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
    
    for attempt in range(max_retries):
        try:
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
            
            return response.text
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(e)
                print(f"오류 발생, 재시도 중... (시도 {attempt + 1}/{max_retries})")
                time.sleep(5)
                continue
            else:
                return f"API 요청 오류: {str(e)}"
    
    return "최대 재시도 횟수 초과"

def list_available_models():
    """
    사용 가능한 Gemini 모델 목록을 확인
    """
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
        print(f"모델 목록 조회 중 오류 발생: {e}")


            
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}")
        print(f"원본 데이터: {response_text[:200]}...")
        print("원본 텍스트를 그대로 반환합니다.")
        return response_text
    except Exception as e:
        print(f"데이터 파싱 중 오류 발생: {e}")
        return response_text

if __name__ == "__main__":


    # list_available_models()
    # 테스트용 - 하나의 아이템만 실행
    print("Gemini API 테스트 시작")
    print("=" * 50)
    
    test_item = '헤드셋'
    test_result = get_industry_data_with_gemini(test_item)
    
    # 테스트 결과를 엑셀 파일에 저장
    excel_file_path = 'item_info2.xlsx'
    
    # 테스트 아이템의 행 찾기
    row_index = find_item_row(excel_file_path, "헤드셋")
    
    if row_index is not None:
        save_to_excel(excel_file_path, row_index, test_item, test_result)
        print("엑셀 파일에 저장 완료!")
    else:
        print("헤드셋 항목을 찾을 수 없어 엑셀 저장을 건너뜁니다.")
    
    # print("=" * 50)
    # print("테스트 완료!")
    
    # 전체 엑셀 파일 처리
    process_excel = input("\n전체 엑셀 파일을 처리하시겠습니까? (y/n): ")
    
    if process_excel.lower() == 'y':
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(excel_file_path)

            # B열 이름 정의
            column_b_name = 'Unnamed: 1' # B열

            # B열 존재 여부 확인
            if column_b_name not in df.columns:
                print(f"오류: '{column_b_name}' 열이 엑셀 파일에 존재하지 않습니다.")
                print(f"엑셀 파일의 실제 열 이름: {df.columns.tolist()}")
            else:
                # B열의 3행부터 물품명 읽기 (인덱스 2부터 시작, 파이썬은 0부터 시작)
                items_from_row3 = df[column_b_name][2:]  # 3행부터 끝까지
                
                print("B열의 3행부터 물품명 처리 시작:")
                processed_count = 0
                
                for index, item in items_from_row3.items():
                    # NaN 값이 아닌 경우에만 처리
                    if index <= 543:
                        continue

                    if pd.notna(item):
                        print(f"\n{'='*50}")
                        print(f"처리 중: 행 {index + 1} - {item}")
                        print(f"{'='*50}")
                        
                        # 이미 데이터가 있는지 확인
                        df_current = pd.read_excel(excel_file_path)  # 최신 상태 읽기
                        if '최신 데이터' in df_current.columns and pd.notna(df_current.loc[index, '최신 데이터']) and df_current.loc[index, '최신 데이터'].strip():
                            print(f"행 {index + 1}에 이미 데이터가 있습니다. 건너뜁니다.")
                            continue
                        
                        # Gemini API를 사용하여 산업 데이터 요청
                        print("국내 산업 규모 데이터 조회 중...")
                        industry_data = get_industry_data_with_gemini(item)
                        
                        # 응답 데이터 파싱
                        parsed_data = parse_industry_data_with_gemini(industry_data)
                        
                        # 함수를 사용하여 엑셀 파일에 저장
                        success = save_to_excel(
                            excel_file_path=excel_file_path,
                            row_index=index,
                            item_name=item,
                            parsed_json_data=parsed_data,
                            perplexity_data=industry_data
                        )
                        
                        if success:
                            processed_count += 1
                            print(f"- 파싱된 데이터: {str(parsed_data)[:100]}...")
                        
                        # 중간 저장 메시지 (실제로는 각 항목마다 저장됨)
                        if processed_count % 5 == 0:
                            print(f"진행 상황: {processed_count}개 처리 완료!")
                        
                        # API 호출 간격 조절 (요청 제한 방지)
                        print("다음 요청까지 3초 대기...")
                        time.sleep(3)

                print(f"\n최종 완료! 총 {processed_count}개 처리됨")
                print(f"결과가 '{excel_file_path}' 파일에 저장되었습니다.")

        except FileNotFoundError:
            print(f"오류: 파일 '{excel_file_path}'을(를) 찾을 수 없습니다.")
        except Exception as e:
            print(f"오류 발생: {e}")

        print("\n처리 완료!")
    else:
        print("전체 처리를 건너뜁니다.")
