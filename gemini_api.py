from pydantic import BaseModel
from dotenv import load_dotenv
from logger_config import get_logger
import os
import time
from google import genai


# .env 파일에서 환경변수 로드
load_dotenv()

# 로거 설정
logger = get_logger("gemini_api")

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
