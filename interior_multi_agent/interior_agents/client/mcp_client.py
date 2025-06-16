"""
Firebase MCP 클라이언트 모듈
- MCP 프로토콜을 통해 Firebase와 통신
"""

from typing import Dict, List, Optional, Any
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
import asyncio
import logging
import json
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseMCPClient:
    """Firebase MCP 클라이언트 클래스"""
    
    def __init__(self):
        """클라이언트 초기화"""
        self.toolset = None
        self.exit_stack = None
        
    async def initialize(self):
        """MCP 도구 세트 초기화"""
        try:
            self.toolset, self.exit_stack = await MCPToolset.from_server(
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
            logger.info("✅ MCP 도구 세트 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"❌ MCP 도구 세트 초기화 실패: {e}")
            return False
            
    async def close(self):
        """리소스 정리"""
        if self.exit_stack:
            await self.exit_stack.aclose()
            
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """MCP 도구 호출"""
        if not self.toolset:
            await self.initialize()
            
        try:
            tool = next((t for t in self.toolset if t.name == tool_name), None)
            if not tool:
                raise ValueError(f"도구를 찾을 수 없음: {tool_name}")
                
            result = await tool.run_async(args=params)
            return result
        except Exception as e:
            logger.error(f"❌ 도구 호출 실패 ({tool_name}): {e}")
            return None
            
    # Firestore 작업
    async def create_document(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 생성"""
        return await self.call_tool("firestore_create_document", {
            "collection": collection,
            "data": data
        })
        
    async def get_document(self, collection: str, doc_id: str) -> Dict[str, Any]:
        """문서 조회"""
        return await self.call_tool("firestore_get_document", {
            "collection": collection,
            "documentId": doc_id
        })
        
    async def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 업데이트"""
        return await self.call_tool("firestore_update_document", {
            "collection": collection,
            "documentId": doc_id,
            "data": data
        })
        
    async def delete_document(self, collection: str, doc_id: str) -> Dict[str, Any]:
        """문서 삭제"""
        return await self.call_tool("firestore_delete_document", {
            "collection": collection,
            "documentId": doc_id
        })
        
    async def list_documents(self, collection: str, limit: int = 10) -> List[Dict[str, Any]]:
        """문서 목록 조회"""
        return await self.call_tool("firestore_list_documents", {
            "collection": collection,
            "limit": limit
        })
        
    async def query_collection(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """컬렉션 쿼리"""
        return await self.call_tool("firestore_query_collection", {
            "collection": collection,
            **query
        })
        
    # Storage 작업
    async def list_files(self, path: str = "") -> List[str]:
        """스토리지 파일 목록"""
        return await self.call_tool("storage_list_files", {
            "path": path
        })
        
    async def upload_file(self, local_path: str, storage_path: str) -> Dict[str, Any]:
        """파일 업로드"""
        return await self.call_tool("storage_upload_file", {
            "localPath": local_path,
            "storagePath": storage_path
        })
        
    async def download_file(self, storage_path: str, local_path: str) -> Dict[str, Any]:
        """파일 다운로드"""
        return await self.call_tool("storage_download_file", {
            "storagePath": storage_path,
            "localPath": local_path
        })
        
    async def delete_file(self, storage_path: str) -> Dict[str, Any]:
        """파일 삭제"""
        return await self.call_tool("storage_delete_file", {
            "path": storage_path
        })
        
    # 프로젝트 관리
    async def get_project_info(self) -> Dict[str, Any]:
        """프로젝트 정보 조회"""
        return await self.call_tool("firebase_get_project_info", {})
        
    async def list_projects(self) -> List[Dict[str, Any]]:
        """프로젝트 목록 조회"""
        return await self.call_tool("firebase_list_projects", {})

# 싱글톤 인스턴스
_client = None

def get_client() -> FirebaseMCPClient:
    """싱글톤 클라이언트 인스턴스 반환"""
    global _client
    if not _client:
        _client = FirebaseMCPClient()
    return _client 