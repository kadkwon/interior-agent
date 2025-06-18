"""
ADK Runner 직접 테스트
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(__file__))

def test_runner_direct():
    """ADK Runner 직접 테스트"""
    print("=== ADK Runner 직접 테스트 ===")
    
    try:
        # 필요한 라이브러리 임포트
        from interior_multi_agent.interior_agents import root_agent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        
        print(f"✅ 임포트 성공")
        print(f"📝 에이전트: {root_agent.name}")
        print(f"📝 에이전트 타입: {type(root_agent)}")
        
        # Session Service 생성
        session_service = InMemorySessionService()
        print(f"✅ Session Service 생성 성공: {type(session_service)}")
        
        # Runner 생성 (ADK v1.0.0 방식)
        runner = Runner(
            agent=root_agent,
            app_name="interior_chatbot",
            session_service=session_service
        )
        print(f"✅ Runner 생성 성공: {type(runner)}")
        
        # 테스트 메시지 실행
        test_message = "안녕하세요"
        print(f"📤 메시지 전송: {test_message}")
        
        result = runner.run(test_message)
        print(f"📥 결과 타입: {type(result)}")
        print(f"📥 결과 속성: {[attr for attr in dir(result) if not attr.startswith('_')]}")
        
        # 결과 내용 추출
        if hasattr(result, 'content'):
            print(f"📝 content: {result.content[:200]}...")
        if hasattr(result, 'message'):
            print(f"📝 message: {result.message[:200]}...")
        if hasattr(result, 'text'):
            print(f"📝 text: {result.text[:200]}...")
        
        print(f"📝 전체 결과: {str(result)[:200]}...")
        
        return True, result
        
    except Exception as e:
        print(f"❌ 에러: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    print("🚀 ADK Runner 직접 테스트 시작\n")
    success, result = test_runner_direct()
    print(f"\n🏁 테스트 완료 - 성공: {success}") 