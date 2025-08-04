from pydantic import BaseModel, Field
from dotenv import load_dotenv
from logger_config import setup_logger
import os
import time
import json
from google import genai
from google.genai import types
import pandas as pd
from typing import Optional, Dict, Any
import requests

# .env 파일에서 환경변수 로드
load_dotenv()

# 로거 설정
logger = setup_logger(__name__)

# 검증 결과를 위한 Pydantic 모델
class ValidationScore(BaseModel):
    url_accessibility: int = Field(ge=0, le=10, description="URL 접근 가능성 점수 (0-10)")
    url_content_relevance: int = Field(ge=0, le=10, description="URL 내용과 키워드 관련성 점수 (0-10)")
    total_score: int = Field(ge=0, le=20, description="총점 (0-20)")
    validation_details: Optional[str] = Field(default=None, description="검증 상세 내용")

class KeywordValidationResult(BaseModel):
    item_name: str
    item_keyword: str
    item_description: str
    item_url: str
    validation_score: ValidationScore
    is_valid: bool = Field(description="전체 검증 통과 여부")

url_context_tool = types.Tool(
    url_context = types.UrlContext()
)

# 검증을 위한 Gemini API 설정
validation_config = types.GenerateContentConfig(
    tools=[url_context_tool],
    response_mime_type="text/plain",
    response_schema=ValidationScore,
    system_instruction="You are a data validation expert. Evaluate the given information and provide accurate scoring based on the criteria."
)

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

# Gemini 클라이언트 초기화
client = genai.Client(
    api_key=GEMINI_API_KEY
)

def get_validation_prompt(item_name: str, item_keyword: str, item_description: str, item_url: str) -> str:
    """검증을 위한 프롬프트 생성"""
    return f"""
    You are a data validation expert. Please evaluate the following information and provide accurate scores according to each criterion.
    
    IMPORTANT: Use the URL Context tool to access and analyze the content at the provided URL: {item_url}

    Information to validate:
    - Item Name: {item_name}
    - Keyword: {item_keyword}
    - Keyword Description: {item_description}
    - Reference URL: {item_url}

    Evaluation Criteria:
    1. url_accessibility (0-10 points): Evaluate URL accessibility using the URL Context tool
       - 10 points: HTTPS and fully accessible with valid content
       - 7-9 points: Accessible with some issues
       - 4-6 points: Limited accessibility
       - 1-3 points: Difficult to access
       - 0 points: Inaccessible or invalid URL

    2. url_content_relevance (0-10 points): Evaluate relevance between URL content and keyword by analyzing the actual content using URL Context tool
       - 10 points: URL content perfectly relates to the keyword
       - 7-9 points: High relevance
       - 4-6 points: Moderate relevance
       - 1-3 points: Low relevance
       - 0 points: Completely unrelated

    3. total_score: Sum of the three scores above (0-20 points)

    4. validation_details: Detailed explanation for each evaluation based on the actual content retrieved from the URL

    Please respond in JSON format:
    {{
        "url_accessibility": score,
        "url_content_relevance": score,
        "total_score": total_score,
        "validation_details": "detailed explanation"
    }}
    """

def validate_keyword_with_gemini(item_name: str, item_keyword: str, item_description: str, item_url: str, max_retries: int = 3) -> ValidationScore:
    """
    Gemini API를 사용하여 키워드 데이터의 유효성을 검증
    """
    logger.debug(f"'{item_name}' - '{item_keyword}' 검증 시작")
    
    for retry in range(max_retries):
        try:
            logger.debug(f"검증 API 호출 시도 {retry + 1}/{max_retries}")
            
            # URL 접근성 사전 체크
            url_accessible = check_url_accessibility(item_url)
            
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=get_validation_prompt(item_name, item_keyword, item_description, item_url),
                config=validation_config
            )
            
            # 응답 파싱
            validation_result = parse_validation_response(response.text)
            
            # URL 접근성 점수 조정 (실제 체크 결과 반영)
            # Gemini가 URL Context tool로 접근 성공했다면 그 결과를 신뢰
            # 로컬 체크가 실패했어도 Gemini가 높은 점수를 주었다면 유지
            if not url_accessible and validation_result.url_accessibility < 5:
                # 로컬 체크 실패 + Gemini도 낮은 점수 = 0점
                validation_result.url_accessibility = 0
                validation_result.total_score = (
                    validation_result.url_accessibility + 
                    validation_result.url_content_relevance
                )
            # 그 외의 경우는 Gemini의 판단을 신뢰
            
            logger.debug(f"'{item_keyword}' 검증 완료 - 총점: {validation_result.total_score}/20")
            return validation_result
            
        except Exception as e:
            logger.error(f"검증 API 호출 오류 (시도 {retry + 1}/{max_retries}): {e}")
            if retry == max_retries - 1:
                # 마지막 시도에서도 실패하면 기본값 반환
                return ValidationScore(
                    url_accessibility=0,
                    url_content_relevance=0,
                    total_score=0,
                    validation_details=f"검증 실패: {str(e)}"
                )
            time.sleep(2 ** retry)  # 지수 백오프

