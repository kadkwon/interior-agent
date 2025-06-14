import requests
import json

def test_health():
    """서버 상태 확인"""
    try:
        response = requests.get("http://localhost:8505/health")
        print(f"Health Check - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health Check 실패: {e}")
        return False

def test_chat(message):
    """채팅 테스트"""
    try:
        data = {"message": message}
        response = requests.post(
            "http://localhost:8505/agent/chat",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Chat Test - Status: {response.status_code}")
        result = response.json()
        print(f"Success: {result.get('success')}")
        if result.get('success'):
            print(f"Response: {result.get('response')}")
        else:
            print(f"Error: {result.get('error')}")
        return result.get('success', False)
    except Exception as e:
        print(f"Chat Test 실패: {e}")
        return False

if __name__ == "__main__":
    print("=== ADK API 서버 테스트 ===")
    
    # 1. 서버 상태 확인
    print("\n1. 서버 상태 확인:")
    health_ok = test_health()
    
    if health_ok:
        # 2. 채팅 테스트
        print("\n2. 채팅 테스트:")
        test_chat("주소 리스트 보여줘")
    else:
        print("서버가 실행되지 않았습니다.") 