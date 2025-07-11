from pydantic import BaseModel
from dotenv import load_dotenv
from logger_config import get_logger
import os
import time
from google import genai
from google.genai import types
import json
from save_excel_gemini import save_to_excel_gemini
# .env 파일에서 환경변수 로드
load_dotenv()

# 로거 설정
logger = get_logger("gemini_api")

class YearlyData(BaseModel):
    """연도별 데이터 모델"""
    year_2022: str
    year_2023: str
    year_2024: str

class MarketSizeData(BaseModel):
    """시장 규모 데이터 모델"""
    domestic: YearlyData  # 국내
    overseas: YearlyData  # 해외

class EstimatedData(BaseModel):
    """추정 여부 데이터 모델"""
    domestic: YearlyData  # 국내
    overseas: YearlyData  # 해외

class EstimateReasonData(BaseModel):
    """추정 근거 데이터 모델"""
    domestic: YearlyData  # 국내
    overseas: YearlyData  # 해외

class ReferencesData(BaseModel):
    """참조 데이터 모델"""
    domestic: YearlyData  # 국내
    overseas: YearlyData  # 해외

class MarketResearchResponse(BaseModel):
    """시장 조사 응답 전체 모델"""
    market_size: MarketSizeData
    is_estimated: EstimatedData
    estimate_reason: EstimateReasonData
    references: ReferencesData


# Gemini API 설정
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

# Gemini 클라이언트 초기화 (v1alpha API 사용으로 프리뷰 모델 접근)
client = genai.Client(
    api_key=GEMINI_API_KEY
)

# Define the grounding tool
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

url_context_tool = types.Tool(
    url_context = types.UrlContext()
)

# Configure generation settings
config = types.GenerateContentConfig(
    tools=[grounding_tool, url_context_tool],
    response_mime_type="text/plain",
    response_schema=list[MarketResearchResponse]
)



def get_prompt(item_name, item_description):

    prompt = f"""당신은 시장 분석 전문가입니다. '{item_name}: {item_description}' 제품/서비스의 시장 규모에 대한 정확한 데이터를 제공해주세요.

                        다음 정확한 JSON 스키마 형식으로 응답해주세요:
                        {{
                            "market_size": {{
                                "domestic": {{
                                    "year_2022": "구체적인 천원단위 숫자의 금액 또는 천원단위의 숫자의 추정값",
                                    "year_2023": "구체적인 천원단위 숫자의 금액 또는 천원단위의 숫자의 추정값", 
                                    "year_2024": "구체적인 천원단위 숫자의 금액 또는 천원단위의 숫자의 추정값"
                                }},
                                "overseas": {{
                                    "year_2022": "구체적인 천원단위 숫자의 금액 또는 천원단위의 숫자의 추정값",
                                    "year_2023": "구체적인 천원단위 숫자의 금액 또는 천원단위의 숫자의 추정값",
                                    "year_2024": "구체적인 천원단위 숫자의 금액 또는 천원단위의 숫자의 추정값"
                                }}
                            }},
                            "is_estimated": {{
                                "domestic": {{
                                    "year_2022": "True 또는 False",
                                    "year_2023": "True 또는 False",
                                    "year_2024": "True 또는 False"
                                }},
                                "overseas": {{
                                    "year_2022": "True 또는 False",x
                                    "year_2023": "True 또는 False",
                                    "year_2024": "True 또는 False"
                                }}
                            }},
                            "estimate_reason": {{
                                "domestic": {{
                                    "year_2022": "추정 근거",
                                    "year_2023": "추정 근거",
                                    "year_2024": "추정 근거"
                                }},
                                "overseas": {{
                                    "year_2022": "추정 근거",
                                    "year_2023": "추정 근거",
                                    "year_2024": "추정 근거"
                                }}
                            }},
                            "references": {{
                                "domestic": {{
                                    "year_2022": "출처 URL",
                                    "year_2023": "출처 URL",
                                    "year_2024": "출처 URL"
                                }},
                                "overseas": {{
                                    "year_2022": "출처 URL", 
                                    "year_2023": "출처 URL",
                                    "year_2024": "출처 URL"
                                }}
                            }}
                        }}

                    중요한 요구사항:
                    1. 반드시 위의 정확한 JSON 구조를 따라야 합니다 (키 이름 변경 금지)
                    2. 시장 규모는 반드시 구체적인 금액으로 제공 (백분율이나 출하량 제외)
                    3. market_size 필드에는 한국 시장은 원화 단위, 해외 시장은 달러 단위, 단위 표시하지 않고 천원 단위의 숫자로만 표기
                    4. is_estimated 필드에는 오직 추정이면 True 그렇지 않으면 False 형태로 표기
                    5. 직접적인 시장 규모 데이터가 없는 경우:
                    - 관련 산업 데이터, 유사 제품 시장 규모, 시장 점유율, 성장률 등을 수집
                    - 이러한 데이터를 바탕으로 시장 규모를 합리적으로 추정
                    - 추정 근거와 사용된 데이터 출처(URL)을 상세히 기록 [1],[2] 이러한 주석 형태가 아닌 URL 형태로 기록
                    - 절대 citations 필드는 제공하지 않고 출처 URL을 references 필드에 매칭하여 제공, 줄바뀜 없이 제공
                    6. 추정 시 고려사항:
                    - 상위 카테고리 시장 규모에서 해당 제품의 예상 점유율 계산
                    - 유사 제품군의 시장 규모와 비교 분석
                    - 연평균 성장률(CAGR)을 활용한 추정
                    - 인구, 경제 규모, 기술 보급률 등 거시경제 지표 활용
                    7. 신뢰할 수 있는 출처의 URL만 제공
                    8. 출처 URL은 유효한 웹 주소여야함. 404 not Found 오류가 발생하거나 사람이 알아볼 수 없는 URL은 제공하지 않음
                    8. 최신 데이터 우선 제공
                    9. 완전히 데이터를 찾을 수 없는 경우에만 "데이터없음"으로 표시
                    10. JSON 형식 외의 다른 텍스트나 설명은 포함하지 않습니다
                """
    return prompt


