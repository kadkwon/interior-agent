"""
Firebase 클라이언트
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class FirebaseClient:
    """Firebase 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"
    
    async def query_documents(self, collection: str, conditions: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """문서 조회"""
        return []
    
    async def add_document(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 추가"""
        return {"id": "dummy", "data": data}
    
    async def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 업데이트"""
        return {"id": doc_id, "data": data}
    
    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """문서 삭제"""
        return True

def schedule_formatter(schedule_data: Dict[str, Any]) -> str:
    """일정 데이터 포맷팅"""
    return str(schedule_data)

# 전역 클라이언트 인스턴스
firebase_client = FirebaseClient() 