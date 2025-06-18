"""
ADK 루트 에이전트 테스트 스크립트
"""
import sys
import os
import requests
import json

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(__file__))

def test_adk_import():
    """ADK 루트 에이전트 임포트 테스트"""
    print("=== ADK 루트 에이전트 임포트 테스트 ===")
    try:
        from interior_multi_agent.interior_agents import root_agent
        print(f"✅ ADK 루트 에이전트 임포트 성공: {root_agent.name}")
        print(f"📝 에이전트 설명: {root_agent.description}")
        return True
    except ImportError as e:
        print(f"❌ ADK 루트 에이전트 임포트 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 기타 오류: {e}")
        return False

def test_adk_direct_execution():
    """ADK 루트 에이전트 직접 실행 테스트"""
    print("\n=== ADK 루트 에이전트 직접 실행 테스트 ===")
    try:
        from interior_multi_agent.interior_agents import root_agent
        
        test_message = "안녕하세요"
        print(f"📤 테스트 메시지 전송: {test_message}")
        
        response = root_agent.run(test_message)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        print(f"📥 ADK 에이전트 응답: {response_text[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ ADK 에이전트 직접 실행 실패: {e}")
        return False

def test_adk_via_fastapi():
    """FastAPI를 통한 ADK 에이전트 테스트"""
    print("\n=== FastAPI를 통한 ADK 에이전트 테스트 ===")
    url = "http://localhost:8505/chat"
    
    test_messages = [
        "안녕하세요",
        "주소를 저장하고 싶어요",
        "인테리어 디자인 추천해주세요"
    ]
    
    for i, message in enumerate(test_messages, 1):
        try:
            print(f"\n[테스트 {i}] 메시지: {message}")
            
            response = requests.post(
                url,
                json={"message": message, "session_id": f"test-{i}"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 응답 상태: {data.get('agent_status', 'unknown')}")
                print(f"📝 응답 내용: {data.get('response', '')[:150]}...")
                print(f"🔧 사용된 도구: {data.get('firebase_tools_used', [])}")
            else:
                print(f"❌ HTTP 오류: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 요청 실패: {e}")

if __name__ == "__main__":
    print("🚀 ADK 루트 에이전트 종합 테스트 시작\n")
    
    # 1. 임포트 테스트
    import_success = test_adk_import()
    
    # 2. 직접 실행 테스트 (임포트 성공시만)
    if import_success:
        test_adk_direct_execution()
    
    # 3. FastAPI 통합 테스트
    test_adk_via_fastapi()
    
    print("\n🏁 테스트 완료") 