def get_industry_data_with_gemini(item_name,item_description, max_retries=3):
    """
    Gemini API를 사용하여 특정 물품의 국내, 해외 산업 규모 데이터를 요청
    """
    
    logger.info(f"'{item_name}' 항목에 대한 Gemini API 호출 시작")
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"API 호출 시도 {attempt + 1}/{max_retries}")
            # logger.info("token count:" + str(client.models.count_tokens(model="gemini-2.5-pro", contents=get_prompt(item_name, item_description))))
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents= get_prompt(item_name, item_description),

                config = config
            )
            
            logger.info(f"'{item_name}' API 호출 성공")
            # logger.info(f"응답: {response}")
            return response.text
                
        except Exception as e:
            logger.error(f"API 요청 최종 실패: {str(e)}")
            return f"API 요청 오류: {str(e)}"

    logger.error("최대 재시도 횟수 초과")
    return "최대 재시도 횟수 초과"


def parse_industry_data_with_gemini(response_text):
    """
    Gemini API 응답을 파싱하여 표준 형태로 변환하는 함수
    """
    
    logger.info("Gemini API 응답 데이터 파싱 시작")
    logger.debug(f"응답 텍스트 길이: {len(str(response_text))}")
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
                        
                        logger.info("새로운 Gemini 응답 형태 파싱 완료")
                        logger.debug(f"국내 시장 규모: {result['market_size']['국내']}")
                        logger.debug(f"해외 시장 규모: {result['market_size']['해외']}")
                        logger.debug(f"국내 참고자료: {result['references']['국내']}")
                        logger.debug(f"해외 참고자료: {result['references']['해외']}")
                        
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
        logger.error(f"데이터 파싱 중 오류 발생: {e}")
        return None


if __name__ == "__main__":
    # 사용 가능한 모든 모델 조회
    # for model in client.models.list():
    #     print(f"모델명: {model.name}")
    #     print(f"설명: {model.display_name}")
    # #     print("---")
    item_name = "게임기"
    item_description = "게임기"
    response_text = get_industry_data_with_gemini(item_name, item_description)

    parsed_data = parse_industry_data_with_gemini(response_text)
    save_to_excel_gemini("item_info_3.xlsx", "게임기", parsed_data)     
    