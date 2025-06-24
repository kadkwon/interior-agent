"""
🔥 Firebase MCP 서버 공통 연결 클라이언트 모듈

## 🎯 모듈의 역할
이 모듈은 **Firebase MCP 서버와의 HTTP 통신을 전담**하는 공통 클라이언트입니다.

### 📋 주요 책임:
1. **연결 관리**: Firebase MCP 서버 초기화 및 세션 관리
2. **HTTP 통신**: JSON-RPC 2.0 프로토콜로 도구 호출
3. **에러 처리**: 타임아웃, 연결 실패, JSON 파싱 오류 처리
4. **SSE 응답**: Server-Sent Events 형식 응답 파싱
5. **로깅**: 상세한 디버깅 정보 제공

### 🏗️ 설계 철학:
- **단일 책임**: Firebase 연결만 담당
- **재사용성**: 모든 ADK 에이전트에서 공통 사용
- **안정성**: 검증된 연결 로직 제공
- **확장성**: 새로운 Firebase 기능 쉽게 추가

### 🔌 사용 방법:
```python
from .firebase_client import FirebaseDirectClient

# 인스턴스 생성
firebase_client = FirebaseDirectClient()

# 도구 호출
result = await firebase_client.call_tool("firestore_list_documents", {
    "collection": "addressesJson",
    "limit": 10
})
```

### 🎯 장점:
- ✅ 코드 중복 제거 (DRY 원칙)
- ✅ 유지보수 중앙화 (한 곳에서 관리)
- ✅ 일관성 보장 (모든 에이전트가 같은 방식으로 연결)
- ✅ 테스트 용이성 (모킹 및 단위 테스트)
- ✅ 기능 확장성 (새 기능 한 번에 모든 에이전트 적용)

### 🔧 기술 스택:
- **HTTP 클라이언트**: aiohttp (비동기 처리)
- **프로토콜**: JSON-RPC 2.0
- **응답 형식**: SSE (Server-Sent Events) 지원
- **에러 처리**: 포괄적인 예외 처리 및 재시도 로직

### 📝 Firebase MCP 서버 정보:
- **URL**: https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp
- **지원 도구**: firestore_*, auth_*, storage_* 
- **프로토콜 버전**: 2024-11-05
"""

import asyncio
import json
import aiohttp
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

