"""
🧪 ADK 표준 인테리어 에이전트 테스트 스크립트

🎯 테스트 목적:
- ADK 표준 구조 검증
- 하위 에이전트 라우팅 테스트
- 세션 관리 검증
- MCP 클라이언트 연결 테스트

📋 테스트 항목:
1. 에이전트 초기화
2. Firebase 에이전트 라우팅
3. Email 에이전트 라우팅
4. 세션 일관성 검증
5. 오류 처리 검증
"""

import asyncio
from . import root_agent, runner, session_service, print_adk_info

async def test_adk_structure():
    """ADK 표준 구조 검증 테스트"""
    print("🧪 ADK 표준 구조 검증 테스트 시작")
    
    # 1. 에이전트 구조 검증
    print("\n1️⃣ 에이전트 구조 검증:")
    print(f"✅ 메인 에이전트: {root_agent.name}")
    print(f"✅ 하위 에이전트 수: {len(root_agent.sub_agents)}")
    for i, sub_agent in enumerate(root_agent.sub_agents):
        print(f"   {i+1}. {sub_agent.name}")
    
    # 2. 세션 서비스 검증
    print("\n2️⃣ 세션 서비스 검증:")
    print(f"✅ 세션 서비스 타입: {type(session_service).__name__}")
    print(f"✅ Runner 설정: {type(runner).__name__}")
    
    # 3. 테스트 세션 생성
    print("\n3️⃣ 테스트 세션 생성:")
    session = session_service.create_session()
    print(f"✅ 세션 생성 완료: {session.id}")
    
    return session

async def test_firebase_routing(session):
    """Firebase 에이전트 라우팅 테스트"""
    print("\n4️⃣ Firebase 에이전트 라우팅 테스트:")
    
    test_messages = [
        "contractors 조회해줘",
        "견적서 목록 보여줘", 
        "주소 리스트 가져와"
    ]
    
    for message in test_messages:
        print(f"\n📤 테스트 메시지: '{message}'")
        try:
            # 실제 ADK Runner 사용
            response = await runner.run_session(session.id, message)
            print(f"📥 응답 (일부): {str(response)[:100]}...")
        except Exception as e:
            print(f"❌ 오류: {e}")

async def test_email_routing(session):
    """Email 에이전트 라우팅 테스트"""
    print("\n5️⃣ Email 에이전트 라우팅 테스트:")
    
    test_messages = [
        "이메일 서버 테스트",
        "서버 정보 확인",
        "이메일 연결 상태 확인"
    ]
    
    for message in test_messages:
        print(f"\n📤 테스트 메시지: '{message}'")
        try:
            response = await runner.run_session(session.id, message)
            print(f"📥 응답 (일부): {str(response)[:100]}...")
        except Exception as e:
            print(f"❌ 오류: {e}")

async def test_session_consistency():
    """세션 일관성 테스트"""
    print("\n6️⃣ 세션 일관성 테스트:")
    
    # 두 개의 다른 세션 생성
    session1 = session_service.create_session()
    session2 = session_service.create_session()
    
    print(f"✅ 세션 1: {session1.id}")
    print(f"✅ 세션 2: {session2.id}")
    
    # 각 세션에서 다른 요청 실행
    print("\n📤 세션 1에서 Firebase 요청...")
    try:
        response1 = await runner.run_session(session1.id, "contractors 조회")
        print(f"📥 세션 1 응답: 정상")
    except Exception as e:
        print(f"❌ 세션 1 오류: {e}")
    
    print("\n📤 세션 2에서 Email 요청...")
    try:
        response2 = await runner.run_session(session2.id, "이메일 서버 테스트")
        print(f"📥 세션 2 응답: 정상")
    except Exception as e:
        print(f"❌ 세션 2 오류: {e}")

async def main():
    """메인 테스트 실행"""
    print("🚀 ADK 표준 인테리어 에이전트 테스트 시작!")
    
    # ADK 정보 출력
    print_adk_info()
    
    try:
        # 구조 검증
        session = await test_adk_structure()
        
        # 라우팅 테스트
        await test_firebase_routing(session)
        await test_email_routing(session)
        
        # 세션 일관성 테스트
        await test_session_consistency()
        
        print("\n🎉 모든 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 