"""
Firebase MCP 도구
"""

import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from interior_multi_agent.interior_agents.tools.base import Tool

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseMCPTool(Tool):
    """Firebase MCP 도구"""
    
    def __init__(self):
        super().__init__("firebase_mcp")
        
        # Firebase 초기화
        try:
            cred = credentials.Certificate(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
            firebase_admin.initialize_app(cred, {
                'projectId': os.environ.get("FIREBASE_PROJECT_ID")
            })
            self.db = firestore.client()
            logger.info("✅ Firebase가 성공적으로 초기화되었습니다.")
        except Exception as e:
            logger.error(f"❌ Firebase 초기화 실패: {e}")
            raise
        
    async def execute(self, params: dict) -> dict:
        """도구 실행"""
        try:
            # Firebase MCP 명령 실행
            command = params.get("command")
            if command == "connect":
                return {"status": "connected"}
            elif command == "query":
                return await self._execute_query(params)
            else:
                raise ValueError(f"알 수 없는 명령: {command}")
        except Exception as e:
            logger.error(f"Firebase MCP 도구 실행 중 오류 발생: {e}")
            raise

    async def _execute_query(self, params: dict) -> dict:
        """쿼리 실행"""
        try:
            # 쿼리 파라미터 추출
            query = params.get("query")
            collection = params.get("collection", "schedules")  # 기본값: schedules
            
            # 쿼리 실행
            docs = self.db.collection(collection).stream()
            results = []
            
            # 결과 수집
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)
                
            return {"data": results}
        except Exception as e:
            logger.error(f"쿼리 실행 중 오류 발생: {e}")
            raise 