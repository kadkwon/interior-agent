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
        self._session = None  # 🔧 세션 재사용을 위한 변수 추가
        self.current_adk_session = None  # 🆕 현재 ADK 세션 추적
    
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
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], adk_session_id: str = None) -> Dict[str, Any]:
        """JSON-RPC 2.0 도구 호출 - ADK 세션 연동 방식 (수정됨)"""
        
        # 🔧 ADK 세션이 바뀌면 MCP 세션도 새로 시작
        if adk_session_id and adk_session_id != self.current_adk_session:
            print(f"🔄 ADK 세션 변경 감지: {self.current_adk_session} → {adk_session_id}")
            await self._reset_mcp_session()
            self.current_adk_session = adk_session_id
        
        # 🔧 세션 재사용 또는 새로 생성
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        
        try:
            # 1. 초기화 (필요한 경우) - 같은 세션 사용
            if not self.initialized:
                print(f"🔧 MCP 초기화 시작 (ADK 세션: {adk_session_id})...")
                await self._initialize(self._session)
            
            # 2. 도구 호출 - 같은 세션 사용
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream, application/json"
            }
            
            # 🔧 세션 ID를 여러 방법으로 전송 (개선된 버전)
            if self.session_id:
                session_str = str(self.session_id)
                headers["mcp-session-id"] = session_str
                headers["x-session-id"] = session_str
                headers["session-id"] = session_str
            
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments}
            }
            
            # 페이로드에도 세션 ID 추가 (다양한 방법 시도)
            if self.session_id:
                session_str = str(self.session_id)
                payload["params"]["sessionId"] = session_str
                payload["params"]["session_id"] = session_str
            
            print(f"🔥 MCP 도구 호출: {tool_name} (세션 재사용)")
            print(f"🔑 사용 중인 세션 ID: {self.session_id}")
            
            async with self._session.post(self.url, json=payload, headers=headers, timeout=20) as response:
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
                                    elif "error" in json_data:
                                        print(f"❌ MCP 오류: {json_data['error']}")
                                        return {"error": json_data["error"]}
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
                            elif "error" in json_result:
                                print(f"❌ MCP 오류: {json_result['error']}")
                                return {"error": json_result["error"]}
                            return json_result
                        except:
                            pass
                    
                    return {"raw_response": response_text}
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP 오류: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text[:100]}"}
                
        except Exception as e:
            print(f"❌ MCP 연결 오류: {e}")
            # 세션 오류 시 재생성
            if self._session and not self._session.closed:
                await self._session.close()
            self._session = None
            self.initialized = False
            return {"error": f"Connection error: {str(e)}"}
    
    async def _initialize(self, session):
        """MCP 초기화 및 세션 ID 추출 (개선된 버전)"""
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
                    response_text = await response.text()
                    print(f"🔍 초기화 응답: {response_text[:200]}...")
                    
                    # 🔧 세션 ID 없이도 작동하도록 수정
                    # Firebase MCP가 세션 ID를 제공하지 않는 경우 임시 ID 생성
                    import time
                    import uuid
                    
                    # 여러 방법으로 세션 ID 시도
                    self.session_id = f"agent_session_{int(time.time())}"
                    print(f"🔧 임시 세션 ID 생성: {self.session_id}")
                    
                    # SSE 응답에서 실제 세션 정보 찾기 (있다면 사용)
                    if 'data:' in response_text:
                        lines = response_text.strip().split('\n')
                        for line in lines:
                            if line.startswith('data: '):
                                try:
                                    import json
                                    data = json.loads(line[6:])
                                    # 실제 세션 ID가 있다면 사용
                                    if "result" in data:
                                        result = data["result"]
                                        for field in ["sessionId", "session_id", "id"]:
                                            if field in result and result[field] != 1:  # ID 1은 제외
                                                self.session_id = str(result[field])
                                                print(f"✅ 실제 세션 ID 발견: {self.session_id}")
                                                break
                                except Exception as parse_error:
                                    print(f"⚠️ 응답 파싱 오류: {parse_error}")
                    
                    # 응답 헤더에서 세션 ID 확인
                    for header_name in ['mcp-session-id', 'x-session-id', 'session-id']:
                        if header_name in response.headers:
                            self.session_id = response.headers[header_name]
                            print(f"✅ 헤더에서 세션 ID 획득: {self.session_id}")
                            break
                    
                    self.initialized = True
                    print(f"🎯 최종 사용할 세션 ID: {self.session_id}")
                    return True
        except Exception as e:
            print(f"❌ MCP 초기화 오류: {e}")
        
        return False
    
    async def _reset_mcp_session(self):
        """MCP 세션 재설정 (ADK 세션 변경 시 호출)"""
        print(f"🔄 MCP 세션 재설정: {self.url}")
        
        # 기존 세션 정리
        if self._session and not self._session.closed:
            await self._session.close()
        
        # 상태 초기화
        self._session = None
        self.initialized = False
        self.session_id = None
        
        print(f"✅ MCP 세션 재설정 완료")
    
    async def close(self):
        """세션 정리"""
        if self._session and not self._session.closed:
            await self._session.close()
            print(f"🔧 MCP 클라이언트 세션 정리됨: {self.url}")
        self._session = None
        self.initialized = False
        self.current_adk_session = None

# Firebase와 Email MCP 클라이언트
firebase_client = MCPClient("https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp")
email_client = MCPClient("https://estimate-email-mcp-638331849453.asia-northeast3.run.app/mcp") 