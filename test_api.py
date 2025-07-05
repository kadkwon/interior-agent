import requests
import json

# 서버 상태 확인
print("🔍 서버 상태 확인...")
try:
    response = requests.get("http://localhost:8506/status")
    print(f"✅ 서버 상태: {response.json()}")
except Exception as e:
    print(f"❌ 서버 상태 확인 실패: {e}")
    exit(1)

# Firebase 에이전트 테스트
print("\n🔥 Firebase 에이전트 테스트...")
try:
    data = {
        "message": "contractors 조회해줘",
        "session_id": "test_session"
    }
    
    response = requests.post(
        "http://localhost:8506/chat",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    result = response.json()
    print(f"✅ Firebase 응답: {result['response'][:200]}...")
    
except Exception as e:
    print(f"❌ Firebase 테스트 실패: {e}")

# Email 에이전트 테스트 (더 명확한 키워드 사용)
print("\n📧 Email 에이전트 테스트...")
try:
    data = {
        "message": "이메일 전송 테스트해줘",  # 더 명확한 키워드
        "session_id": "test_session"
    }
    
    response = requests.post(
        "http://localhost:8506/chat",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    result = response.json()
    print(f"✅ Email 응답: {result['response'][:200]}...")
    
except Exception as e:
    print(f"❌ Email 테스트 실패: {e}")

print("\n🎉 테스트 완료!") 