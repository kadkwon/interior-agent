"""
인테리어 프로젝트 관리 에이전트
- Firebase MCP 서버를 사용한 관리 시스템
"""

import logging
from typing import Dict, Any, Tuple
import aiohttp
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.sessions.base_session_service import GetSessionConfig
from datetime import datetime, timedelta
from .agent.address_management_agent import AddressAgent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteriorAgent:
    """인테리어 프로젝트 관리 에이전트"""
    
    def __init__(self):
        self.session = None
        self.address_agent = AddressAgent()
        # 인메모리 세션 서비스 사용
        self.session_service = InMemorySessionService()
        
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
        
        # 주소 관련 의도 체크
        if any(keyword in message for keyword in address_keywords):
            return "address", {}
            
        # 기본값
        return "chat", {}

    def get_session_config(self):
        """세션 설정 가져오기"""
        now = datetime.now()
        timestamp = now - timedelta(days=1)
        return GetSessionConfig(
            num_recent_events=50,
            after_timestamp=timestamp.timestamp()
        )
            
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
                
            # 사용자 ID와 세션 ID 분리
            parts = session_id.split(":")
            user_id = parts[0] if len(parts) > 1 else "default-user"
            chat_session_id = parts[1] if len(parts) > 1 else session_id
            
            logger.info(f"처리 시작 - 메시지: {message}, 사용자 ID: {user_id}, 세션 ID: {chat_session_id}")
            
            # 세션 가져오기 또는 생성
            session = await self.session_service.get_session(
                app_name="interior_agent",
                user_id=user_id,
                session_id=chat_session_id,
                config=self.get_session_config()
            )
            
            if not session:
                # 세션이 없으면 새로 생성
                session = await self.session_service.create_session(
                    app_name="interior_agent",
                    user_id=user_id,
                    session_id=chat_session_id
                )
                
            # 의도 분석
            intent, params = self._analyze_intent(message)
            logger.info(f"의도 분석 결과 - 의도: {intent}, 파라미터: {params}")
            
            # 의도별 처리
            if intent == "address":
                return await self.address_agent.process_message(message, session_id, self.session)
            
            # 일반 채팅 - LLM 호출
            request_data = {
                "jsonrpc": "2.0",
                "method": "mcp_llm_chat",
                "params": {
                    "message": message,
                    "sessionId": session.id,  # ADK 세션 ID 사용
                    "userId": user_id,
                    "context": "당신은 인테리어 프로젝트 관리를 돕는 AI 어시스턴트입니다. 친절하고 전문적으로 응답해주세요."
                },
                "id": 1
            }
            
            logger.info(f"Cloud Run 요청 - {request_data}")
            
            async with self.session.post(
                "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_data = await response.json()
                logger.info(f"Cloud Run 응답 - {response_data}")
                
                if "error" in response_data:
                    error_msg = f"처리 중 오류가 발생했습니다: {response_data['error'].get('message', '알 수 없는 오류')}"
                    logger.error(error_msg)
                    return {
                        "response": error_msg,
                        "toolsUsed": []
                    }
                    
                return {
                    "response": response_data.get("result", {}).get("response", "죄송합니다. 응답을 처리할 수 없습니다."),
                    "toolsUsed": response_data.get("result", {}).get("toolsUsed", [])
                }
                
        except Exception as e:
            logger.error(f"메시지 처리 중 오류 발생: {e}", exc_info=True)
            return {
                "response": f"처리 중 오류가 발생했습니다: {str(e)}",
                "toolsUsed": []
            } 