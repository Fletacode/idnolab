from google import genai
from google.genai import types
import pandas as pd
from gemini_api import get_prompt
import os
import json
import time

GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

client = genai.Client(
    api_key=GEMINI_API_KEY
)

def transform_to_json(data_list, filename="batch_requests.jsonl"):
    """
    리스트 형태의 데이터를 JSONL 파일로 저장하는 함수
    
    Args:
        data_list (list): JSON으로 변환할 리스트 데이터
        filename (str): 저장할 파일명
    """
    try:
        # JSONL 형식으로 저장 (각 줄이 하나의 JSON 객체)
        with open(filename, 'w', encoding='utf-8') as f:
            for item in data_list:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')  # 각 JSON 객체 후 줄바꿈
            
        # 파일 크기 확인
        file_size = os.path.getsize(filename)
        print(f"JSONL 파일 저장 완료 - 파일: {filename}, 크기: {file_size} bytes")
        print(f"저장된 요청 개수: {len(data_list)}")
        
        # JSONL 파일 내용 미리보기 (처음 3줄)
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:3]
            print(f"파일 내용 미리보기:")
            for i, line in enumerate(lines):
                print(f"  줄 {i+1}: {line.strip()[:100]}...")
            
        return True
        
    except Exception as e:
        print(f"JSONL 변환/저장 중 오류: {e}")
        return False


