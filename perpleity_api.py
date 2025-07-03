import requests
import json
import time
import os
from dotenv import load_dotenv
from logger_config import get_logger
from save_excel2 import save_to_excel_v2, find_item_row

# 환경변수 로드
load_dotenv()

# 로거 설정
logger = get_logger("perplexity_api")

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

        다음 JSON 형식으로 응답해주세요:
        {{
            "market_size": {{
                "국내": {{
                    "2022": "구체적인 금액 또는 추정값",
                    "2023": "구체적인 금액 또는 추정값", 
                    "2024": "구체적인 금액 또는 추정값"
                }},
                "해외": {{
                    "2022": "구체적인 금액 또는 추정값",
                    "2023": "구체적인 금액 또는 추정값",
                    "2024": "구체적인 금액 또는 추정값"
                }}
            }},
            "isEstimated":{{
                "국내": {{
                    "2022": "추정 | 실제금액",
                    "2023": "추정 | 실제금액",
                    "2024": "추정 | 실제금액"
                }},
                "해외": {{
                    "2022": "추정 | 실제금액",
                    "2023": "추정 | 실제금액",
                    "2024": "추정 | 실제금액"
                }}
            }},
            "estimateReason":{{
                "국내": {{
                    "2022": "추정 근거",
                    "2023": "추정 근거",
                    "2024": "추정 근거"
                }},
                "해외": {{
                    "2022": "추정 근거",
                    "2023": "추정 근거",
                    "2024": "추정 근거"
                }}
            }},
            "references": {{
                "국내": {{
                    "2022": "출처 URL",
                    "2023": "출처 URL",
                    "2024": "출처 URL"
                }},
                "해외": {{
                    "2022": "출처 URL", 
                    "2023": "출처 URL",
                    "2024": "출처 URL"
                }}
            }}
        }}

        요구사항:
        1. 시장 규모는 반드시 구체적인 금액으로 제공 (백분율이나 출하량 제외)
        2. 한국 시장은 원화 단위, 해외 시장은 달러 단위, 단위 표시하지 않고 천원 단위의 숫자로만 표기
        3. 직접적인 시장 규모 데이터가 없는 경우:
           - 관련 산업 데이터, 유사 제품 시장 규모, 시장 점유율, 성장률 등을 수집
           - 이러한 데이터를 바탕으로 시장 규모를 합리적으로 추정
           - 추정값은 "숫자(추정)" 형태로 표시 (예: "5000000000(추정)")
           - 추정 근거와 사용된 데이터 출처(URL)을 references에 상세히 기록 [1],[2] 이러한 주석 형태가 아닌 URL 형태로 기록
           - citations의 출처 URL을 references에 매칭하여 제공
        4. 추정 시 고려사항:
           - 상위 카테고리 시장 규모에서 해당 제품의 예상 점유율 계산
           - 유사 제품군의 시장 규모와 비교 분석
           - 연평균 성장률(CAGR)을 활용한 추정
           - 인구, 경제 규모, 기술 보급률 등 거시경제 지표 활용
        5. 신뢰할 수 있는 출처의 URL만 제공
        6. 최신 데이터 우선 제공
        7. 완전히 데이터를 찾을 수 없는 경우에만 "데이터없음"으로 표시

        '{item_name}' 시장 규모 데이터를 조사하고, 직접 데이터가 없으면 관련 데이터를 수집하여 합리적으로 추정해주세요.
        """
        
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 정확한 시장 데이터를 제공하는 전문 시장 분석가입니다. 항상 JSON 형식으로 응답하고, 신뢰할 수 있는 출처만 인용합니다. 직접적인 시장 규모 데이터가 없는 경우 관련 산업 데이터, 유사 제품 시장 규모, 시장 점유율 등을 수집하여 합리적으로 추정하고, 추정값은 '숫자(추정)' 형태로 표시하며, 추정 근거를 상세히 기록합니다."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "return_citations": True,
            "return_images": False,
            "return_related_questions": False,
            "stream": False,
            "presence_penalty": 0,
            "frequency_penalty": 1
        }
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"API 호출 시도 {attempt + 1}/{max_retries}")
                
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=30
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
            
            print("api_response: ", api_response)

            
            # JSON 블록 추출
            json_text = content.strip()
            
            # sonar-reasoning 모델의 <think> 태그 처리
            if '<think>' in json_text and '</think>' in json_text:
                # <think> 태그 이후의 내용에서 JSON 추출
                think_end = json_text.find('</think>') + 8
                json_text = json_text[think_end:].strip()
                logger.debug("sonar-reasoning 모델의 <think> 태그 제거 완료")
            
            # ```json으로 시작하는 경우 JSON 부분만 추출
            if '```json' in json_text:
                start = json_text.find('```json') + 7
                end = json_text.find('```', start)
                if end != -1:
                    json_text = json_text[start:end].strip()
            elif '```' in json_text and '{' in json_text:
                # ```로 감싸진 JSON 블록 추출
                start = json_text.find('{')
                end = json_text.rfind('}') + 1
                if start != -1 and end > start:
                    json_text = json_text[start:end]
            elif '{' in json_text and '}' in json_text:
                # { } 사이의 JSON 부분만 추출
                start = json_text.find('{')
                end = json_text.rfind('}') + 1
                if start != -1 and end > start:
                    json_text = json_text[start:end]
            
            # sonar 모델용 JSON 정리 (주석 제거)
            json_text = self._clean_json_for_sonar_model(json_text)
            
            # JSON 파싱 시도
            try:
                parsed_data = json.loads(json_text)
                # print("parsed_data: ", parsed_data)
                return parsed_data
            except json.JSONDecodeError as e:
                logger.warning(f"첫 번째 JSON 파싱 실패: {e}")
                # 더 강력한 JSON 추출 시도
                return self._extract_json_with_fallback(content)
            
        except Exception as e:
            logger.error(f"데이터 파싱 중 오류 발생: {e}")
            return None
    
    def _extract_json_with_fallback(self, content):
        """
        JSON 파싱이 실패했을 때 더 강력한 방법으로 JSON 추출 시도
        
        Args:
            content (str): 원본 응답 내용
            
        Returns:
            dict: 파싱된 데이터 또는 None
        """
        import re
        
        try:
            logger.info("Fallback JSON 추출 시도")
            
            # 방법 1: 정규식으로 JSON 객체 추출
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, content, re.DOTALL)
            
            for match in json_matches:
                try:
                    # 제어 문자 제거
                    clean_match = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', match)
                    parsed = json.loads(clean_match)
                    if isinstance(parsed, dict) and 'market_size' in parsed:
                        logger.info("정규식 방법으로 JSON 추출 성공")
                        
                        return parsed
                except:
                    continue
            
            # 방법 2: 중괄호 균형 맞추기로 JSON 추출
            brace_count = 0
            start_pos = -1
            
            for i, char in enumerate(content):
                if char == '{':
                    if start_pos == -1:
                        start_pos = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_pos != -1:
                        json_candidate = content[start_pos:i+1]
                        try:
                            # 제어 문자 제거
                            clean_candidate = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_candidate)
                            parsed = json.loads(clean_candidate)
                            if isinstance(parsed, dict) and 'market_size' in parsed:
                                logger.info("중괄호 균형 방법으로 JSON 추출 성공")
                                
                                return parsed
                        except:
                            pass
                        start_pos = -1
            
            # 방법 3: 수동으로 데이터 추출 (최후의 수단)
            return self._manual_data_extraction(content)
            
        except Exception as e:
            logger.error(f"Fallback JSON 추출 실패: {e}")
            return None
    
    def _manual_data_extraction(self, content):
        """
        JSON 파싱이 완전히 실패했을 때 수동으로 데이터 추출
        
        Args:
            content (str): 원본 응답 내용
            
        Returns:
            dict: 추출된 데이터 또는 None
        """
        try:
            logger.info("수동 데이터 추출 시도")
            
            # 새로운 JSON 양식에 맞는 기본 구조 생성
            result = {
                "market_size": {"국내": {}, "해외": {}},
                "isEstimated": {"국내": {}, "해외": {}},
                "estimateReason": {"국내": {}, "해외": {}},
                "references": {"국내": {}, "해외": {}}
            }
            
            # 숫자 패턴으로 시장 규모 추출
            import re
            
            years = ["2022", "2023", "2024"]
            
            # 국내 시장 규모 추출
            domestic_patterns = [
                r'"국내"[^}]*"2022"[^"]*"([^"]*)"',
                r'"국내"[^}]*"2023"[^"]*"([^"]*)"',
                r'"국내"[^}]*"2024"[^"]*"([^"]*)"'
            ]
            
            for i, pattern in enumerate(domestic_patterns):
                match = re.search(pattern, content)
                if match:
                    market_value = match.group(1)
                    result["market_size"]["국내"][years[i]] = market_value
                    
                    # 추정 여부 판단 (값에 "추정"이 포함되어 있으면 추정, 아니면 실제금액)
                    if "(추정)" in market_value:
                        result["isEstimated"]["국내"][years[i]] = "추정"
                        result["estimateReason"]["국내"][years[i]] = "API 응답에서 추정값으로 표시됨"
                    else:
                        result["isEstimated"]["국내"][years[i]] = "실제금액"
                        result["estimateReason"]["국내"][years[i]] = "API 응답에서 실제 수치로 표시됨"
                else:
                    result["market_size"]["국내"][years[i]] = "데이터없음"
                    result["isEstimated"]["국내"][years[i]] = "데이터없음"
                    result["estimateReason"]["국내"][years[i]] = "데이터없음"
            
            # 해외 시장 규모 추출
            overseas_patterns = [
                r'"해외"[^}]*"2022"[^"]*"([^"]*)"',
                r'"해외"[^}]*"2023"[^"]*"([^"]*)"',
                r'"해외"[^}]*"2024"[^"]*"([^"]*)"'
            ]
            
            for i, pattern in enumerate(overseas_patterns):
                match = re.search(pattern, content)
                if match:
                    market_value = match.group(1)
                    result["market_size"]["해외"][years[i]] = market_value
                    
                    # 추정 여부 판단
                    if "(추정)" in market_value:
                        result["isEstimated"]["해외"][years[i]] = "추정"
                        result["estimateReason"]["해외"][years[i]] = "API 응답에서 추정값으로 표시됨"
                    else:
                        result["isEstimated"]["해외"][years[i]] = "실제금액"
                        result["estimateReason"]["해외"][years[i]] = "API 응답에서 실제 수치로 표시됨"
                else:
                    result["market_size"]["해외"][years[i]] = "데이터없음"
                    result["isEstimated"]["해외"][years[i]] = "데이터없음"
                    result["estimateReason"]["해외"][years[i]] = "데이터없음"
            
            # references 정보 추출 시도 및 실패 시 해당 시장 규모 데이터 삭제
            try:
                # references 섹션 찾기
                ref_start = content.find('"references"')
                if ref_start != -1:
                    # 국내 references 추출
                    domestic_ref_patterns = [
                        r'"references"[^}]*"국내"[^}]*"2022"[^"]*"([^"]*)"',
                        r'"references"[^}]*"국내"[^}]*"2023"[^"]*"([^"]*)"',
                        r'"references"[^}]*"국내"[^}]*"2024"[^"]*"([^"]*)"'
                    ]
                    
                    for i, pattern in enumerate(domestic_ref_patterns):
                        match = re.search(pattern, content, re.DOTALL)
                        if match:
                            ref_text = match.group(1)
                            # 제어 문자 제거
                            ref_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', ref_text)
                            result["references"]["국내"][years[i]] = ref_text[:200] + "..." if len(ref_text) > 200 else ref_text
                        else:
                            # 참조 정보 추출 실패 시 해당 연도의 모든 데이터 삭제
                            logger.warning(f"국내 {years[i]}년 참조 정보 추출 실패, 모든 관련 데이터 삭제")
                            if years[i] in result["market_size"]["국내"]:
                                del result["market_size"]["국내"][years[i]]
                            if years[i] in result["isEstimated"]["국내"]:
                                del result["isEstimated"]["국내"][years[i]]
                            if years[i] in result["estimateReason"]["국내"]:
                                del result["estimateReason"]["국내"][years[i]]
                            # references에서도 해당 연도 항목 삭제 (흔적 제거)
                    
                    # 해외 references 추출
                    overseas_ref_patterns = [
                        r'"references"[^}]*"해외"[^}]*"2022"[^"]*"([^"]*)"',
                        r'"references"[^}]*"해외"[^}]*"2023"[^"]*"([^"]*)"',
                        r'"references"[^}]*"해외"[^}]*"2024"[^"]*"([^"]*)"'
                    ]
                    
                    for i, pattern in enumerate(overseas_ref_patterns):
                        match = re.search(pattern, content, re.DOTALL)
                        if match:
                            ref_text = match.group(1)
                            # 제어 문자 제거
                            ref_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', ref_text)
                            result["references"]["해외"][years[i]] = ref_text[:200] + "..." if len(ref_text) > 200 else ref_text
                        else:
                            # 참조 정보 추출 실패 시 해당 연도의 모든 데이터 삭제
                            logger.warning(f"해외 {years[i]}년 참조 정보 추출 실패, 모든 관련 데이터 삭제")
                            if years[i] in result["market_size"]["해외"]:
                                del result["market_size"]["해외"][years[i]]
                            if years[i] in result["isEstimated"]["해외"]:
                                del result["isEstimated"]["해외"][years[i]]
                            if years[i] in result["estimateReason"]["해외"]:
                                del result["estimateReason"]["해외"][years[i]]
                            # references에서도 해당 연도 항목 삭제 (흔적 제거)
                else:
                    # references 섹션을 찾지 못한 경우 - 모든 데이터 삭제
                    logger.warning("references 섹션을 찾지 못함, 모든 데이터 삭제")
                    result["market_size"]["국내"] = {}
                    result["market_size"]["해외"] = {}
                    result["isEstimated"]["국내"] = {}
                    result["isEstimated"]["해외"] = {}
                    result["estimateReason"]["국내"] = {}
                    result["estimateReason"]["해외"] = {}
                    result["references"]["국내"] = {}
                    result["references"]["해외"] = {}
                            
            except Exception as ref_e:
                logger.warning(f"References 추출 중 오류: {ref_e}, 모든 데이터 삭제")
                # references 추출 실패 시 모든 데이터 삭제
                result["market_size"]["국내"] = {}
                result["market_size"]["해외"] = {}
                result["isEstimated"]["국내"] = {}
                result["isEstimated"]["해외"] = {}
                result["estimateReason"]["국내"] = {}
                result["estimateReason"]["해외"] = {}
                result["references"]["국내"] = {}
                result["references"]["해외"] = {}
            
            logger.info("수동 데이터 추출 완료")
            return result
            
        except Exception as e:
            logger.error(f"수동 데이터 추출 실패: {e}")
            return None
    
    def _clean_json_for_sonar_model(self, json_text):
        """
        sonar 모델의 JSON 응답에서 주석과 불완전한 부분을 정리
        
        Args:
            json_text (str): 원본 JSON 텍스트
            
        Returns:
            str: 정리된 JSON 텍스트
        """
        try:
            # 제어 문자 제거 (JSON에서 허용되지 않는 문자들)
            import re
            # 제어 문자 제거 (탭, 개행, 캐리지 리턴 제외)
            json_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_text)
            
            lines = json_text.split('\n')
            cleaned_lines = []
            in_comment_block = False
            brace_count = 0
            
            for line in lines:
                stripped_line = line.strip()
                
                # 빈 줄 건너뛰기
                if not stripped_line:
                    continue
                
                # // 주석으로 시작하는 줄 제거
                if stripped_line.startswith('//'):
                    continue
                
                # 여러 줄 주석 블록 처리
                if '/*' in stripped_line and '*/' in stripped_line:
                    # 한 줄에 시작과 끝이 모두 있는 경우
                    start = stripped_line.find('/*')
                    end = stripped_line.find('*/') + 2
                    cleaned_line = stripped_line[:start] + stripped_line[end:]
                    if cleaned_line.strip():
                        cleaned_lines.append(cleaned_line)
                    continue
                elif '/*' in stripped_line:
                    # 여러 줄 주석 시작
                    in_comment_block = True
                    before_comment = stripped_line[:stripped_line.find('/*')]
                    if before_comment.strip():
                        cleaned_lines.append(before_comment)
                    continue
                elif '*/' in stripped_line:
                    # 여러 줄 주석 끝
                    in_comment_block = False
                    after_comment = stripped_line[stripped_line.find('*/') + 2:]
                    if after_comment.strip():
                        cleaned_lines.append(after_comment)
                    continue
                
                # 주석 블록 안에 있으면 건너뛰기
                if in_comment_block:
                    continue
                
                # 인라인 주석 제거 (문자열 내부가 아닌 경우에만)
                if '//' in stripped_line:
                    # 문자열 내부인지 확인
                    quote_count = 0
                    comment_pos = -1
                    for i, char in enumerate(stripped_line):
                        if char == '"' and (i == 0 or stripped_line[i-1] != '\\'):
                            quote_count += 1
                        elif char == '/' and i < len(stripped_line) - 1 and stripped_line[i+1] == '/' and quote_count % 2 == 0:
                            comment_pos = i
                            break
                    
                    if comment_pos != -1:
                        stripped_line = stripped_line[:comment_pos].strip()
                
                # 중괄호 개수 추적
                brace_count += stripped_line.count('{') - stripped_line.count('}')
                
                # 유효한 줄만 추가
                if stripped_line:
                    cleaned_lines.append(stripped_line)
                
                # JSON 객체가 완료되면 중단 (추가적인 텍스트 무시)
                if brace_count == 0 and '{' in ''.join(cleaned_lines):
                    break
            
            # 불완전한 마지막 항목 정리
            cleaned_text = '\n'.join(cleaned_lines)
            
            # 마지막 쉼표 뒤에 불완전한 내용이 있으면 제거
            if cleaned_text.endswith(','):
                cleaned_text = cleaned_text.rstrip(',')
            
            # 불완전한 문자열 값 정리
            cleaned_text = self._fix_incomplete_json_values(cleaned_text)
            
            logger.debug("sonar 모델 JSON 정리 완료")
            return cleaned_text
            
        except Exception as e:
            logger.warning(f"JSON 정리 중 오류 발생: {e}, 원본 반환")
            return json_text
    
    def _fix_incomplete_json_values(self, json_text):
        """
        불완전한 JSON 값들을 수정
        
        Args:
            json_text (str): JSON 텍스트
            
        Returns:
            str: 수정된 JSON 텍스트
        """
        try:
            # 불완전한 문자열 값 찾기 및 수정
            lines = json_text.split('\n')
            fixed_lines = []
            
            for line in lines:
                # 따옴표로 시작하지만 제대로 닫히지 않은 값 찾기
                if ':' in line and '"' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key_part = parts[0].strip()
                        value_part = parts[1].strip()
                        
                        # 값 부분이 따옴표로 시작하지만 제대로 끝나지 않는 경우
                        if value_part.startswith('"') and not (value_part.endswith('"') or value_part.endswith('",') or value_part.endswith('"}')):
                            # 불완전한 값을 "데이터없음"으로 대체
                            if value_part.endswith(','):
                                fixed_value = '"데이터없음",'
                            elif line.strip().endswith('}'):
                                fixed_value = '"데이터없음"'
                            else:
                                fixed_value = '"데이터없음"'
                            
                            line = f"{key_part}: {fixed_value}"
                            logger.debug(f"불완전한 값 수정: {value_part} -> {fixed_value}")
                
                fixed_lines.append(line)
            
            return '\n'.join(fixed_lines)
            
        except Exception as e:
            logger.warning(f"JSON 값 수정 중 오류 발생: {e}, 원본 반환")
            return json_text
    
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
            
            # 2. 응답 데이터 파싱
            parsed_data = self._parse_market_data(api_response)
            
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


def main():
    """
    메인 실행 함수
    """
    logger.info("퍼플렉시티 시장 조사 프로그램 시작")
    
    # 퍼플렉시티 API 클라이언트 초기화
    try:
        perplexity_client = PerplexityMarketResearch()
    except ValueError as e:
        logger.error(f"클라이언트 초기화 실패: {e}")
        print("오류: .env 파일에 PERPLEXITY_API_KEY를 설정해주세요.")
        return
    
    # 엑셀 파일 경로
    excel_file_path = 'item_info3.xlsx'
    
    # 테스트 항목
    test_item = '공유기'
    
    print(f"'{test_item}' 시장 규모 조사 시작...")
    logger.info(f"테스트 항목: {test_item}")
    
    # 시장 조사 및 저장 실행
    success = perplexity_client.research_parse(test_item)
    
    if success:
        print(f"✅ '{test_item}' 시장 규모 데이터 조사 및 저장 완료!")
        logger.info("테스트 완료 - 성공")
    else:
        print(f"❌ '{test_item}' 시장 규모 조사 실패")
        logger.error("테스트 완료 - 실패")
    
    logger.info("퍼플렉시티 시장 조사 프로그램 종료")


if __name__ == "__main__":
    main()
