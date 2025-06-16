"""
인테리어 프로젝트 관리 에이전트
- Firebase MCP 서버를 사용한 관리 시스템
"""

import os
import logging
import asyncio
from typing import Optional
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_agent():
    """MCP 서버에서 도구를 가져와서 에이전트를 생성합니다."""
    try:
        # MCP 도구 초기화
        tools, exit_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "firebase-tools",
                    "experimental:mcp",
                    "--dir",
                    "."
                ]
            )
        )
        
        # 에이전트 생성
        agent = Agent(
            name='interior_agent',
            model='gemini-2.0-pro',
            instruction='인테리어 프로젝트 관리를 위한 AI 에이전트입니다.',
            tools=tools
        )
        
        return agent, exit_stack
    except Exception as e:
        logger.error(f"❌ Firebase MCP 에이전트 초기화 실패: {e}")
        raise

def init_agent():
    """에이전트 초기화"""
    try:
        # 세션 서비스 초기화
        session_service = InMemorySessionService()
        
        # 에이전트 생성
        agent, exit_stack = asyncio.run(create_agent())
        
        # 러너 생성
        runner = Runner(
            app_name='interior_agent',
            agent=agent,
            session_service=session_service
        )
        
        logger.info("✅ Firebase MCP 에이전트가 성공적으로 초기화되었습니다.")
        return runner
        
    except Exception as e:
        logger.error(f"❌ 에이전트를 사용할 수 없습니다.")
        raise

# 에이전트 초기화
root_runner = init_agent() 