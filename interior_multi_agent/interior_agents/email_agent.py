"""
📧 이메일 관리 에이전트 - ADK 공식 간단 방식
"""

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

# Email MCP 도구셋 연결 (단 3줄!)
email_toolset = MCPToolset(
    connection_params=SseServerParams(
        url="https://estimate-email-mcp-638331849453.asia-northeast3.run.app/mcp"
    )
)

# 이메일 관리 에이전트 (단 5줄!)
email_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp-1219',
    name='email_manager',
    instruction='견적서 이메일 전송 전문 에이전트입니다. 이메일 전송, 서버 상태 확인 등을 담당합니다.',
    tools=[email_toolset]
) 