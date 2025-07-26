import asyncio
import aiohttp
from aiohttp import ClientError, ClientTimeout, ClientConnectorError, ClientSSLError

async def check_url_detailed(session, url, source_info):
    url = url.strip()
    if not url or not url.startswith('http'):
        return url, "Invalid Format", source_info

    if url.lower().endswith('.pdf'):
        return None, "Valid", source_info

    try:
        async with session.get(url, timeout=ClientTimeout(total=15)) as response:
            if response.status in [200, 301, 302, 303, 307, 308]:
                return None, "Valid", source_info
            else:
                return url, f"Status Code {response.status}", source_info
                
    except ClientConnectorError as e:
        error_msg = str(e)
        if "Cannot connect to host" in error_msg:
            if "Name or service not known" in error_msg:
                return url, "DNS Resolution Failed", source_info
            else:
                return url, "Connection Refused", source_info
        elif "timeout" in error_msg.lower():
            return url, "Connection Timeout", source_info
        else:
            return url, "Connection Error", source_info
            
    except ClientSSLError as e:
        return url, "SSL Certificate Error", source_info
        
    except ClientError as e:
        # 기타 ClientError들
        return url, f"Client Error: {type(e).__name__}", source_info
        
    except asyncio.TimeoutError:
        return url, "Request Timeout", source_info
        
    except Exception as e:
        return url, f"Unexpected Error: {type(e).__name__}", source_info
    
async def main():
    async with aiohttp.ClientSession() as session:
        result = await check_url_detailed(session, "https://eiec.kdi.re.kr/policy/callDownload.do?num=253316&filenum=1&dtime=20240626185444", "Test Source")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())