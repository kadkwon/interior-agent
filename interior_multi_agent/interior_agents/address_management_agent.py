"""
🏠 주소 관리 에이전트 - ADK 공식 간단 방식
"""

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

# Firebase MCP 도구셋 연결 (단 3줄!)
firebase_toolset = MCPToolset(
    connection_params=SseServerParams(
        url="https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"
    )
)

# 주소 관리 에이전트 (단 5줄!)
address_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp-1219',
    name='address_manager',
    instruction='주소 관리 전문 에이전트입니다. Firebase의 addressesJson 컬렉션을 사용해서 주소를 검색, 추가, 수정, 삭제할 수 있습니다.',
    tools=[firebase_toolset]
) 