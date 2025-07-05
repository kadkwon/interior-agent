import requests
import json
import time

def test_web_chatbot_connection():
    """웹 챗봇 연결 테스트 (InteriorAgent.js와 동일한 방식)"""
    
    print("🌐 InteriorAgent.js 웹 챗봇 연결 테스트")
    print("=" * 60)
    
    # 웹 챗봇에서 사용하는 것과 동일한 API 엔드포인트
    API_BASE_URL = "http://localhost:8506"
    STATUS_ENDPOINT = f"{API_BASE_URL}/status"
    CHAT_ENDPOINT = f"{API_BASE_URL}/chat"
    
    # 1. 서버 상태 확인 (InteriorAgent.js의 checkServerHealth와 동일)
    print("1️⃣ 서버 상태 확인...")
    try:
        response = requests.get(STATUS_ENDPOINT, timeout=5)
        
        if response.ok:
            data = response.json()
            print(f"✅ 서버 응답: {data}")
            
            # ADK 모드 확인
            is_connected = data.get('mode') == 'ADK_Standard'
            print(f"🔍 ADK 모드 확인: {data.get('mode')} ({'✅ 연결됨' if is_connected else '❌ 연결 안됨'})")
            
            if not is_connected:
                print("❌ 서버가 ADK 표준 모드가 아닙니다.")
                return
                
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return
    
    # 2. 웹 챗봇 스타일 채팅 테스트
    print("\n2️⃣ 웹 챗봇 스타일 채팅 테스트...")
    
    # 웹 챗봇에서 사용하는 세션 ID 형태
    session_id = f"react-session-{int(time.time())}-web-test"
    print(f"🔑 세션 ID: {session_id}")
    
    test_messages = [
        "안녕하세요! 인테리어 에이전트님",
        "contractors 조회해주세요",
        "estimateVersionsV3 목록을 보여주세요",
        "gncloud86@naver.com으로 이메일 테스트 해주세요"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 테스트 {i}: {message}")
        
        try:
            # InteriorAgent.js와 동일한 요청 형태
            data = {
                "message": message,
                "session_id": session_id
            }
            
            response = requests.post(
                CHAT_ENDPOINT,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            result = response.json()
            print(f"✅ 응답 받음 ({response.status_code})")
            print(f"📄 응답: {result.get('response', 'No response')[:200]}...")
            
            # 응답에서 추가 정보 확인
            if 'agent_status' in result:
                print(f"🤖 에이전트 상태: {result['agent_status']}")
            
            if 'firebase_tools_used' in result and result['firebase_tools_used']:
                print(f"🔧 사용된 도구: {result['firebase_tools_used']}")
            
            time.sleep(1)  # 서버 부하 방지
            
        except Exception as e:
            print(f"❌ 채팅 테스트 {i} 실패: {e}")
    
    print("\n🎉 웹 챗봇 연결 테스트 완료!")

if __name__ == "__main__":
    test_web_chatbot_connection() 