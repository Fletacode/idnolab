from pydantic import BaseModel
from dotenv import load_dotenv
from logger_config import setup_logger
import os
import time
import json
from google import genai
from google.genai import types
import random

# .env 파일에서 환경변수 로드
load_dotenv()

# 로거 설정
logger = setup_logger(__name__)

class TrendDomesticCompany(BaseModel):
    company_name: str  # 기업명
    company_url: str  # 기업 URL
    company_description: str  # 기업 설명
    company_best_product: str  # 주력 제품명
    company_best_product_url: str  # 제품 URL
    company_best_product_description: str  # 제품 설명

class TrendGlobalCompany(BaseModel):
    company_name: str  # 기업명
    company_url: str  # 기업 URL
    company_description: str  # 기업 설명
    company_best_product: str  # 주력 제품명
    company_best_product_url: str  # 제품 URL
    company_best_product_description: str  # 제품 설명

class TrendCompanies(BaseModel):
    domestic_companies: TrendDomesticCompany  # 국내 트렌드 기업 목록
    global_companies: TrendGlobalCompany  # 해외 트렌드 기업 목록

# Define the grounding tool
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

url_context_tool = types.Tool(
    url_context = types.UrlContext()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool, url_context_tool],
    response_mime_type="text/plain",
    response_schema=TrendCompanies,
    temperature=0.0,
    system_instruction="당신은 산업 분석 전문가입니다. 최신 데이터와 정확한 정보를 제공해주세요."
)

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

# Gemini 클라이언트 초기화 (v1alpha API 사용으로 프리뷰 모델 접근)
client = genai.Client(
    api_key=GEMINI_API_KEY
)

def get_prompt(item_name, item_description):
    return f"""
        당신은 산업 분석 전문가입니다. 최신 데이터와 정확한 정보를 제공해주세요.

            '{item_name} : {item_description}' 관련 트렌드 기업들의 정보를 제공해주세요.
            각 기업에 대해 다음 정보를 포함해주세요: 
            - company_name: 기업명
            - company_url: 기업 홈페이지 URL
            - company_description: 기업 소개/설명
            - company_best_product: 주력 제품명
            - company_best_product_url: 주력 제품 페이지 URL
            - company_best_product_description: 주력 제품 설명
            

            모든 URL은 실제 접근 가능한 정확한 URL이어야 합니다.
            URL응답코드가 200이 아닌 경우 URL응답코드가 200인 다른 기업을 찾아주세요.
            기업 소개와 제품 설명에 [1] 또는 [2, 5] 이런식으로 참고 자료 번호가 있는 경우 참고 자료 번호를 제거하고 작성해주세요.
            기업 설명과 제품 설명은 30자 내외로 핵심만 요약하여 작성해주세요.
            트렌드 기업 선정 기준은 다음과 같습니다.
            - 정량적 분석
                - 성장 지표 (Growth Metrics): 3개년 연평균 성장률(CAGR) 20% 이상, 인력 증가율 15% 이상.
                - 투자 유치 (Funding): 최근 2년 내 Series A 라운드 이상의 투자 유치 실적 보유.
                - 혁신 지표 (Innovation Metrics): 매출 대비 R&D 투자 비율 10% 이상, 핵심 기술 관련 특허 포트폴리오 보유.
            - 정성적 분석
                - 업계 인지도 (Industry Recognition): CES 등 권위 있는 어워드 수상 경력 보유.
                - 미디어 버즈 (Media Buzz): 주요 언론 및 소셜 미디어 내 긍정적 언급량, Google Trends 상승세.
                - 시장 리더십 (Market Leadership): 해당 산업 내 선도적 위치를 점하고 있거나, 경쟁사의 벤치마킹 대상이 되는 경우를 포함.
                                        
            기업 선정 우선순위는 성장 지표, 투자 유치, 혁신 지표, 업계 인지도, 미디어 버즈, 시장 리더십 순으로 합니다.
            
            응답 형식:
            
            {{ 
                "domestic_company":{{ 
                "company_name": "기업명",
                "company_url": "https://example.com",
                "company_description": "기업 소개 및 설명",
                "company_best_product": "주력 제품명",
                "company_best_product_url": "https://example.com/product",
                "company_best_product_description": "주력 제품 설명"
                }},
                "global_company":{{
                    "company_name": "기업명",
                    "company_url": "https://example.com",
                    "company_description": "기업 소개 및 설명",
                    "company_best_product": "주력 제품명",
                    "company_best_product_url": "https://example.com/product",
                    "company_best_product_description": "주력 제품 설명"
                }}  
            }}
                        
    """

def get_trend_companies_with_gemini(item_name, item_description, max_retries=3):
    """
    Gemini API를 사용하여 특정 물품과 관련된 트렌드 기업 정보를 요청
    """
    logger.debug(f"'{item_name}' 항목에 대한 트렌드 기업 정보 Gemini API 호출 시작")
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"API 호출 시도 {attempt + 1}/{max_retries}")
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents= get_prompt(item_name, item_description),            
                config=config
            )
            
            logger.debug(f"'{item_name}' 트렌드 기업 정보 API 호출 성공")
            logger.debug(f"응답 길이: {len(response.text)} 문자")
            return response.text
                
        except Exception as e:
            logger.error(f"API 호출 오류 발생: {e} {response.text}")
            raise e


def parse_trend_companies_with_gemini(response_text):
    """
    Gemini API 응답을 파싱하여 TrendCompany 객체로 변환하는 함수
    """
    
    logger.debug("Gemini API 트렌드 기업 응답 데이터 파싱 시작")
    logger.debug(f"응답 텍스트 길이: {len(str(response_text))}")
    
    try:
        # JSON 문자열을 파싱
        if isinstance(response_text, str):
            json_text = response_text.strip()
            
            # ```json 코드 블록 제거
            if '```json' in json_text:
                start = json_text.find('```json') + 7
                end = json_text.find('```', start)
                if end != -1:
                    json_text = json_text[start:end].strip()
            elif '```' in json_text:
                # 일반 ``` 코드 블록 제거
                start = json_text.find('```') + 3
                end = json_text.rfind('```')
                if end > start:
                    json_text = json_text[start:end].strip()
            
            # { }로 감싸진 JSON 객체만 추출
            if '{' in json_text and '}' in json_text:
                start = json_text.find('{')
                end = json_text.rfind('}') + 1
                if start != -1 and end > start:
                    json_text = json_text[start:end]
            
            # JSON 파싱
            parsed_data = json.loads(json_text)
            
            # 단일 객체 형태로 반환
            if isinstance(parsed_data, dict):
                logger.debug("트렌드 기업 정보 파싱 완료")
                return parsed_data
            else:
                logger.warning("예상과 다른 데이터 형태")
                return parsed_data
        
        # response_text가 문자열이 아닌 경우
        else:
            return response_text
            
    except Exception as e:
        raise e


if __name__ == "__main__":
    import pandas as pd
    from save_to_excel import save_to_excel

    response_text = get_trend_companies_with_gemini("카메라", "카메라는 사진을 촬영하는 장치입니다.")
    print(response_text)

    parsed_data = parse_trend_companies_with_gemini(response_text)
    df = pd.read_excel("item_info_trend.xlsx", sheet_name="Sheet1")
    df.astype(object)

    for index, row in df.iterrows():
        if index == 1:
            update_row = save_to_excel(row, parsed_data)
            df.loc[index] = update_row
            df.to_excel("item_info_trend.xlsx", sheet_name="Sheet1", index=False)
            logger.info(f"트렌드 기업 정보 저장 완료: {row['code_name']}: {index}")