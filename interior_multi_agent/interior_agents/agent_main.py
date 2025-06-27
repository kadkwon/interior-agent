"""
🏠 인테리어 멀티 에이전트 메인 - ADK 공식 간단 방식

간단한 ADK 에이전트 시스템으로 주소 관리와 이메일 전송을 담당합니다.
"""

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
from .address_management_agent import address_agent
from .email_agent import email_agent

# 메인 인테리어 에이전트 (모든 MCP 도구 포함)
interior_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp-1219',
    name='interior_multi_agent',
    instruction='''
당신은 인테리어 프로젝트 관리를 담당하는 AI 어시스턴트입니다.

## 🏠 주요 기능:
1. **주소 관리**: Firebase의 addressesJson 컬렉션을 사용하여 주소 검색, 추가, 수정, 삭제
2. **이메일 관리**: 견적서 이메일 전송 및 관리

## 📋 사용 가능한 도구:
- Firebase MCP 도구들 (주소 관리용)
- Email MCP 도구들 (이메일 전송용)

사용자의 요청에 따라 적절한 도구를 선택해서 작업을 수행하세요.
    ''',
    tools=[
        # Firebase MCP 도구셋
        MCPToolset(
            connection_params=SseServerParams(
                url="https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"
            )
        ),
        # Email MCP 도구셋  
        MCPToolset(
            connection_params=SseServerParams(
                url="https://estimate-email-mcp-638331849453.asia-northeast3.run.app/mcp"
            )
        )
    ]
)

print(f"✅ 인테리어 멀티 에이전트 시스템 초기화 완료: {interior_agent.name}")
print(f"📦 등록된 도구 수: {len(interior_agent.tools) if hasattr(interior_agent, 'tools') else 'N/A'}")