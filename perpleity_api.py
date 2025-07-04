import requests
import json
import time
import os
from dotenv import load_dotenv
from logger_config import get_logger
from save_excel2 import save_to_excel_v2, find_item_row
from pydantic import BaseModel
from typing import Dict, Optional

# 환경변수 로드
load_dotenv()

# 로거 설정
logger = get_logger("perplexity_api")

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

class PerplexityMarketResearch:
    def __init__(self):
        """
        퍼플렉시티 API를 사용한 시장 규모 조사 클래스
        """
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai/chat/completions"
        
        if not self.api_key:
            logger.error("PERPLEXITY_API_KEY 환경변수가 설정되지 않았습니다.")
            raise ValueError("PERPLEXITY_API_KEY가 필요합니다.")
        
        logger.info("퍼플렉시티 API 클라이언트 초기화 완료")
    
    def _get_market_size_data(self, item_name, max_retries=3):
        """
        퍼플렉시티 API를 사용하여 특정 물품의 시장 규모 데이터를 요청
        
        Args:
            item_name (str): 조사할 물품명
            max_retries (int): 최대 재시도 횟수
            
        Returns:
            dict: 시장 규모 데이터 또는 오류 메시지
        """
        
        logger.info(f"'{item_name}' 항목에 대한 퍼플렉시티 API 호출 시작")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 한국어와 영어로 상세한 프롬프트 작성
        prompt = f"""
        당신은 시장 분석 전문가입니다. '{item_name}' 제품/서비스의 시장 규모에 대한 정확한 데이터를 제공해주세요.

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
        5. 반드시 citations 필드는 제공하지 않고 출처 URL을 references 필드에 매칭하여 제공, 줄바뀜 없이 제공
        6. 직접적인 시장 규모 데이터가 없는 경우:
           - 관련 산업 데이터, 유사 제품 시장 규모, 시장 점유율, 성장률 등을 수집
           - 이러한 데이터를 바탕으로 시장 규모를 합리적으로 추정
           - 추정 근거와 사용된 데이터 출처(URL)을 상세히 기록 [1],[2] 이러한 주석 형태가 아닌 URL 형태로 기록
           - 절대 citations 필드는 제공하지 않고 출처 URL을 references 필드에 매칭하여 제공, 줄바뀜 없이 제공
        7. 추정 시 고려사항:
           - 상위 카테고리 시장 규모에서 해당 제품의 예상 점유율 계산
           - 유사 제품군의 시장 규모와 비교 분석
           - 연평균 성장률(CAGR)을 활용한 추정
           - 인구, 경제 규모, 기술 보급률 등 거시경제 지표 활용
        8. 신뢰할 수 있는 출처의 URL만 제공
        9. 최신 데이터 우선 제공
        10. 완전히 데이터를 찾을 수 없는 경우에만 "데이터없음"으로 표시
        11. JSON 형식 외의 다른 텍스트나 설명은 포함하지 않습니다
        12. citations 필드는 제공하지 않고 출처 URL을 references 필드에 매칭하여 제공, 줄바뀜 없이 제공

        '{item_name}' 시장 규모 데이터를 조사하고, 위의 정확한 JSON 스키마로 응답해주세요.
        """
        
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 정확한 시장 데이터를 제공하는 전문 시장 분석가입니다. 항상 JSON 형식으로 응답하고, 신뢰할 수 있는 출처만 인용합니다. 직접적인 시장 규모 데이터가 없는 경우 관련 산업 데이터, 유사 제품 시장 규모, 시장 점유율 등을 수집하여 합리적으로 추정하고, 추정값은 '숫자' 형태로 표시하며, 추정 근거를 상세히 기록합니다."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "MarketResearchResponse",
                    "schema": MarketResearchResponse.model_json_schema()
                }
            },
            "max_tokens": 4000,
            "return_citations": False,
            "return_images": False,
            "return_related_questions": False,
            "stream": False,
            "web_search_options": {
                "search_context_size": "high"
            }
        }
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"API 호출 시도 {attempt + 1}/{max_retries}")
                
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    logger.info(f"'{item_name}' API 호출 성공")
                    logger.debug(f"응답 길이: {len(content)} 문자")
                    
                    return {
                        'content': content,
                        'citations': result.get('citations', []),
                        'usage': result.get('usage', {}),
                        'success': True
                    }
                else:
                    logger.error("API 응답에 choices가 없습니다.")
                    return {'success': False, 'error': 'Invalid response format'}
                    
            except requests.exceptions.Timeout:
                logger.warning(f"API 호출 타임아웃 (시도 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                else:
                    return {'success': False, 'error': 'Request timeout'}
                    
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                logger.error(f"HTTP 오류 {status_code}: {e}")
                
                if status_code == 429:  # Rate limit
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 5  # Exponential backoff
                        logger.info(f"Rate limit 도달. {wait_time}초 대기 후 재시도...")
                        time.sleep(wait_time)
                        continue
                
                return {'success': False, 'error': f'HTTP {status_code}: {str(e)}'}
                
            except Exception as e:
                logger.error(f"예상치 못한 오류: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"재시도 중... (시도 {attempt + 1}/{max_retries})")
                    time.sleep(5)
                    continue
                else:
                    return {'success': False, 'error': str(e)}
        
        logger.error("최대 재시도 횟수 초과")
        return {'success': False, 'error': '최대 재시도 횟수 초과'}
    
    def _parse_market_data(self, api_response):
        """
        퍼플렉시티 API 응답을 파싱하여 표준 형태로 변환
        
        Args:
            api_response (dict): API 응답 데이터
            
        Returns:
            dict: 파싱된 시장 데이터
        """
        
        if not api_response.get('success', False):
            logger.error(f"API 호출 실패: {api_response.get('error', 'Unknown error')}")
            return None
        
        try:
            content = api_response['content']
            logger.info("퍼플렉시티 API 응답 파싱 시작")
            
            # JSON 파싱 시도
            try:
                parsed_data = json.loads(content)
                logger.info("JSON 파싱 성공")
                
                # 새로운 스키마 형식을 기존 형식으로 변환
                converted_data = self._convert_new_schema_to_old(parsed_data)
                
                # 데이터 검증 및 정리
                validated_data = self._validate_and_clean_data(converted_data)
                
                return validated_data
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}")
                logger.debug(f"파싱 실패한 내용: {content[:500]}...")
                return None
            
        except Exception as e:
            logger.error(f"데이터 파싱 중 오류 발생: {e}")
            return None
    
    def _convert_new_schema_to_old(self, new_data):
        """
        새로운 스키마 형식을 기존 형식으로 변환
        
        Args:
            new_data (dict): 새로운 스키마 형식 데이터
            
        Returns:
            dict: 기존 스키마 형식으로 변환된 데이터
        """
        try:
            old_data = {
                "market_size": {"국내": {}, "해외": {}},
                "isEstimated": {"국내": {}, "해외": {}},
                "estimateReason": {"국내": {}, "해외": {}},
                "references": {"국내": {}, "해외": {}}
            }
            
            # 키 매핑
            region_mapping = {
                "domestic": "국내",
                "overseas": "해외"
            }
            
            year_mapping = {
                "year_2022": "2022",
                "year_2023": "2023", 
                "year_2024": "2024"
            }
            
            field_mapping = {
                "market_size": "market_size",
                "is_estimated": "isEstimated",
                "estimate_reason": "estimateReason",
                "references": "references"
            }
            
            # 데이터 변환
            for new_field, old_field in field_mapping.items():
                if new_field in new_data and isinstance(new_data[new_field], dict):
                    for new_region, old_region in region_mapping.items():
                        if new_region in new_data[new_field] and isinstance(new_data[new_field][new_region], dict):
                            for new_year, old_year in year_mapping.items():
                                if new_year in new_data[new_field][new_region]:
                                    old_data[old_field][old_region][old_year] = new_data[new_field][new_region][new_year]
            
            logger.info("스키마 변환 완료")
            return old_data
            
        except Exception as e:
            logger.error(f"스키마 변환 중 오류 발생: {e}")
            return new_data  # 변환 실패 시 원본 반환
    
    def _validate_and_clean_data(self, data):
        """
        데이터 검증 및 정리
        
        Args:
            data (dict): 변환된 데이터
            
        Returns:
            dict: 검증 및 정리된 데이터
        """
        try:
            # 참조 정보가 없는 경우 해당 연도 데이터 삭제
            years = ["2022", "2023", "2024"]
            regions = ["국내", "해외"]
            
            for region in regions:
                for year in years:
                    # references 체크
                    ref_value = data.get("references", {}).get(region, {}).get(year, "")
                    market_size_value = data.get("market_size", {}).get(region, {}).get(year, "")
                    # 참조 정보가 없거나 "데이터없음", "없음" 등인 경우 해당 연도 모든 데이터 삭제
                    if not ref_value or ref_value in ["데이터없음", "없음", "데이터 없음", "", "괸련 데이터 없음", ""] or not market_size_value or market_size_value in ["데이터없음", "없음", "데이터 없음", "", "괸련 데이터 없음", ""]:
                        logger.warning(f"{region} {year}년 참조 정보 없음, 모든 관련 데이터 삭제")
                        
                        # 모든 필드에서 해당 연도 데이터 삭제
                        for field in ["market_size", "isEstimated", "estimateReason", "references"]:
                            if field in data and region in data[field] and year in data[field][region]:
                                del data[field][region][year]
            
            logger.info("데이터 검증 및 정리 완료")
            return data
            
        except Exception as e:
            logger.error(f"데이터 검증 중 오류 발생: {e}")
            return data  # 검증 실패 시 원본 반환
    
    def research_parse(self, item_name, excel_file_path='item_info3.xlsx'):
        """
        시장 규모 조사 후 엑셀 파일에 저장 (새로운 JSON 양식 지원)
        
        Args:
            item_name (str): 조사할 물품명
            excel_file_path (str): 엑셀 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        
        logger.info(f"'{item_name}' 시장 규모 조사 및 저장 시작")
        cnt = 0
        while cnt < 3:
            # 1. 퍼플렉시티 API로 시장 데이터 조회
            api_response = self._get_market_size_data(item_name)
            
            if not api_response.get('success', False):
                logger.error(f"'{item_name}' API 호출 실패, 재시도 {cnt+1}회")
                cnt += 1
                continue
            print("api_response: ", api_response)
            # 2. 응답 데이터 파싱
            parsed_data = self._parse_market_data(api_response)
            print("--------------------------------")
            print("parsed_data: ", parsed_data)
            
            if parsed_data is None:
                logger.error(f"'{item_name}' 데이터 파싱 실패, 재시도 {cnt+1}회")
                cnt += 1
                continue
            
            # 3. 엑셀 파일에 저장 (새로운 JSON 양식 지원)
            try:
                save_success = save_to_excel_v2(excel_file_path, item_name, parsed_data)
                
                if save_success:
                    logger.info(f"'{item_name}' 데이터가 엑셀 파일에 성공적으로 저장되었습니다.")
                    return True
                else:
                    logger.error(f"'{item_name}' 엑셀 저장 실패, 재시도 {cnt+1}회")
                    cnt += 1
                    continue
                    
            except Exception as e:
                logger.error(f"엑셀 저장 중 오류 발생: {e}, 재시도 {cnt+1}회")
                cnt += 1
                continue
        
        # 3회 재시도 후에도 실패한 경우
        logger.error(f"'{item_name}' 시장 규모 조사 및 저장이 3회 시도 후에도 실패했습니다.")
        return False



if __name__ == "__main__":
    data = {
    'content': '{ "market_size": { "domestic": { "year_2022": "없음", "year_2023": "없음", "year_2024": "ioT 관련 데이터가 아닌 Wi-Fi 라우터 시장 기준으로 4692억 원(약 3억 5천만 달러)" }, "overseas": { "year_2022": "없음", "year_2023": "없음", "year_2024": "없음" } }, "is_estimated": { "domestic": { "year_2022": "없음", "year_2023": "없음", "year_2024": "실제금액" }, "overseas": { "year_2022": "없음", "year_2023": "없음", "year_2024": "없음" } }, "estimate_reason": { "domestic": { "year_2022": "데이터 없음", "year_2023": "데이터 없음", "year_2024": "실제 데이터" }, "overseas": { "year_2022": "데이터 없음", "year_2023": "데이터 없음", "year_2024": "데이터 없음" } }, "references": { "domestic": { "year_2022": "데이터없음", "year_2023": "데이터없음", "year_2024": "https://v.daum.net/v/Wun1pAaV8I" }, "overseas": { "year_2022": "데이터없음", "year_2023": "데이터없음", "year_2024": "데이터없음" } } }',
    'citations': [
        'https://v.daum.net/v/Wun1pAaV8I',
        'http://www.inetbank.co.kr/news_cboard.asp?bi=54&page=16&startpage=1&style=board3',
        'https://www.globalict.kr/upload_file/kms/202403/54723923920628804.pdf',
        'http://www.inetbank.co.kr/news_cboard.asp?bi=55&page=16&startpage=11&style=board3',
        'https://ssl.pstatic.net/imgstock/upload/research/company/1636600850257.pdf'
    ],
    'usage': {
        'prompt_tokens': 978,
        'completion_tokens': 363,
        'total_tokens': 1341,
        'search_context_size': 'low'
    },
    'success': True
}
    parsed_data = PerplexityMarketResearch()._parse_market_data(data)
    save_to_excel_v2('item_info3.xlsx', '공유기', parsed_data)
    print(parsed_data)