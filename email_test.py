import requests
import json

def test_email_send():
    """이메일 전송 테스트"""
    
    # 서버 상태 확인
    print("🔍 서버 상태 확인...")
    try:
        response = requests.get("http://localhost:8506/status")
        print(f"✅ 서버 상태: {response.json()}")
    except Exception as e:
        print(f"❌ 서버 상태 확인 실패: {e}")
        return
    
    # 이메일 전송 테스트 - 더 명확한 키워드 사용
    print("\n📧 이메일 전송 테스트 시작...")
    
    test_scenarios = [
        {
            "name": "이메일 전송 요청 (명확한 키워드)",
            "message": "gncloud86@naver.com 주소로 테스트 견적서 이메일을 보내줘",
            "expected": "email_agent"
        },
        {
            "name": "이메일 서버 연결 테스트",
            "message": "이메일 서버 연결 테스트를 실행해줘",
            "expected": "email_agent"
        },
        {
            "name": "이메일 서버 정보 조회",
            "message": "이메일 서버 정보를 조회해줘",
            "expected": "email_agent"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*60}")
        print(f"🧪 {scenario['name']}")
        print(f"📝 요청: {scenario['message']}")
        
        try:
            data = {
                "message": scenario['message'],
                "session_id": "email_test_session"
            }
            
            response = requests.post(
                "http://localhost:8506/chat",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            result = response.json()
            print(f"✅ 응답 받음")
            print(f"📄 응답 내용: {result['response']}")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_email_send() 