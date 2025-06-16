import requests
import json

# MCP 서버 URL
MCP_URL = "http://localhost:8080/mcp"

try:
    # 세션 생성
    session_response = requests.post(f"{MCP_URL}/session")
    session_response.raise_for_status()
    session_id = session_response.json()["sessionId"]
    
    # 스케줄 컬렉션 조회 요청
    payload = {
        "name": "firestore_query",
        "arguments": {
            "collection": "schedules"
        }
    }
    
    response = requests.post(f"{MCP_URL}?sessionId={session_id}", json=payload)
    response.raise_for_status()
    
    data = response.json()
    print("=== 스케줄 목록 ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
except requests.exceptions.RequestException as e:
    print(f"오류 발생: {e}") 