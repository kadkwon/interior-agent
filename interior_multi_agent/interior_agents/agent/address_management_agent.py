"""
주소 관리 에이전트

addresses 컬렉션의 CRUD 작업을 담당하는 전용 에이전트입니다.
"""

import logging
from typing import Dict, Any
import aiohttp
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.sessions.base_session_service import GetSessionConfig
from datetime import datetime, timedelta

# 로깅 설정
logger = logging.getLogger(__name__)

class AddressAgent:
    """주소 관리 에이전트"""
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        
    def get_session_config(self):
        """세션 설정 가져오기"""
        now = datetime.now()
        timestamp = now - timedelta(days=1)
        return GetSessionConfig(
            num_recent_events=50,
            after_timestamp=timestamp.timestamp()
        )
    
    async def process_message(self, message: str, session_id: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """
        주소 관련 메시지 처리
        
        Args:
            message: 사용자 메시지
            session_id: 세션 ID
            session: HTTP 세션
            
        Returns:
            Dict: 처리 결과
        """
        try:
            # 세션 ID에서 사용자 ID 추출
            parts = session_id.split(":")
            user_id = parts[0] if len(parts) > 1 else "default-user"
            chat_session_id = parts[1] if len(parts) > 1 else session_id
            
            logger.info(f"주소 처리 시작 - 메시지: {message}, 사용자 ID: {user_id}, 세션 ID: {chat_session_id}")
            
            # ADK 세션 가져오기 또는 생성
            adk_session = await self.session_service.get_session(
                app_name="interior_agent",
                user_id=user_id,
                session_id=chat_session_id,
                config=self.get_session_config()
            )
            
            if not adk_session:
                adk_session = await self.session_service.create_session(
                    app_name="interior_agent",
                    user_id=user_id,
                    session_id=chat_session_id
                )
            
            # 주소 조회 요청
            if "조회" in message or "검색" in message or "찾아" in message:
                request_data = {
                    "jsonrpc": "2.0",
                    "method": "mcp_firebase_firestore_list_documents",
                    "params": {
                        "collection": "addresses",
                        "userId": user_id,
                        "sessionId": adk_session.id  # ADK 세션 ID 사용
                    },
                    "id": 1
                }
                
                logger.info(f"Cloud Run 요청 - {request_data}")
                
                async with session.post(
                    "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response_data = await response.json()
                    logger.info(f"Cloud Run 응답 - {response_data}")
                    
                    if "error" in response_data:
                        error_msg = f"주소 조회 중 오류가 발생했습니다: {response_data['error'].get('message', '알 수 없는 오류')}"
                        logger.error(error_msg)
                        return {
                            "response": error_msg,
                            "toolsUsed": ["mcp_firebase_firestore_list_documents"]
                        }
                        
                    addresses = response_data.get("result", {}).get("documents", [])
                    if not addresses:
                        return {
                            "response": "등록된 주소가 없습니다.",
                            "toolsUsed": ["mcp_firebase_firestore_list_documents"]
                        }
                        
                    address_list = "\n".join([
                        f"- {addr.get('data', {}).get('address', '알 수 없는 주소')}"
                        for addr in addresses
                    ])
                    
                    return {
                        "response": f"조회된 주소 목록입니다:\n{address_list}",
                        "toolsUsed": ["mcp_firebase_firestore_list_documents"]
                    }
            
            # 일반 대화
            return {
                "response": "안녕하세요! 주소 관리를 도와드릴 수 있습니다. 주소 조회나 검색이 필요하시다면 말씀해 주세요.",
                "toolsUsed": []
            }
            
        except Exception as e:
            logger.error(f"주소 처리 중 오류 발생: {e}", exc_info=True)
            return {
                "response": f"처리 중 오류가 발생했습니다: {str(e)}",
                "toolsUsed": []
            } 