def upload_file_to_genai(file_path, display_name=None):
    """
    파일을 Google GenAI에 업로드하고 URI 반환
    
    Args:
        file_path (str): 업로드할 파일 경로
        display_name (str): 파일 표시 이름
    """
    try:
        if display_name is None:
            display_name = os.path.basename(file_path)
            
        print(f"파일 업로드 시작: {file_path}")
        
        # 파일 업로드 - 'file' 매개변수 사용
        uploaded_file = client.files.upload(
            file=file_path  # 'path' 대신 'file' 사용
        )
        
        print(f"파일 업로드 완료:")
        print(f"- 파일 URI: {uploaded_file.uri}")
        print(f"- 파일 이름: {uploaded_file.name}")
        print(f"- 파일 크기: {uploaded_file.size_bytes} bytes")
        print(f"- 생성 시간: {uploaded_file.create_time}")
        
        return uploaded_file.uri
        
    except Exception as e:
        print(f"파일 업로드 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_batch_job_with_file(file_uri, job_name="trend-companies-batch-job"):
    """
    업로드된 파일 URI를 사용하여 배치 작업 생성
    
    Args:
        file_uri (str): 업로드된 파일의 URI
        job_name (str): 배치 작업 표시 이름
    """
    try:
        print(f"배치 작업 생성 시작: {job_name}")
        
        # 배치 작업 생성
        batch_job = client.batches.create(
            model="models/gemini-2.5-pro",
            src=file_uri,  # 업로드된 파일 URI 사용
            config=types.CreateBatchJobConfig(
                display_name=job_name
            )
        )
        
        print(f"배치 작업 생성 완료:")
        print(f"- 작업 ID: {batch_job.name}")
        print(f"- 상태: {batch_job.state}")
        print(f"- 모델: {batch_job.model}")
        print(f"- 표시 이름: {batch_job.display_name}")
        print(f"- 생성 시간: {batch_job.create_time}")
        
        # 배치 작업 정보를 JSON 파일로 저장
        batch_info = {
            "batch_id": batch_job.name,
            "state": batch_job.state,
            "model": batch_job.model,
            "display_name": batch_job.display_name,
            "create_time": str(batch_job.create_time),
            "source_file_uri": file_uri
        }
        
        with open('batch_job_info.json', 'w', encoding='utf-8') as f:
            json.dump(batch_info, f, ensure_ascii=False, indent=4, default=str)
            
        print("배치 작업 정보가 'batch_job_info.json'에 저장되었습니다.")
        
        return batch_job
        
    except Exception as e:
        print(f"배치 작업 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_batch_requests_from_df(df, max_rows=2):
    """
    DataFrame에서 배치 요청 생성
    
    Args:
        df: pandas DataFrame
        max_rows: 처리할 최대 행 수
    """
    batch_requests = []
    
    try:
        for index, row in df.iterrows():
            if index >= max_rows:
                break
            
            # 필요한 컬럼 확인
            if 'code_name' not in row or '개념설명' not in row:
                print(f"인덱스 {index}: 필요한 컬럼이 없습니다.")
                continue
                
            # 빈 값 확인
            if pd.isna(row['code_name']) or pd.isna(row['개념설명']):
                print(f"인덱스 {index}: 빈 값이 있습니다.")
                continue
            
            # 배치 요청 생성 (JSONL 형식)
            batch_request = {
                "custom_id": f"request-{index}",
                "method": "POST",
                "url": "/v1beta/models/gemini-2.5-pro:generateContent",
                "body": {
                    "contents": [{
                        "parts": [{"text": get_prompt(row["code_name"], row["개념설명"])}],
                        "role": "user"
                    }],
                    "generationConfig": {
                        "temperature": 0.0,
                        "maxOutputTokens": 8192,
                        "responseMimeType": "application/json"
                    }
                }
            }
            
            batch_requests.append(batch_request)
            print(f"인덱스 {index}: {row['code_name']} 배치 요청 생성 완료")
        
        print(f"총 {len(batch_requests)}개의 배치 요청 생성 완료")
        return batch_requests
        
    except Exception as e:
        print(f"배치 요청 생성 중 오류: {e}")
        return []


def complete_batch_workflow(excel_file="item_info_trend.xlsx", max_rows=2):
    """
    완전한 배치 처리 워크플로우
    1. Excel 파일 읽기
    2. 배치 요청 생성
    3. JSONL 파일로 저장
    4. 파일 업로드
    5. 배치 작업 생성
    """
    try:
        print("=== 배치 처리 워크플로우 시작 ===")
        
        # 1. Excel 파일 읽기
        print(f"\n1. Excel 파일 읽기: {excel_file}")
        df = pd.read_excel(excel_file, sheet_name="Sheet1")
        df = df.astype(object)
        print(f"Excel 파일 로드 완료. 총 {len(df)}개 행")
        
        # 2. 배치 요청 생성
        print(f"\n2. 배치 요청 생성 (최대 {max_rows}개)")
        batch_requests = create_batch_requests_from_df(df, max_rows)
        
        if not batch_requests:
            print("배치 요청이 생성되지 않았습니다.")
            return None
        
        # 3. JSONL 파일로 저장
        print(f"\n3. JSONL 파일 저장")
        jsonl_filename = "batch_requests.jsonl"
        if not transform_to_json(batch_requests, jsonl_filename):
            print("JSONL 파일 저장에 실패했습니다.")
            return None
        
        # 4. 파일 업로드
        print(f"\n4. 파일 업로드")
        file_uri = upload_file_to_genai(jsonl_filename, "trend-companies-batch-requests")
        
        if not file_uri:
            print("파일 업로드에 실패했습니다.")
            return None
        
        # 5. 배치 작업 생성
        print(f"\n5. 배치 작업 생성")
        batch_job = create_batch_job_with_file(file_uri, "trend-companies-batch-job")
        
        if batch_job:
            print(f"\n=== 배치 처리 워크플로우 완료 ===")
            print(f"배치 작업 ID: {batch_job.name}")
            print(f"상태 확인: monitor_batch_job('{batch_job.name}')")
            print(f"결과 확인: get_batch_results('{batch_job.name}')")
            
            return batch_job
        else:
            print("배치 작업 생성에 실패했습니다.")
            return None
            
    except Exception as e:
        print(f"배치 처리 워크플로우 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_inline_batch_requests(df):
    """
    DataFrame의 데이터를 인라인 배치 요청으로 생성 (딕셔너리 형태)
    """
    inline_requests = []
    
    try:
        for index, row in df.iterrows():
            if index >= 2:  # 처음 2개 행만 처리
                break
            
            # 딕셔너리 형태의 GenerateContentRequest 생성
            request = {
                'contents': [{
                    'parts': [{'text': get_prompt(row["code_name"], row["개념설명"])}],
                    'role': 'user'
                }],
                'generationConfig': {
                    'temperature': 0.0,
                    'maxOutputTokens': 8192,
                    'responseMimeType': 'application/json'
                }
            }
            
            inline_requests.append(request)
            print(f"인덱스 {index}: {row['code_name']} 인라인 요청 생성 완료")
        
        print(f"총 {len(inline_requests)}개의 인라인 요청 생성 완료")
        return inline_requests
        
    except Exception as e:
        print(f"인라인 요청 생성 중 오류: {e}")
        return []


def create_inline_batch_job(inline_requests):
    """
    인라인 요청을 사용하여 배치 작업 생성 (올바른 방식)
    """
    try:
        # BatchJobSource를 사용하여 inlined_requests 설정
        batch_source = types.BatchJobSource(
            inlined_requests=inline_requests
        )
        
        # 배치 작업 생성
        inline_batch_job = client.batches.create(
            model="models/gemini-2.5-pro",
            src=batch_source,  # BatchJobSource 객체 전달
            config=types.CreateBatchJobConfig(
                display_name="inline-trend-companies-batch-job"
            )
        )
        
        print(f"인라인 배치 작업 생성 완료:")
        print(f"- 작업 ID: {inline_batch_job.name}")
        print(f"- 상태: {inline_batch_job.state}")
        print(f"- 모델: {inline_batch_job.model}")
        print(f"- 생성 시간: {inline_batch_job.create_time}")
        print(f"- 표시 이름: {inline_batch_job.display_name}")
        
        return inline_batch_job
        
    except Exception as e:
        print(f"인라인 배치 작업 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def monitor_batch_job(batch_job_name):
    """
    배치 작업 상태를 모니터링
    """
    try:
        job = client.batches.get(name=batch_job_name)
        
        print(f"\n=== 배치 작업 상태 ===")
        print(f"작업 ID: {job.name}")
        print(f"상태: {job.state}")
        print(f"생성 시간: {job.create_time}")
        
        if hasattr(job, 'start_time') and job.start_time:
            print(f"시작 시간: {job.start_time}")
            
        if hasattr(job, 'end_time') and job.end_time:
            print(f"완료 시간: {job.end_time}")
            
        if hasattr(job, 'error') and job.error:
            print(f"오류: {job.error}")
            
        return job
        
    except Exception as e:
        print(f"배치 작업 상태 확인 중 오류: {e}")
        return None


def wait_for_completion(batch_job_name, max_wait_time=300):
    """
    배치 작업 완료까지 대기 (최대 대기 시간: 300초)
    """
    import time
    
    completed_states = {
        'JOB_STATE_SUCCEEDED',
        'JOB_STATE_FAILED', 
        'JOB_STATE_CANCELLED',
        'JOB_STATE_PAUSED'
    }
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        job = client.batches.get(name=batch_job_name)
        print(f"현재 상태: {job.state}")
        
        if job.state in completed_states:
            print(f"배치 작업 완료! 최종 상태: {job.state}")
            return job
            
        print("30초 후 다시 확인합니다...")
        time.sleep(30)
    
    print(f"최대 대기 시간({max_wait_time}초)을 초과했습니다.")
    return None


def get_batch_results(batch_job_name):
    """
    완료된 배치 작업의 결과 가져오기
    """
    try:
        job = client.batches.get(name=batch_job_name)
        
        if job.state == "JOB_STATE_SUCCEEDED":
            print(f"\n=== 배치 작업 결과 ===")
            
            # 결과 데이터 구조 확인
            print(f"작업 정보:")
            print(f"- 작업 ID: {job.name}")
            print(f"- 상태: {job.state}")
            print(f"- 완료 시간: {job.end_time}")
            
            # 작업 결과를 JSON 파일로 저장
            results = {
                "job_name": job.name,
                "state": job.state,
                "create_time": str(job.create_time),
                "start_time": str(job.start_time) if hasattr(job, 'start_time') else None,
                "end_time": str(job.end_time) if hasattr(job, 'end_time') else None,
                "model": job.model,
                "display_name": job.display_name
            }
            
            # 추가 결과 데이터가 있다면 포함
            if hasattr(job, 'dest'):
                results["destination"] = str(job.dest)
            
            with open('batch_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4, default=str)
            
            print("결과가 'batch_results.json'에 저장되었습니다.")
            
            # 실제 응답 데이터는 별도 방법으로 다운로드해야 할 수 있음
            print("\n실제 응답 데이터를 확인하려면 Google Cloud Console 또는")
            print("지정된 출력 위치를 확인해주세요.")
            
            return results
            
        else:
            print(f"배치 작업이 아직 완료되지 않았습니다. 현재 상태: {job.state}")
            return None
            
    except Exception as e:
        print(f"배치 결과 가져오기 중 오류: {e}")
        return None


def list_batch_jobs():
    """
    모든 배치 작업 목록 조회
    """
    try:
        print("\n=== 배치 작업 목록 ===")
        for job in client.batches.list(
            config=types.ListBatchJobsConfig(page_size=10)
        ):
            print(f"- {job.name}: {job.state} ({job.display_name})")
            
    except Exception as e:
        print(f"배치 작업 목록 조회 중 오류: {e}")


if __name__ == "__main__":
    try:
        # 완전한 배치 처리 워크플로우 실행
        batch_job = complete_batch_workflow(
            excel_file="item_info_trend.xlsx", 
            max_rows=2  # 처리할 행 수 조정 가능
        )
        
        if batch_job:
            print(f"\n=== 다음 단계 ===")
            print(f"1. 배치 작업 상태 확인:")
            print(f"   monitor_batch_job('{batch_job.name}')")
            print(f"2. 완료 대기:")
            print(f"   wait_for_completion('{batch_job.name}')")
            print(f"3. 결과 확인:")
            print(f"   get_batch_results('{batch_job.name}')")
            print(f"4. 모든 배치 작업 목록:")
            print(f"   list_batch_jobs()")
        else:
            print("배치 처리 워크플로우가 실패했습니다.")
            
    except Exception as e:
        print(f"메인 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
    
    


    