"""
🔌 MCP HTTP Direct 클라이언트 - JSON-RPC 2.0 직접 구현
"""

import aiohttp
import json
import uuid
from typing import Dict, Any

class MCPClient:
    """미니멀한 MCP HTTP 클라이언트"""
    
    def __init__(self, url: str):
        self.url = url
        self.session_id = str(uuid.uuid4())
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """JSON-RPC 2.0 도구 호출"""
        async with aiohttp.ClientSession() as session:
            # 도구 호출 페이로드
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments}
            }
            
            headers = {
                "Content-Type": "application/json",
                "mcp-session-id": self.session_id
            }
            
            async with session.post(self.url, json=payload, headers=headers, timeout=30) as response:
                if response.status != 200:
                    return {"error": f"HTTP {response.status}"}
                
                result = await response.json()
                return result.get("result", result)

# 전역 클라이언트 인스턴스
firebase_client = MCPClient("https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp")
email_client = MCPClient("https://estimate-email-mcp-638331849453.asia-northeast3.run.app/mcp") 