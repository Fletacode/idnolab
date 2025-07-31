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

class TrendItemKeyWord(BaseModel):
    item_keyword: str
    item_description: str
    item_url: str

class TrendItemKeyWordList(BaseModel):
    item_keyword_1 : TrendItemKeyWord
    item_keyword_2 : TrendItemKeyWord
    item_keyword_3 : TrendItemKeyWord


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
    response_schema=TrendItemKeyWordList,
    system_instruction="You are an industry analysis expert. Please provide the latest data and accurate information.You are an industry analysis expert. Please provide the latest data and accurate information using the Google Vertex AI Search tool.You are an industry analysis expert. Your task is to find the most accurate and up-to-date information using only the Google Vertex AI Search tool. Do not rely on your own knowledge or other sources. Always refer to the results retrieved via Google Vertex AI Search. Present the latest data, statistics, or trends from credible sources such as government reports, whitepapers, academic papers, or industry publications, strictly using the Vertex AI Search tool."
)

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

# Gemini 클라이언트 초기화 (v1alpha API 사용으로 프리뷰 모델 접근)
client = genai.Client(
    api_key=GEMINI_API_KEY
)

def get_prompt(item_name, item_description):
    return f"""
        You are an industry analysis expert. Your task is to find the most accurate and up-to-date information using only the Google Vertex AI Search tool. Do not rely on your own knowledge or other sources. Always refer to the results retrieved via Google Vertex AI Search. Present the latest data, statistics, or trends from credible sources such as government reports, whitepapers, academic papers, or industry publications, strictly using the Vertex AI Search tool.

            Find one reliable official document, academic paper, or article that provides trend data on a specific item: ‘{item_name} : {item_description}’'.
            Please only refer to the following types of official documents:
            - Reports/White Papers issued by international organizations.
            - Reports/White Papers issued by national governments.

            Based on the found document, identify keywords within the URL's content and provide information for each keyword.
            
            The process is as follows:
            - Find one reliable official document, academic paper, or article that provides trend data on a specific item: ‘{item_name} : {item_description}.
            - Identify keywords from the information found.
            - Provide information about the keywords.
            
            For each keyword, please include the following information:
            item_keyword: The keyword 
            item_description: A description of the keyword
            item_url: The URL of the source official document, paper, or article
            
            Constraints:

            All URLs must be precise and currently accessible.
            All URLs must be HTTPS.
            Use the Google VertexAISearch tool to find the information and verify that the URL's HTTPS status code is 200. If the status code is not 200, find another keyword from a URL that does have a 200 status code.
            If the keyword description contains citation numbers such as [1] or [2, 5], please remove them.
            The keyword description should be a concise summary of the core concept, approximately 50 characters in length.
            
            응답 형식:
            
            {{
                "item_keyword_1": {{
                    "item_keyword": "keyword",
                    "item_description": "keyword description",
                    "item_url": "source official document, paper, or article URL"
                }},
                "item_keyword_2": {{
                    "item_keyword": "keyword",
                    "item_description": "keyword description",
                    "item_url": "source official document, paper, or article URL"
                }},
                "item_keyword_3": {{
                    "item_keyword": "keyword",
                    "item_description": "keyword description",
                    "item_url": "source official document, paper, or article URL"
                }}
            }}  
                        
    """

def get_item_keyword_with_gemini(item_name, item_description, max_retries=3):
    """
    Gemini API를 사용하여 특정 물품과 관련된 트렌드 기업 정보를 요청
    """
    logger.debug(f"'{item_name}' 항목에 대한 트렌드 기업 정보 Gemini API 호출 시작")
    
    try:
        logger.debug(f"API 호출 시도")
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents= get_prompt(item_name, item_description),            
            config=config
        )
        
        logger.debug(f"'{item_name}' 트렌드 기업 정보 API 호출 성공")
        # logger.debug(f"응답 길이: {len(response.text)} 문자")
        return response.text
            
    except Exception as e:
        # logger.error(f"API 호출 오류 발생: {e} {response.text}")
        raise e


def parse_item_keyword_with_gemini(response_text):
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

    response_text = get_item_keyword_with_gemini("카메라", "카메라는 사진을 촬영하는 장치입니다.")
    

    parsed_data = parse_item_keyword_with_gemini(response_text)
    
    df = pd.read_excel("item_info_keyword.xlsx", sheet_name="Sheet1")
    df.astype(object)

    for index, row in df.iterrows():
        if index == 1:
            update_row = save_to_excel(row, parsed_data)
            df.loc[index] = update_row
            df.to_excel("item_info_keyword.xlsx", sheet_name="Sheet1", index=False)
            logger.info(f"키워드 정보 저장 완료: {row['code_name']}: {index}")