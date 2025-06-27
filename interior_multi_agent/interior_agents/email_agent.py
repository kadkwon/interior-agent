"""
📧 이메일 관리 하위 에이전트 - ADK 미니멀 방식
"""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .mcp_client import email_client

async def send_estimate_email(email: str, address: str, process_data: list):
    """견적서 이메일 전송"""
    return await email_client.call_tool("send_estimate_email", {
        "email": email,
        "address": address,
        "process_data": process_data
    })

async def test_email_connection():
    """이메일 서버 연결 테스트"""
    return await email_client.call_tool("test_connection", {
        "random_string": "test"
    })

async def get_email_server_info():
    """이메일 서버 정보 조회"""
    return await email_client.call_tool("get_server_info", {
        "random_string": "info"
    })

# 이메일 관리 하위 에이전트
email_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='email_manager',
    instruction='견적서 이메일 전송 전문 에이전트. 이메일 전송, 서버 상태 확인을 담당합니다.',
    tools=[
        FunctionTool(send_estimate_email),
        FunctionTool(test_email_connection),
        FunctionTool(get_email_server_info)
    ]
) 