def check_url_accessibility(url: str) -> bool:
    """URL 접근 가능성 체크"""
    try:
        # HEAD 요청 먼저 시도
        response = requests.head(url, timeout=5, allow_redirects=True, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if response.status_code == 200:
            return True
        
        # HEAD 실패 시 GET 요청으로 재시도 (일부만 다운로드)
        response = requests.get(url, timeout=5, allow_redirects=True, stream=True, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.close()  # 스트림 닫기
        return response.status_code == 200
    except:
        return False

def parse_validation_response(response_text: str) -> ValidationScore:
    """Gemini API 응답을 파싱하여 ValidationScore 객체로 변환"""
    try:
        # JSON 문자열 파싱
        json_text = response_text.strip()
        
        # 코드 블록 제거
        if '```json' in json_text:
            start = json_text.find('```json') + 7
            end = json_text.find('```', start)
            if end != -1:
                json_text = json_text[start:end].strip()
        elif '```' in json_text:
            start = json_text.find('```') + 3
            end = json_text.rfind('```')
            if end > start:
                json_text = json_text[start:end].strip()
        
        # JSON 파싱
        parsed_data = json.loads(json_text)
        
        # ValidationScore 객체 생성
        return ValidationScore(**parsed_data)
        
    except Exception as e:
        logger.error(f"검증 응답 파싱 오류: {e}")
        raise e

def validate_keyword_data(df: pd.DataFrame, output_file: str = "validation_results.xlsx"):
    """
    엑셀 파일의 키워드 데이터를 검증하고 결과를 저장
    """
    logger.info("키워드 데이터 검증 시작")
    
    results = []
    
    temp = [33]

    for index, row in df.iterrows():
        if index not in temp:
            continue 
        item_name = row.get('code_name', '')
        
        # 각 키워드 컬럼 검증 (item_keyword_1, item_keyword_2, item_keyword_3)
        for i in range(1, 4):
            keyword_col = f'item_keyword_{i}'
            description_col = f'item_description_{i}'
            url_col = f'item_url_{i}'
            
            if keyword_col in row and pd.notna(row[keyword_col]):
                keyword = row[keyword_col]
                description = row.get(description_col, '')
                url = row.get(url_col, '')
                
                if keyword and description and url:
                    logger.info(f"검증 중: {item_name} - {keyword}")
                    
                    # 검증 수행
                    validation_score = validate_keyword_with_gemini(
                        item_name=item_name,
                        item_keyword=keyword,
                        item_description=description,
                        item_url=url
                    )
                    
                    # 검증 결과 저장
                    result = KeywordValidationResult(
                        item_name=item_name,
                        item_keyword=keyword,
                        item_description=description,
                        item_url=url,
                        validation_score=validation_score,
                        is_valid=validation_score.total_score >= 17  # 70% 이상이면 유효
                    )
                    
                    results.append(result.dict())
                    
                    # 진행 상황 로깅
                    logger.info(f"검증 완료: {keyword} - 점수: {validation_score.total_score}/20")
                    
                    # API 호출 제한을 위한 대기
                    time.sleep(1)
    
    # 결과를 DataFrame으로 변환하여 엑셀로 저장
    if results:
        results_df = pd.DataFrame(results)
        
        # validation_score를 개별 컬럼으로 확장
        score_df = pd.json_normalize(results_df['validation_score'])
        results_df = pd.concat([results_df.drop('validation_score', axis=1), score_df], axis=1)
        
        # 엑셀 파일로 저장
        results_df.to_excel(output_file, index=False)
        logger.info(f"검증 결과 저장 완료: {output_file}")
        
        # 요약 통계 출력
        total_items = len(results)
        valid_items = sum(1 for r in results if r['is_valid'])
        avg_score = sum(r['validation_score']['total_score'] for r in results) / total_items if total_items > 0 else 0
        
        logger.info(f"검증 완료 - 총 {total_items}개 항목")
        logger.info(f"유효 항목: {valid_items}개 ({valid_items/total_items*100:.1f}%)")
        logger.info(f"평균 점수: {avg_score:.1f}/30")
    else:
        logger.warning("검증할 데이터가 없습니다.")




if __name__ == "__main__":
    import argparse
    
    # 명령줄 인자 파서 설정
    parser = argparse.ArgumentParser(description='키워드 데이터 유효성 검증')
    parser.add_argument('--input', '-i', type=str, default='item_info_keyword_v1.0.xlsx',
                        help='검증할 엑셀 파일 경로 (기본값: item_info_keyword_v1.0.xlsx)')
    parser.add_argument('--output', '-o', type=str, default='validation_results.xlsx',
                        help='검증 결과를 저장할 엑셀 파일 경로 (기본값: validation_results.xlsx)')
    parser.add_argument('--test', action='store_true',
                        help='테스트 모드 (첫 번째 항목만 검증)')
    
    args = parser.parse_args()
    
    try:
        # 엑셀 파일 읽기
        logger.info(f"엑셀 파일 읽기: {args.input}")
        df = pd.read_excel(args.input, sheet_name="Sheet1")
        
        # 테스트 모드인 경우 첫 번째 행만 처리
        if args.test:
            logger.info("테스트 모드: 첫 번째 항목만 검증합니다.")
            df = df.head(1)
        
        # 검증 수행
        validate_keyword_data(df, args.output)
        
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {args.input}")
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        raise e