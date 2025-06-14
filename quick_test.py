import requests
import json

def test_server():
    try:
        # Health check
        print("Health check 테스트...")
        health_response = requests.get("http://localhost:8505/health", timeout=5)
        print(f"Health status: {health_response.status_code}")
        print(f"Health response: {health_response.json()}")
        
        # Chat test
        print("\nChat 테스트...")
        chat_data = {"message": "주소 리스트보여줘"}
        chat_response = requests.post(
            "http://localhost:8505/agent/chat", 
            json=chat_data, 
            timeout=30
        )
        print(f"Chat status: {chat_response.status_code}")
        print(f"Chat response: {chat_response.text}")
        
    except Exception as e:
        print(f"테스트 오류: {e}")

if __name__ == "__main__":
    test_server() 