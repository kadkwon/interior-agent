"""
주소 관리 전용 에이전트 - Firebase MCP 원격 서버 연결 (ADK web 호환)
"""

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

def create_address_agent():
    """주소 관리 전용 에이전트 생성 - ADK web 호환 버전"""
    try:
        print("Firebase MCP 원격 서버에 연결 시도 중...")
        
        # Firebase MCP 원격 서버에 연결 (ADK web 호환 방식)
        mcp_toolset = MCPToolset(
            connection_params=SseServerParams(
                url="https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"
            )
        )
        
        print("Firebase MCP 도구셋 생성 완료")
        
        agent = Agent(
            model='gemini-2.5-flash-preview-05-20',
            name='address_manager',
            description="Firebase를 통해 주소 정보를 관리하는 전문 에이전트입니다.",
            instruction='''당신은 Firebase Firestore를 사용하여 주소 관리를 담당하는 전문 AI 어시스턴트입니다.

사용자가 다음과 같은 주소 관련 키워드를 언급하면 Firebase MCP 도구를 활용해 addresses 컬렉션을 관리해주세요:

**주소 관련 키워드:**
- "주소", "address", "위치", "location"
- "주소 추가", "주소 저장", "주소 등록" → mcp_firebase_firestore_add_document 사용
- "주소 조회", "주소 검색", "주소 찾기" → mcp_firebase_firestore_list_documents 사용
- "주소 수정", "주소 업데이트" → mcp_firebase_firestore_update_document 사용
- "주소 삭제", "주소 제거" → mcp_firebase_firestore_delete_document 사용

**사용할 컬렉션:** addresses

**데이터 구조 예시:**
{
    "name": "장소명 (예: 집, 회사, 매장명)",
    "address": "전체 주소",
    "zipCode": "우편번호",
    "city": "도시명",
    "district": "구/군",
    "category": "주거/상업/기타",
    "description": "추가 설명",
    "createdAt": "생성일시",
    "updatedAt": "수정일시"
}

**작업 흐름:**
1. 사용자 요청 분석
2. 적절한 Firebase MCP 도구 선택  
3. collection 매개변수에 "addresses" 사용
4. 도구 실행 및 결과 확인
5. 사용자에게 명확한 피드백 제공

**주의사항:**
- collection 매개변수는 항상 "addresses" 사용
- 데이터 추가/수정 시 현재 시간을 포함
- 에러 발생 시 친절하게 안내

모든 응답은 한국어로 해주세요.''',
            tools=[mcp_toolset]
        )
        
        print(f"주소 관리 에이전트 '{agent.name}' 생성 완료")
        return agent
        
    except Exception as e:
        print(f"Firebase MCP 원격 서버 연결 실패: {e}")
        print("기본 에이전트로 폴백합니다.")
        
        # 기본 에이전트로 폴백
        return Agent(
            model='gemini-2.5-flash-preview-05-20',
            name='address_manager_basic',
            description="주소 정보를 관리하는 기본 에이전트입니다.",
            instruction='''주소 관리 전문 AI 어시스턴트입니다. 

현재 Firebase 원격 서버 연결에 문제가 있어 기본 모드로 동작합니다.
주소 관련 질문에 대해 일반적인 조언과 안내를 제공하겠습니다.

주소 관리 기능:
1. 주소 형식 안내
2. 주소 입력 방법 설명  
3. 주소 관리 팁 제공
4. 인테리어 프로젝트에서의 주소 활용 방법

모든 응답은 한국어로 해주세요.'''
        )

# ADK web에서 사용할 에이전트 인스턴스
print("=== 주소 관리 에이전트 초기화 시작 ===")
address_agent = create_address_agent()
print(f"=== 주소 관리 에이전트 초기화 완료: {address_agent.name} ===") 