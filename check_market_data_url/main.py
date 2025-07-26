import pandas as pd
import asyncio
import aiohttp
import json
from datetime import datetime
from aiohttp import ClientError, ClientTimeout, ClientConnectorError, ClientSSLError

async def check_url(session, url, source_info):
    """
    단일 URL의 유효성을 비동기적으로 확인합니다.
    """
    url = url.strip()
    if not url or not url.startswith('http'):
        print(f"Invalid Format | URL: {url} | Source: {source_info}")
        return url, "Invalid Format", source_info

    # PDF URL은 유효한 것으로 간주
    if url.lower().endswith('.pdf'):
        print(f"PDF (Valid) | URL: {url} | Source: {source_info}")
        return None, "Valid", source_info
    
    # Google Vertex AI Search URL은 유효한 것으로 간주
    if 'vertexaisearch.cloud.google.com' in url:
        print(f"Google Vertex AI (Valid) | URL: {url} | Source: {source_info}")
        return None, "Valid", source_info
    
    # 다운로드 URL 패턴 확인
    download_patterns = [
        'callDownload.do',
        'download.php', 
        'fileDownload',
        'getFile',
        '/download/',
        'attachment=',
        'fileDown.do'
    ]
    if any(pattern in url for pattern in download_patterns):
        print(f"Download URL (Valid) | URL: {url} | Source: {source_info}")
        return None, "Valid", source_info
    
    # 정부/공공기관 도메인 확인
    trusted_domains = [
        'kdi.re.kr',
        'go.kr',
        'or.kr', 
        'ac.kr',
        'kostat.go.kr',
        'bok.or.kr',
        'eiec.kdi.re.kr'  # KDI 경제정보센터
    ]
    if any(domain in url for domain in trusted_domains):
        print(f"Government/Public Domain (Valid) | URL: {url} | Source: {source_info}")
        return None, "Valid", source_info

    try:
        # 브라우저를 흉내낸 헤더 추가 (403 오류 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 15초 타임아웃 설정 (더 여유있게)
        async with session.get(url, headers=headers, timeout=ClientTimeout(total=15)) as response:
            if response.status in [200, 301, 302, 303, 307, 308]:  # 리다이렉트도 유효로 처리
                print(f"OK | URL: {url} | Source: {source_info} | Status: {response.status}")
                return None, "Valid", source_info
            else:
                # 403 오류에 대한 구체적인 메시지
                if response.status == 400:
                    print(f"Bad Request | URL: {url} | Source: {source_info} | Status: 400 (Bad Request)")
                    return url, "Bad Request (400)", source_info
                elif response.status == 401:
                    print(f"Unauthorized | URL: {url} | Source: {source_info} | Status: 401 (Unauthorized)")
                    return url, "Unauthorized (401)", source_info
                elif response.status == 402:
                    print(f"Payment Required | URL: {url} | Source: {source_info} | Status: 402 (Payment Required)")
                    return url, "Payment Required (402)", source_info
                if response.status == 403:
                    print(f"Access Forbidden | URL: {url} | Source: {source_info} | Status: 403 (Bot/Script blocked)")
                    return url, "Access Forbidden (403)", source_info
                elif response.status == 404:
                    print(f"Not Found | URL: {url} | Source: {source_info} | Status: 404 (Page not found)")
                    return url, "Page Not Found (404)", source_info
                elif response.status == 405:
                    print(f"Method Not Allowed | URL: {url} | Source: {source_info} | Status: {response.status} (Method Not Allowed)")
                    return url, f"Method Not Allowed ({response.status})", source_info
                elif response.status == 406:
                    print(f"Not Acceptable | URL: {url} | Source: {source_info} | Status: {response.status} (Not Acceptable)")
                    return url, f"Not Acceptable ({response.status})", source_info
                elif response.status == 407:
                    print(f"Proxy Authentication Required | URL: {url} | Source: {source_info} | Status: {response.status} (Proxy Authentication Required)")
                    return url, f"Proxy Authentication Required ({response.status})", source_info
                elif response.status >= 500:
                    print(f"Server Error | URL: {url} | Source: {source_info} | Status: {response.status} (Server problem)")
                    return url, f"Server Error ({response.status})", source_info
            
    except ClientConnectorError as e:
        error_msg = str(e)
        if "Cannot connect to host" in error_msg:
            if any(dns_error in error_msg for dns_error in [
                "Name or service not known",
                "nodename nor servname provided", 
                "No address associated with hostname"
            ]):
                print(f"DNS Failed | URL: {url} | Source: {source_info} | Error: Domain not found")
                return url, "DNS Resolution Failed", source_info
            else:
                print(f"Connection Refused | URL: {url} | Source: {source_info} | Error: Server refused connection")
                return url, "Connection Refused", source_info
        # elif "timeout" in error_msg.lower():
        #     print(f"Connection Timeout | URL: {url} | Source: {source_info} | Error: Connection timed out")
        #     return url, "Connection Timeout", source_info
        else:
            print(f"Connection Error | URL: {url} | Source: {source_info} | Error: {e.__class__.__name__}")
            return None, "Valid", source_info
    # except ClientSSLError as e:
    #     print(f"SSL Error | URL: {url} | Source: {source_info} | Error: SSL certificate problem")
    #     return url, "SSL Certificate Error", source_info
    # except ClientError as e:
    #     print(f"Client Error | URL: {url} | Source: {source_info} | Error: {e.__class__.__name__}")
    #     return url, f"Client Error: {type(e).__name__}", source_info
    # except asyncio.TimeoutError:
    #     print(f"Timeout Error | URL: {url} | Source: {source_info}")
    #     return url, "Timeout", source_info
    except Exception as e:
        # 기타 예상치 못한 예외 처리
        print(f"Unexpected Error | URL: {url} | Source: {source_info} | Error: {e.__class__.__name__}")
        return None, "Valid", source_info
    
    # 함수 끝 안전장치 (이론적으로는 도달하지 않아야 함)
    print(f"Warning: Reached end of check_url without return | URL: {url} | Source: {source_info}")
    return None, "Valid", source_info

