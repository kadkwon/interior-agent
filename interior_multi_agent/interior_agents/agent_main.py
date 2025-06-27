"""
🏠 인테리어 멀티 에이전트 루트 - 라우팅 시스템
"""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .address_management_agent import address_agent
from .email_agent import email_agent

async def handle_address_request(user_query: str):
    """주소 관련 요청을 주소 에이전트로 라우팅"""
    response = await address_agent.send_message(user_query)
    return {"agent": "address_manager", "response": response.text}

async def handle_email_request(user_query: str):
    """이메일 관련 요청을 이메일 에이전트로 라우팅"""
    response = await email_agent.send_message(user_query)
    return {"agent": "email_manager", "response": response.text}

async def get_system_status():
    """시스템 상태 확인"""
    return {
        "status": "active",
        "agents": ["address_manager", "email_manager"],
        "description": "인테리어 멀티 에이전트 시스템이 정상 작동 중입니다."
    }

# 루트 에이전트 - 라우팅 담당
interior_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='interior_multi_agent',
    instruction='''
인테리어 프로젝트 관리 루트 에이전트입니다.

## 🎯 라우팅 규칙:
- 주소/address 관련: handle_address_request 사용
- 이메일/email 관련: handle_email_request 사용
- 시스템 상태: get_system_status 사용

사용자 요청을 분석해서 적절한 하위 에이전트로 라우팅하세요.
    ''',
    tools=[
        FunctionTool(handle_address_request),
        FunctionTool(handle_email_request),
        FunctionTool(get_system_status)
    ]
)

print(f"✅ 인테리어 멀티 에이전트 시스템 초기화 완료: {interior_agent.name}")
print(f"📦 등록된 라우팅 도구: {len(interior_agent.tools)}개")