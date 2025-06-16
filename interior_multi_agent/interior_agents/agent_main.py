"""
인테리어 프로젝트 관리 에이전트
- Firebase MCP 서버를 사용한 관리 시스템
"""

import os
import logging
import asyncio
from typing import Optional
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 서비스 계정 키 파일 경로
SERVICE_ACCOUNT_KEY_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'interior-one-click-firebase-adminsdk-mpr08-94f76b4e50.json')

async def create_agent():
    """MCP 서버에서 도구를 가져와서 에이전트를 생성합니다."""
    try:
        # MCP 도구 초기화
        server_params = {
            'command': 'npx',
            'args': ['-y', '@gannonh/firebase-mcp'],
            'env': {
                'SERVICE_ACCOUNT_KEY_PATH': SERVICE_ACCOUNT_KEY_PATH,
                'FIREBASE_STORAGE_BUCKET': 'interior-one-click.appspot.com',
                'MCP_TRANSPORT': 'http',
                'MCP_HTTP_PORT': '8080',
                'MCP_SERVER_URL': 'https://firebase-mcp-638331849453.asia-northeast3.run.app'
            }
        }
        
        toolset = MCPToolset(connection_params=StdioConnectionParams(server_params=server_params))
        
        # 에이전트 생성
        agent = Agent(
            name='interior_agent',
            model='gemini-2.0-pro',
            instruction='인테리어 프로젝트 관리를 위한 AI 에이전트입니다.',
            tools=toolset.tools
        )
        
        return agent
    except Exception as e:
        logger.error(f"❌ Firebase MCP 에이전트 초기화 실패: {e}")
        return None

def init_agent():
    """에이전트 초기화"""
    try:
        # 세션 서비스 초기화
        session_service = InMemorySessionService()
        
        # 에이전트 생성 (동기적으로 실행)
        agent = None
        try:
            loop = asyncio.new_event_loop()
            agent = loop.run_until_complete(create_agent())
            loop.close()
        except RuntimeError:
            # 이미 이벤트 루프가 실행 중인 경우
            loop = asyncio.get_event_loop()
            agent = loop.run_until_complete(create_agent())
            
        if agent is None:
            logger.error("❌ 에이전트 생성 실패")
            return None
            
        # 러너 생성
        runner = Runner(
            app_name='interior_agent',
            agent=agent,
            session_service=session_service
        )
        
        logger.info("✅ Firebase MCP 에이전트가 성공적으로 초기화되었습니다.")
        return runner
        
    except Exception as e:
        logger.error(f"❌ 에이전트를 사용할 수 없습니다: {e}")
        return None

# 에이전트 초기화
root_runner = init_agent() 