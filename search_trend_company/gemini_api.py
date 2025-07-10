from pydantic import BaseModel
from dotenv import load_dotenv
from logger_config import setup_logger
import os
import time
import json
from google import genai


# .env 파일에서 환경변수 로드
load_dotenv()

# 로거 설정
logger = setup_logger(__name__)

class TrendCompany(BaseModel):
    company_name: str
    company_url: str
    company_description: str
    company_best_product: str
    company_best_product_url: str
    company_best_product_description: str
    

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

# Gemini 클라이언트 초기화 (v1alpha API 사용으로 프리뷰 모델 접근)
client = genai.Client(
    api_key=GEMINI_API_KEY
)

def get_trend_companies_with_gemini(item_name, item_description, max_retries=3):
    """
    Gemini API를 사용하여 특정 물품과 관련된 트렌드 기업 정보를 요청
    """
    logger.info(f"'{item_name}' 항목에 대한 트렌드 기업 정보 Gemini API 호출 시작")
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"API 호출 시도 {attempt + 1}/{max_retries}")
            response = client.models.generate_content(
                model="gemini-2.5-pro-preview-06-05",
                contents= f"""당신은 산업 분석 전문가입니다. 최신 데이터와 정확한 정보를 제공해주세요.

                        '{item_name} : {item_description}' 관련 트렌드 기업들의 정보를 제공해주세요.
                        각 기업에 대해 다음 정보를 포함해주세요: 
                        - company_name: 기업명
                        - company_url: 기업 홈페이지 URL
                        - company_description: 기업 소개/설명
                        - company_best_product: 주력 제품명
                        - company_best_product_url: 주력 제품 페이지 URL
                        - company_best_product_description: 주력 제품 설명
                        

                        모든 URL은 실제 접근 가능한 정확한 URL이어야 합니다.
                        기업 설명과 제품 설명은 구체적이고 유용한 정보를 포함해주세요.
                        
                        응답 형식:
                        
                        {{
                            "company_name": "기업명",
                            "company_url": "https://example.com",
                            "company_description": "기업 소개 및 설명",
                            "company_best_product": "주력 제품명",
                            "company_best_product_url": "https://example.com/product",
                            "company_best_product_description": "주력 제품 설명"
                        }}
                        
                        """,            
                config={
                    "response_mime_type": "application/json",
                    "response_schema": TrendCompany
                }
            )
            
            logger.info(f"'{item_name}' 트렌드 기업 정보 API 호출 성공")
            logger.debug(f"응답 길이: {len(response.text)} 문자")
            return response.text
                
        except Exception as e:
            if attempt < max_retries - 1:
                logger.error(f"API 호출 오류 발생: {e}")
                logger.info(f"재시도 중... (시도 {attempt + 1}/{max_retries})")
                time.sleep(5)
                continue
            else:
                logger.error(f"API 요청 최종 실패: {str(e)}")
                return f"API 요청 오류: {str(e)}"
    
    logger.error("최대 재시도 횟수 초과")
    return "최대 재시도 횟수 초과"


def parse_trend_companies_with_gemini(response_text):
    """
    Gemini API 응답을 파싱하여 TrendCompany 객체로 변환하는 함수
    """
    
    logger.info("Gemini API 트렌드 기업 응답 데이터 파싱 시작")
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
                logger.info("트렌드 기업 정보 파싱 완료")
                return parsed_data
            else:
                logger.warning("예상과 다른 데이터 형태")
                return parsed_data
        
        # response_text가 문자열이 아닌 경우
        else:
            return response_text
            
    except Exception as e:
        logger.error(f"트렌드 기업 데이터 파싱 중 오류 발생: {e}")
        logger.debug(f"파싱 실패한 텍스트: {response_text[:200]}...")
        return None