async def main():
    """
    메인 비동기 실행 함수
    """
    excel_file_path = 'item_info_v0.xlsx'
    try:
        df = pd.read_excel(excel_file_path)
    except FileNotFoundError:
        print(f"오류: 파일 '{excel_file_path}'을(를) 찾을 수 없습니다.")
        return

    columns_to_check = [6, 10, 14, 18, 22, 26]
    url_dict = {}  # {(column_name, row_index): [url1, url2, ...]} 형태

    print("=== 지정된 열에서 URL 추출 시작 ===")
    for col_index in columns_to_check:
        if col_index < df.shape[1]:
            column_name = df.columns[col_index]  # 열 이름 가져오기
            print(f"- {col_index + 1}번째 열 '{column_name}'의 URL을 추출합니다.")
            
            # 각 행을 순회하며 URL 추출
            for row_index, value in df.iloc[:, col_index].items():
                if pd.notna(value):  # NaN이 아닌 경우만 처리
                    # 먼저 쉼표로 분리, 그 다음 공백으로 분리하여 URL 추출
                    raw_text = str(value)
                    urls = []
                    
                    # 쉼표와 공백 모두로 분리
                    for part in raw_text.replace(',', ' ').split():
                        part = part.strip()
                        if part and part != 'nan' and part.startswith('http'):
                            urls.append(part)
                    
                    if urls:  # URL이 있는 경우만 딕셔너리에 추가
                        key = (column_name, row_index)
                        url_dict[key] = urls
        else:
            print(f"경고: {col_index + 1}번째 열이 파일에 존재하지 않아 건너뜁니다.")
    
    if not url_dict:
        print("\n검사할 URL을 찾지 못했습니다.")
        return

    # 모든 URL과 소스 정보를 준비
    all_url_tasks = []
    for (column_name, row_index), urls in url_dict.items():
        for url in urls:
            source_info = f"{column_name}[{row_index}]"
            all_url_tasks.append((url, source_info))

    print(f"\n=== 총 {len(all_url_tasks)}개의 URL 유효성 검사 시작 ===")

    # 동시 연결 수를 더 보수적으로 제한하고 세마포어 사용
    max_concurrent = 20  # 동시 연결 수를 20개로 제한
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def check_url_with_semaphore(session, url, source_info):
        async with semaphore:
            # 각 요청 사이에 작은 지연 추가
            await asyncio.sleep(0.1)
            return await check_url(session, url, source_info)
    
    tasks = []
    # aiohttp.TCPConnector 설정 개선
    connector = aiohttp.TCPConnector(
        limit=30,  # 전체 연결 풀 크기
        limit_per_host=5,  # 호스트당 연결 수 제한
        ttl_dns_cache=300,  # DNS 캐시 TTL
        use_dns_cache=True,
        keepalive_timeout=30,  # Keep-alive 타임아웃
        enable_cleanup_closed=True
    )
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=20, connect=10)  # 전체 및 연결 타임아웃
    ) as session:
        for url, source_info in all_url_tasks:
            # 각 URL에 대한 비동기 작업을 생성 (세마포어 포함)
            task = asyncio.create_task(check_url_with_semaphore(session, url, source_info))
            tasks.append(task)
        
        # 모든 작업을 동시에 실행하고 결과를 기다림
        results = await asyncio.gather(*tasks)

        # 안전한 필터링: None이거나 결과가 없는 경우 유효한 데이터로 처리
        # 무효한 URL만 필터링 (첫 번째 요소가 None이 아닌 경우)
        invalid_urls_with_info = []
        valid_count = 0
        error_count = 0
        
        for res in results:
            # res가 None인 경우 (유효한 데이터로 처리)
            if res is None:
                valid_count += 1
                continue
            # res가 튜플이고 첫 번째 요소가 None이 아닌 경우 (무효한 URL)
            elif isinstance(res, tuple) and len(res) >= 3 and res[0] is not None:
                invalid_urls_with_info.append(res)
                error_count += 1
            # res가 튜플이고 첫 번째 요소가 None인 경우 (유효한 URL)
            elif isinstance(res, tuple) and len(res) >= 3 and res[0] is None:
                valid_count += 1
            # 그 외의 예상치 못한 경우
            else:
                print(f"Warning: Unexpected result format: {res}")
                valid_count += 1  # 안전하게 유효한 것으로 처리
        
        print(f"\n=== 처리 통계 ===")
        print(f"전체 검사 대상: {len(results)}개")
        print(f"유효한 URL: {valid_count}개")
        print(f"무효한 URL: {error_count}개")

    print("\n=== 검사 완료 ===")
    if invalid_urls_with_info:
        # 이유(reason)별로 그룹화
        sorted_invalid_urls = sorted(invalid_urls_with_info, key=lambda x: x[1])
        
        print(f"유효하지 않은 URL 목록 (총 {len(invalid_urls_with_info)}개):")
        
        current_reason = ""
        for url, reason, source_info in sorted_invalid_urls:
            if reason != current_reason:
                print(f"\n--- {reason} ---")
                current_reason = reason
            print(f"{url} | 출처: {source_info}")
    else:
        print("모든 URL이 유효합니다.")
        
    # 요약 정보 출력
    print(f"\n=== 요약 ===")
    print(f"검사한 열: {len(columns_to_check)}개")
    print(f"URL이 있는 셀: {len(url_dict)}개")
    print(f"총 검사한 URL: {len(all_url_tasks)}개")
    if invalid_urls_with_info:
        print(f"유효하지 않은 URL: {len(invalid_urls_with_info)}개")
        print(f"유효한 URL: {len(all_url_tasks) - len(invalid_urls_with_info)}개")

    # JSON 결과 저장 (실패한 URL만)
    result_data = {
        "검사_정보": {
            "검사_시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "엑셀_파일": excel_file_path,
            "검사한_열": [f"{i+1}번째 열" for i in columns_to_check if i < df.shape[1]],
            "검사한_열_이름": [df.columns[i] for i in columns_to_check if i < df.shape[1]]
        },
        "통계": {
            "검사한_열_개수": len(columns_to_check),
            "URL이_있는_셀_개수": len(url_dict),
            "총_검사한_URL_개수": len(all_url_tasks),
            "유효한_URL_개수": len(all_url_tasks) - len(invalid_urls_with_info),
            "유효하지_않은_URL_개수": len(invalid_urls_with_info)
        },
        "실패한_URL": {}
    }
    
    # 유효하지 않은 URL만 저장
    for url, reason, source_info in invalid_urls_with_info:
        if reason not in result_data["실패한_URL"]:
            result_data["실패한_URL"][reason] = []
        
        result_data["실패한_URL"][reason].append({
            "URL": url,
            "출처": source_info,
            "오류_유형": reason
        })
    
    # JSON 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"url_validation_result_{timestamp}.json"
    
    try:
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"\n=== JSON 결과 저장 완료 ===")
        print(f"파일명: {json_filename}")
                except Exception as e:
        print(f"\nJSON 저장 중 오류 발생: {e}")
                    
if __name__ == "__main__":
    # 비동기 이벤트 루프 실행
    asyncio.run(main())

