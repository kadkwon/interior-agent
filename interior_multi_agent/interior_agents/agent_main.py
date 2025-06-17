"""
인테리어 프로젝트 관리 에이전트
- Firebase MCP 서버를 사용한 관리 시스템
"""

import os
import logging
import json
import aiohttp
from typing import Dict, Any
from .agent.schedule_management_agent import *
from .agent.address_management_agent import *

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP 서버 URL
MCP_SERVER_URL = "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"

class InteriorAgent:
    """인테리어 프로젝트 관리 에이전트"""
    
    def __init__(self):
        self.session = None
        
    async def initialize(self):
        """HTTP 세션 초기화"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        """HTTP 세션 종료"""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def process_message(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """
        사용자 메시지 처리
        
        Args:
            message: 사용자 메시지
            session_id: 세션 ID (선택)
            
        Returns:
            Dict: 처리 결과
        """
        try:
            await self.initialize()
            
            # 세션 ID가 없으면 기본값 사용
            if not session_id:
                session_id = "default-session"
            
            # MCP 서버로 요청 전송
            async with self.session.post(
                MCP_SERVER_URL,
                json={
                    "message": message,
                    "sessionId": session_id
                },
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"MCP 서버 오류: {error_text}")
                    return {
                        "error": "MCP 서버 오류",
                        "details": error_text
                    }
                    
        except Exception as e:
            logger.error(f"메시지 처리 중 오류 발생: {e}")
            return {
                "error": "내부 서버 오류",
                "details": str(e)
            }

# 전역 에이전트 인스턴스
root_agent = InteriorAgent() 