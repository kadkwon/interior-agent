"""
MCP 도구 호출 유틸리티
"""

import logging
from typing import Dict, Any, Optional
import aiohttp

# 로깅 설정
logger = logging.getLogger(__name__)

# MCP 서버 URL
MCP_SERVER_URL = "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"

async def call_mcp_tool(method: str, params: Dict[str, Any], session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
    """
    MCP 도구 호출
    
    Args:
        method: 호출할 MCP 메서드 이름
        params: 메서드 파라미터
        session: 기존 aiohttp 세션 (옵션)
        
    Returns:
        Dict: MCP 응답
    """
    should_close_session = False
    if not session:
        session = aiohttp.ClientSession()
        should_close_session = True
        
    try:
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        async with session.post(
            MCP_SERVER_URL,
            json=request_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            response_data = await response.json()
            
            if "error" in response_data:
                logger.error(f"MCP 도구 호출 오류 ({method}): {response_data['error']}")
                return {
                    "status": "error",
                    "error": response_data["error"].get("message", "알 수 없는 오류")
                }
                
            return {
                "status": "success",
                "data": response_data.get("result", {})
            }
            
    except Exception as e:
        logger.error(f"MCP 도구 호출 중 오류 발생 ({method}): {e}")
        return {
            "status": "error",
            "error": str(e)
        }
        
    finally:
        if should_close_session:
            await session.close()

# Firestore 도구 호출 헬퍼 함수들
async def firestore_add_document(collection: str, data: Dict[str, Any], session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
    """Firestore 문서 추가"""
    return await call_mcp_tool(
        "mcp_firebase_firestore_add_document",
        {"collection": collection, "data": data},
        session
    )

async def firestore_get_document(collection: str, doc_id: str, session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
    """Firestore 문서 조회"""
    return await call_mcp_tool(
        "mcp_firebase_firestore_get_document",
        {"collection": collection, "id": doc_id},
        session
    )

async def firestore_update_document(collection: str, doc_id: str, data: Dict[str, Any], session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
    """Firestore 문서 업데이트"""
    return await call_mcp_tool(
        "mcp_firebase_firestore_update_document",
        {"collection": collection, "id": doc_id, "data": data},
        session
    )

async def firestore_delete_document(collection: str, doc_id: str, session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
    """Firestore 문서 삭제"""
    return await call_mcp_tool(
        "mcp_firebase_firestore_delete_document",
        {"collection": collection, "id": doc_id},
        session
    )

async def firestore_list_documents(
    collection: str,
    filters: Optional[list] = None,
    order_by: Optional[list] = None,
    limit: int = 20,
    session: Optional[aiohttp.ClientSession] = None
) -> Dict[str, Any]:
    """Firestore 문서 목록 조회"""
    params = {"collection": collection, "limit": limit}
    if filters:
        params["filters"] = filters
    if order_by:
        params["orderBy"] = order_by
        
    return await call_mcp_tool(
        "mcp_firebase_firestore_list_documents",
        params,
        session
    ) 