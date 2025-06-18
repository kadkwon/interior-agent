import requests
import json

def test_chat_endpoint():
    """채팅 엔드포인트 테스트"""
    url = "http://localhost:8505/chat"
    
    test_message = {
        "message": "안녕하세요",
        "session_id": "test-session"
    }
    
    try:
        response = requests.post(
            url, 
            json=test_message,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"오류: {e}")

def test_health_endpoint():
    """건강 체크 엔드포인트 테스트"""
    url = "http://localhost:8505/health"
    
    try:
        response = requests.get(url)
        print(f"Health 체크 상태 코드: {response.status_code}")
        print(f"Health 응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"Health 체크 오류: {e}")

if __name__ == "__main__":
    print("=== FastAPI 서버 테스트 ===")
    test_health_endpoint()
    print("\n=== 채팅 엔드포인트 테스트 ===")
    test_chat_endpoint() 