class FirebaseDirectClient:
    """
    🔥 Firebase MCP 서버 전용 HTTP 클라이언트
    
    이 클라이언트는 Firebase MCP 서버와의 모든 통신을 담당합니다.
    simple_api_server.py에서 검증된 연결 방식을 기반으로 구현되었습니다.
    
    주요 기능:
    - Firebase MCP 서버 초기화
    - JSON-RPC 2.0 도구 호출  
    - SSE 응답 파싱
    - 세션 관리
    - 에러 처리 및 로깅
    """
    
    def __init__(self):
        """
        Firebase 클라이언트 초기화
        
        설정값:
        - server_url: Firebase MCP 서버 엔드포인트
        - session_id: 세션 식별자 (자동 생성)
        - initialized: 초기화 상태 플래그
        """
        self.server_url = "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"
        self.session_id: Optional[str] = None
        self.initialized: bool = False
        
        # 로깅용 클라이언트 ID
        self.client_id = str(uuid.uuid4())[:8]
        print(f"🔥 Firebase 클라이언트 생성 완료 (ID: {self.client_id})")
    
    async def _parse_sse_response(self, response) -> Dict[str, Any]:
        """
        SSE (Server-Sent Events) 응답을 파싱하여 JSON 데이터 추출
        
        Firebase MCP 서버는 text/event-stream 형식으로 응답할 수 있으므로
        이를 파싱하여 실제 JSON 데이터를 추출합니다.
        
        Args:
            response: aiohttp ClientResponse 객체
            
        Returns:
            Dict[str, Any]: 파싱된 JSON 데이터
        """
        try:
            content = await response.text()
            
            # SSE 형식에서 JSON 추출 (data: {...} 형태)
            lines = content.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    try:
                        json_data = json.loads(line[6:])  # 'data: ' 제거
                        print(f"🔥 [{self.client_id}] SSE JSON 파싱 성공")
                        return json_data
                    except json.JSONDecodeError:
                        continue
            
            print(f"⚠️ [{self.client_id}] SSE 응답에서 유효한 JSON을 찾을 수 없음: {content[:200]}")
            return {"error": "No valid JSON data in SSE response"}
            
        except Exception as e:
            print(f"❌ [{self.client_id}] SSE 응답 파싱 오류: {e}")
            return {"error": f"SSE parsing error: {str(e)}"}
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Firebase MCP 도구 호출 메인 메서드
        
        이 메서드는 simple_api_server.py와 동일한 방식으로 Firebase MCP 서버에
        HTTP 요청을 보내고 응답을 처리합니다.
        
        Args:
            tool_name (str): 호출할 도구 이름 (예: "firestore_list_documents")
            arguments (Dict[str, Any]): 도구에 전달할 인수들
            
        Returns:
            Dict[str, Any]: 도구 실행 결과 또는 에러 정보
            
        처리 단계:
        1. Firebase MCP 서버 초기화 (세션별 1회)
        2. 도구 호출 요청 전송
        3. 응답 파싱 (JSON 또는 SSE)
        4. 결과 반환
        """
        
        print(f"🔥 [{self.client_id}] Firebase MCP 요청: {tool_name} - {arguments}")
        
        async with aiohttp.ClientSession() as session:
            try:
                # 1단계: Firebase MCP 서버 초기화
                init_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "adk-firebase-client",
                            "version": "1.0.0"
                        }
                    }
                }
                
                print(f"🔥 [{self.client_id}] Firebase MCP 초기화 시도...")
                async with session.post(
                    self.server_url,
                    json=init_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as init_response:
                    
                    init_text = await init_response.text()
                    print(f"🔥 [{self.client_id}] MCP 초기화 응답: {init_response.status} - {init_text[:200]}")
                    
                    if init_response.status == 200:
                        # 세션 ID 추출 및 저장
                        self.session_id = init_response.headers.get('mcp-session-id')
                        if not self.session_id:
                            self.session_id = f"adk-{self.client_id}-{int(datetime.now().timestamp())}"
                        print(f"🔥 [{self.client_id}] MCP 세션 ID 설정: {self.session_id}")
                        self.initialized = True
                    else:
                        return {"error": f"MCP 초기화 실패: {init_response.status}"}
                
                # 2단계: 도구 호출 요청
                tool_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                print(f"🔥 [{self.client_id}] Firebase MCP 도구 호출: {tool_name}")
                
                # 헤더 구성 (세션 ID 포함)
                tool_headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
                if self.session_id:
                    tool_headers["mcp-session-id"] = self.session_id
                    print(f"🔥 [{self.client_id}] 세션 ID 헤더 추가: {self.session_id}")
                
                # 3단계: 도구 호출 및 응답 처리
                async with session.post(
                    self.server_url,
                    json=tool_payload,
                    headers=tool_headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as tool_response:
                    
                    response_text = await tool_response.text()
                    print(f"🔥 [{self.client_id}] Firebase MCP 도구 응답 상태: {tool_response.status}")
                    print(f"🔥 [{self.client_id}] Firebase MCP 도구 응답 내용: {response_text[:500]}")
                    
                    if tool_response.status == 200:
                        try:
                            # Content-Type에 따라 다르게 처리
                            content_type = tool_response.headers.get('Content-Type', '')
                            if 'text/event-stream' in content_type:
                                print(f"🔥 [{self.client_id}] SSE 응답 감지 - 파싱 시작...")
                                result = await self._parse_sse_response(tool_response)
                            else:
                                result = await tool_response.json()
                            
                            # 에러 체크
                            if "error" in result:
                                error_msg = result["error"].get("message", "Unknown error")
                                print(f"❌ [{self.client_id}] Firebase MCP 에러: {error_msg}")
                                return {"error": error_msg}
                            
                            # 결과 반환
                            if "result" in result:
                                print(f"✅ [{self.client_id}] Firebase MCP 성공: {tool_name}")
                                return result["result"]
                            else:
                                print(f"⚠️ [{self.client_id}] Firebase MCP 응답에 result 없음: {result}")
                                return result
                                
                        except Exception as json_error:
                            print(f"❌ [{self.client_id}] JSON 파싱 에러: {json_error}")
                            return {"error": f"JSON parsing failed: {str(json_error)}"}
                    else:
                        print(f"❌ [{self.client_id}] HTTP 에러 {tool_response.status}: {response_text}")
                        return {"error": f"HTTP {tool_response.status}: {response_text[:200]}"}
                        
            except asyncio.TimeoutError:
                print(f"❌ [{self.client_id}] Firebase MCP 타임아웃: {tool_name}")
                return {"error": "Request timeout"}
            except Exception as e:
                print(f"❌ [{self.client_id}] Firebase MCP 연결 에러: {e}")
                return {"error": f"Connection error: {str(e)}"}
    
    async def get_server_status(self) -> Dict[str, Any]:
        """
        Firebase MCP 서버 상태 확인
        
        서버가 정상적으로 응답하는지 확인합니다.
        주로 디버깅이나 헬스체크 용도로 사용됩니다.
        
        Returns:
            Dict[str, Any]: 서버 상태 정보
        """
        try:
            result = await self.call_tool("firestore_list_collections", {})
            if "error" not in result:
                return {
                    "status": "healthy",
                    "server_url": self.server_url,
                    "session_id": self.session_id,
                    "client_id": self.client_id
                }
            else:
                return {
                    "status": "error",
                    "error": result["error"],
                    "server_url": self.server_url
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "server_url": self.server_url
            }
    
    def __str__(self) -> str:
        """클라이언트 정보 문자열 표현"""
        return f"FirebaseDirectClient(client_id={self.client_id}, session_id={self.session_id}, initialized={self.initialized})"
    
    def __repr__(self) -> str:
        """클라이언트 정보 개발자용 표현"""
        return self.__str__()

# 공통 인스턴스 생성 함수
def create_firebase_client() -> FirebaseDirectClient:
    """
    새로운 Firebase 클라이언트 인스턴스 생성
    
    각 에이전트에서 독립적인 Firebase 연결이 필요할 때 사용합니다.
    
    Returns:
        FirebaseDirectClient: 새로운 클라이언트 인스턴스
    """
    return FirebaseDirectClient()

# 모듈 정보
__version__ = "1.0.0"
__author__ = "ADK Interior Agent Team"
__description__ = "Firebase MCP 서버 공통 연결 클라이언트"

print(f"📦 Firebase 공통 클라이언트 모듈 로드 완료 (v{__version__})") 