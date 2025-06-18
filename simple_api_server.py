"""
FastAPI Firebase MCP 프록시 서버 - React 챗봇과 Firebase MCP 서버 간 연결만 담당
"""

import logging
import uuid
import json
import aiohttp
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="Firebase MCP 프록시 서버", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase MCP 서버 설정
FIREBASE_MCP_URL = "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"

class ToolCallRequest(BaseModel):
    """Firebase MCP 도구 호출 요청"""
    tool_name: str
    arguments: Dict[str, Any]

class FirebaseMCPClient:
    """Firebase MCP 서버와 통신하는 클라이언트"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session = None
        self.session_id = None
        self.initialized = False
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self._initialize_mcp()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _parse_sse_response(self, response) -> Dict[str, Any]:
        """SSE 응답을 파싱하여 JSON 데이터 추출"""
        try:
            content = await response.text()
            
            # SSE 형식에서 JSON 추출
            lines = content.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    try:
                        json_data = json.loads(line[6:])  # 'data: ' 제거
                        return json_data
                    except json.JSONDecodeError:
                        continue
            
            logger.warning(f"SSE 응답에서 JSON 데이터를 찾을 수 없습니다: {content}")
            return {"error": "No valid JSON data in SSE response"}
            
        except Exception as e:
            logger.error(f"SSE 응답 파싱 오류: {e}")
            return {"error": f"SSE parsing error: {str(e)}"}
    
    async def _initialize_mcp(self) -> bool:
        """MCP 프로토콜 초기화"""
        if self.initialized:
            return True
            
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "firebase-mcp-proxy",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        try:
            async with self.session.post(
                self.server_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    self.session_id = response.headers.get('mcp-session-id')
                    if not self.session_id:
                        self.session_id = str(uuid.uuid4())
                    
                    if response.headers.get('Content-Type') == 'text/event-stream':
                        result = await self._parse_sse_response(response)
                    else:
                        result = await response.json()
                    
                    self.initialized = True
                    logger.info(f"MCP 초기화 성공. 세션 ID: {self.session_id}")
                    return True
                else:
                    logger.error(f"MCP 초기화 실패: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"MCP 초기화 오류: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Firebase MCP 도구 호출"""
        
        if not self.initialized:
            logger.warning("MCP가 초기화되지 않았습니다. 재시도합니다.")
            if not await self._initialize_mcp():
                return {"error": "MCP 초기화 실패"}
        
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    if response.headers.get('Content-Type') == 'text/event-stream':
                        result = await self._parse_sse_response(response)
                    else:
                        result = await response.json()
                    
                    logger.info(f"도구 '{tool_name}' 호출 성공")
                    return result
                else:
                    logger.error(f"Firebase MCP 도구 호출 실패: {response.status}")
                    response_text = await response.text()
                    logger.error(f"응답 내용: {response_text}")
                    return {"error": f"HTTP {response.status}: {response_text}"}
                    
        except Exception as e:
            logger.error(f"Firebase MCP 통신 오류: {e}")
            return {"error": str(e)}

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    try:
        async with FirebaseMCPClient(FIREBASE_MCP_URL) as client:
            test_result = await client.call_tool("firestore_list_collections", {"random_string": "test"})
            firebase_available = "error" not in test_result
        
        return {
            "status": "healthy",
            "firebase_connected": firebase_available,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check 실패: {e}")
        return {
            "status": "degraded",
            "firebase_connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/firebase/tool")
async def call_firebase_tool(request: ToolCallRequest):
    """Firebase MCP 도구 호출 API - 모든 도구를 통합하여 처리"""
    try:
        async with FirebaseMCPClient(FIREBASE_MCP_URL) as client:
            result = await client.call_tool(request.tool_name, request.arguments)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8505) 