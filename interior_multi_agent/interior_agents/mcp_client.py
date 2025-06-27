"""
🔌 MCP HTTP Direct 클라이언트 - JSON-RPC 2.0 직접 구현
"""

import aiohttp
import json
import uuid
from typing import Dict, Any

class MCPClient:
    """미니멀한 MCP HTTP 클라이언트 - HTTP Direct with Session"""
    
    def __init__(self, url: str):
        self.url = url
        self.initialized = False
        self.session_id = None
    
    async def initialize(self, session):
        """MCP 서버 초기화 - Stream 응답 처리"""
        if self.initialized:
            return True
            
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        init_payload = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "interior-agent", "version": "1.0.0"}
            }
        }
        
        try:
            async with session.post(self.url, json=init_payload, headers=headers, timeout=15) as response:
                if response.status == 200:
                    # Stream 응답 처리
                    response_text = await response.text()
                    print(f"🔥 MCP 초기화 응답: {response_text[:100]}...")
                    self.initialized = True
                    return True
                else:
                    print(f"❌ MCP 초기화 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ MCP 초기화 오류: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """JSON-RPC 2.0 도구 호출 - HTTP Direct 방식"""
        async with aiohttp.ClientSession() as session:
            try:
                # 1. 초기화 (필요한 경우)
                if not self.initialized:
                    await self._initialize(session)
                
                # 2. 도구 호출
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream, application/json"
                }
                
                # 세션 ID가 있으면 헤더에 추가
                if self.session_id:
                    headers["mcp-session-id"] = self.session_id
                
                payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments}
                }
                
                print(f"🔥 MCP 도구 호출: {tool_name}")
                
                async with session.post(self.url, json=payload, headers=headers, timeout=30) as response:
                    print(f"📡 응답 상태: {response.status}")
                    print(f"📋 Content-Type: {response.content_type}")
                    
                    if response.status == 200:
                        response_text = await response.text()
                        print(f"📝 응답 내용: {response_text[:300]}...")
                        
                        # SSE 형식 파싱
                        if 'event:' in response_text or 'data:' in response_text:
                            lines = response_text.strip().split('\n')
                            for line in lines:
                                if line.startswith('data: '):
                                    try:
                                        json_data = json.loads(line[6:])
                                        if "result" in json_data:
                                            print(f"✅ 결과 파싱 성공!")
                                            return json_data["result"]
                                        return json_data
                                    except Exception as parse_error:
                                        print(f"JSON 파싱 오류: {parse_error}")
                                        continue
                        else:
                            # 일반 JSON 응답
                            try:
                                json_result = json.loads(response_text)
                                if "result" in json_result:
                                    return json_result["result"]
                                return json_result
                            except:
                                pass
                        
                        return {"raw_response": response_text}
                    else:
                        error_text = await response.text()
                        return {"error": f"HTTP {response.status}: {error_text[:100]}"}
                    
            except Exception as e:
                print(f"❌ MCP 연결 오류: {e}")
                return {"error": f"Connection error: {str(e)}"}
    
    async def _initialize(self, session):
        """MCP 초기화 및 세션 ID 추출"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream, application/json"
        }
        
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "interior-agent", "version": "1.0.0"}
            }
        }
        
        try:
            async with session.post(self.url, json=init_payload, headers=headers, timeout=15) as response:
                if response.status == 200:
                    # 응답에서 세션 ID 추출 시도
                    response_text = await response.text()
                    print(f"🔍 초기화 응답: {response_text[:200]}...")
                    
                    # SSE 응답에서 세션 정보 찾기
                    if 'data:' in response_text:
                        lines = response_text.strip().split('\n')
                        for line in lines:
                            if line.startswith('data: '):
                                try:
                                    data = json.loads(line[6:])
                                    if "result" in data and "sessionId" in data["result"]:
                                        self.session_id = data["result"]["sessionId"]
                                        print(f"✅ 세션 ID 획득: {self.session_id}")
                                    elif "result" in data:
                                        # 세션 ID가 없어도 초기화 성공으로 처리
                                        print(f"✅ 초기화 성공 (세션 ID 없음)")
                                except Exception as parse_error:
                                    print(f"응답 파싱 오류: {parse_error}")
                    
                    # 응답 헤더에서 세션 ID 확인
                    if 'mcp-session-id' in response.headers:
                        self.session_id = response.headers['mcp-session-id']
                        print(f"✅ 헤더에서 세션 ID 획득: {self.session_id}")
                    
                    self.initialized = True
                    return True
        except Exception as e:
            print(f"❌ MCP 초기화 오류: {e}")
        
        return False

# 전역 클라이언트 인스턴스
firebase_client = MCPClient("https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp")
email_client = MCPClient("https://estimate-email-mcp-638331849453.asia-northeast3.run.app/mcp") 