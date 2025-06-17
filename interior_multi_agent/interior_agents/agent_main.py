"""
인테리어 프로젝트 관리 에이전트
- Firebase MCP 서버를 사용한 관리 시스템
"""

import os
import logging
import json
import aiohttp
from typing import Dict, Any, Tuple
from .agent.address_management_agent import AddressAgent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteriorAgent:
    """인테리어 프로젝트 관리 에이전트"""
    
    def __init__(self):
        self.session = None
        self.address_agent = AddressAgent()
        
    async def initialize(self):
        """HTTP 세션 초기화"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        """HTTP 세션 종료"""
        if self.session:
            await self.session.close()
            self.session = None
            
    def _analyze_intent(self, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        사용자 메시지의 의도 분석
        
        Args:
            message: 사용자 메시지
            
        Returns:
            Tuple[str, Dict]: (의도, 추출된 파라미터)
        """
        # 주소 관련 키워드
        address_keywords = ["주소", "위치", "현장", "장소", "동", "구", "시"]
        
        message = message.lower()
        
        # 주소 관련 의도 체크
        if any(keyword in message for keyword in address_keywords):
            return "address", {}
            
        # 기본값
        return "chat", {}
            
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
                
            # 의도 분석
            intent, params = self._analyze_intent(message)
            
            # 의도별 처리
            if intent == "address":
                return await self.address_agent.process_message(message, session_id, self.session)
            else:
                # 일반 채팅은 MCP 서버로 전달
                request_data = {
                    "jsonrpc": "2.0",
                    "method": "chat",
                    "params": {
                        "message": message,
                        "sessionId": session_id
                    },
                    "id": 1
                }
                
                async with self.session.post(
                    "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response_data = await response.json()
                    
                    if "error" in response_data:
                        logger.error(f"MCP 서버 오류: {response_data['error']}")
                        return {
                            "error": "MCP 서버 오류",
                            "details": response_data["error"].get("message", "알 수 없는 오류")
                        }
                        
                    return {
                        "response": response_data.get("result", {}).get("response", "죄송합니다. 응답을 처리할 수 없습니다."),
                        "toolsUsed": response_data.get("result", {}).get("toolsUsed", [])
                    }
                    
        except Exception as e:
            logger.error(f"메시지 처리 중 오류 발생: {e}")
            return {
                "error": "내부 서버 오류",
                "details": str(e)
            }

# 전역 에이전트 인스턴스
root_agent = InteriorAgent() 