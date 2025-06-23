"""
주소 관리 전용 에이전트 - Firebase MCP 직접 HTTP 요청 방식
"""

import asyncio
import json
import aiohttp
import uuid
from datetime import datetime
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.genai.types import FunctionDeclaration, Schema, Type

class FirebaseDirectClient:
    """Firebase MCP 서버에 직접 HTTP 요청을 보내는 클라이언트 - simple_api_server.py 방식 참고"""
    
    def __init__(self):
        self.server_url = "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"
        self.session_id = None
        self.initialized = False
    
    async def _parse_sse_response(self, response) -> dict:
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
            
            print(f"⚠️ SSE 응답에서 JSON 데이터를 찾을 수 없습니다: {content}")
            return {"error": "No valid JSON data in SSE response"}
            
        except Exception as e:
            print(f"❌ SSE 응답 파싱 오류: {e}")
            return {"error": f"SSE parsing error: {str(e)}"}
    
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Firebase MCP 도구 직접 호출 - simple_api_server.py와 동일한 방식"""
        
        print(f"🔥 Firebase MCP 요청: {tool_name} - {arguments}")
        
        # simple_api_server.py에서 사용하는 방식과 동일하게 구현
        async with aiohttp.ClientSession() as session:
            try:
                # Firebase MCP 서버 초기화 (simple_api_server.py 방식)
                init_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "mcp-client",
                            "version": "1.0.0"
                        }
                    }
                }
                
                print("🔥 Firebase MCP 초기화 시도...")
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
                    print(f"🔥 MCP 초기화 응답: {init_response.status} - {init_text[:200]}")
                    
                    if init_response.status == 200:
                        # 세션 ID 추출 및 저장
                        self.session_id = init_response.headers.get('mcp-session-id')
                        if not self.session_id:
                            self.session_id = str(uuid.uuid4())
                        print(f"🔥 MCP 세션 ID 설정: {self.session_id}")
                    else:
                        return {"error": f"MCP 초기화 실패: {init_response.status}"}
                
                # 도구 호출 요청
                tool_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                print(f"🔥 Firebase MCP 도구 호출: {tool_name}")
                
                # 헤더 구성 (세션 ID 포함)
                tool_headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
                if self.session_id:
                    tool_headers["mcp-session-id"] = self.session_id
                    print(f"🔥 세션 ID 헤더 추가: {self.session_id}")
                
                async with session.post(
                    self.server_url,
                    json=tool_payload,
                    headers=tool_headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as tool_response:
                    
                    response_text = await tool_response.text()
                    print(f"🔥 Firebase MCP 도구 응답 상태: {tool_response.status}")
                    print(f"🔥 Firebase MCP 도구 응답 내용: {response_text[:500]}")
                    
                    if tool_response.status == 200:
                        try:
                            # Content-Type에 따라 다르게 처리
                            content_type = tool_response.headers.get('Content-Type', '')
                            if 'text/event-stream' in content_type:
                                print("🔥 SSE 응답 감지 - 파싱 시작...")
                                result = await self._parse_sse_response(tool_response)
                            else:
                                result = await tool_response.json()
                            
                            if "error" in result:
                                error_msg = result["error"].get("message", "Unknown error")
                                print(f"❌ Firebase MCP 에러: {error_msg}")
                                return {"error": error_msg}
                            
                            if "result" in result:
                                print(f"✅ Firebase MCP 성공: {tool_name}")
                                return result["result"]
                            else:
                                print(f"⚠️ Firebase MCP 응답에 result 없음: {result}")
                                return result
                                
                        except Exception as json_error:
                            print(f"❌ JSON 파싱 에러: {json_error}")
                            return {"error": f"JSON parsing failed: {str(json_error)}"}
                    else:
                        print(f"❌ HTTP 에러 {tool_response.status}: {response_text}")
                        return {"error": f"HTTP {tool_response.status}: {response_text[:200]}"}
                        
            except asyncio.TimeoutError:
                print(f"❌ Firebase MCP 타임아웃: {tool_name}")
                return {"error": "Request timeout"}
            except Exception as e:
                print(f"❌ Firebase MCP 연결 에러: {e}")
                return {"error": f"Connection error: {str(e)}"}

def create_address_agent():
    """주소 관리 전용 에이전트 생성 - 직접 HTTP 요청 방식"""
    try:
        print("Firebase MCP 직접 HTTP 연결 방식으로 에이전트 생성 중...")
        
        # Firebase 클라이언트 인스턴스
        firebase_client = FirebaseDirectClient()
        
        # 1. 컬렉션 목록 조회 함수
        async def firestore_list_collections():
            """Firestore 컬렉션 목록 조회"""
            print("🔥 Firebase 컬렉션 목록 조회 중...")
            result = await firebase_client.call_tool("firestore_list_collections", {})
            return result

        # 2. 문서 목록 조회 함수
        async def firestore_list_documents(collection: str, limit: int = 10):
            """Firestore 문서 목록 조회"""
            print(f"🔥 Firebase {collection} 컬렉션 문서 조회 중...")
            result = await firebase_client.call_tool("firestore_list_documents", {
                "collection": collection,
                "limit": limit
            })
            return result

        # 3. 문서 추가 함수
        async def firestore_add_document(collection: str, data: dict):
            """Firestore 문서 추가"""
            print(f"🔥 Firebase {collection} 컬렉션에 문서 추가 중...")
            
            # 타임스탬프 추가
            if isinstance(data, dict):
                data["createdAt"] = datetime.now().isoformat()
                data["updatedAt"] = datetime.now().isoformat()
            
            result = await firebase_client.call_tool("firestore_add_document", {
                "collection": collection,
                "data": data
            })
            return result

        # 4. 문서 업데이트 함수
        async def firestore_update_document(collection: str, document_id: str, data: dict):
            """Firestore 문서 업데이트"""
            print(f"🔥 Firebase {collection}/{document_id} 문서 업데이트 중...")
            
            # 업데이트 타임스탬프 추가
            if isinstance(data, dict):
                data["updatedAt"] = datetime.now().isoformat()
            
            result = await firebase_client.call_tool("firestore_update_document", {
                "collection": collection,
                "documentId": document_id,
                "data": data
            })
            return result

        # 5. 문서 조회 함수 (상세 조회용)
        async def firestore_get_document(collection: str, document_id: str):
            """Firestore 특정 문서 상세 조회"""
            print(f"🔥 Firebase {collection}/{document_id} 문서 상세 조회 중...")
            
            result = await firebase_client.call_tool("firestore_get_document", {
                "collection": collection,
                "id": document_id
            })
            return result

        # 6. 문서 삭제 함수
        async def firestore_delete_document(collection: str, document_id: str):
            """Firestore 문서 삭제"""
            print(f"🔥 Firebase {collection}/{document_id} 문서 삭제 중...")
            
            result = await firebase_client.call_tool("firestore_delete_document", {
                "collection": collection,
                "documentId": document_id
            })
            return result

        # Firebase 도구들 생성
        tools = [
            FunctionTool(firestore_list_collections),
            FunctionTool(firestore_list_documents),
            FunctionTool(firestore_get_document),
            FunctionTool(firestore_add_document),
            FunctionTool(firestore_update_document),
            FunctionTool(firestore_delete_document)
        ]
        
        print(f"✅ Firebase 직접 HTTP 도구 {len(tools)}개 생성 완료")
        
        agent = Agent(
            model='gemini-2.5-flash-preview-05-20',
            name='address_manager',
            description="Firebase 직접 HTTP 연결을 통해 주소 정보를 관리하는 전문 에이전트입니다.",
            instruction='''당신은 Firebase Firestore를 직접 HTTP 요청으로 관리하는 전문 AI 어시스턴트입니다.

## 🔥 CRITICAL: 즉시 도구 사용 규칙!

### ⚡ 키워드 감지 시 즉시 실행:

**"주소 조회", "주소", "address" 언급 시:**
→ 즉시 firestore_list_documents(collection="addressesJson", limit=50) 실행

**"컬렉션", "목록" 언급 시:**
→ 즉시 firestore_list_collections() 실행

**"schedules" 언급 시:**
→ 즉시 firestore_list_documents(collection="schedules", limit=20) 실행

### 🧠 컨텍스트 인식 및 참조 처리:

**컨텍스트 정보 형식 인식:**
```
[컨텍스트 정보]
이전 대화: [대화 내용]
최근 결과: [조회 결과]

[현재 요청]
[실제 요청]
```

**참조 표현 처리:**
- "방금 조회한 결과" → 최근 결과에서 참조
- "첫 번째 문서" → 목록의 첫 번째 항목 식별
- "두 번째", "세 번째" → 해당 순서의 항목
- "마지막 문서" → 목록의 마지막 항목

**상세 조회 로직:**
1. 컨텍스트에서 이전 조회 결과 파싱
2. 요청된 순서(첫 번째, 두 번째 등) 식별
3. 해당 문서의 ID 추출
4. firestore_get_document 또는 상세 정보 조회

### 🚫 절대 금지:
- ❌ "몇 개를 조회할까요?" 같은 질문 금지
- ❌ 추가 정보 요청 금지
- ❌ 도구 사용 없이 텍스트로만 응답 금지
- ❌ "이전 조회 결과는 저장되지 않습니다" 응답 금지

### ✅ 올바른 동작:
1. 요청에서 컨텍스트 정보 파싱
2. 참조 표현 인식 (방금, 첫 번째 등)
3. 컨텍스트 기반 적절한 도구 실행
4. 결과를 명확하게 한국어로 설명

### 🎯 기본 설정:
- 주소 관련 요청은 무조건 addressesJson 컬렉션에서 조회
- limit 기본값: 50개 (충분한 데이터 표시)
- 컨텍스트 없으면 새로운 조회 수행
- 에러 시에도 재시도 또는 대안 제시

### 📝 데이터 구조 (addressesJson):
```json
{
    "id": "문서ID",
    "description": "주소 설명",
    "dataJson": "상세 정보 JSON 문자열"
}
```

### 💡 참조 처리 예시:

**요청**: "방금 조회한 결과에서 첫 번째 문서 상세 보여줘"
**처리**:
1. 컨텍스트에서 이전 addressesJson 조회 결과 확인
2. 첫 번째 문서 ID 추출 (예: "1734608505871")
3. 해당 문서의 상세 정보 표시 (description + dataJson 파싱)

**핵심**: 컨텍스트 정보를 적극 활용하여 이전 결과를 기반으로 추가 작업을 수행하세요!

모든 응답은 한국어로 해주세요.''',
            tools=tools
        )
        
        print(f"✅ 주소 관리 에이전트 '{agent.name}' 생성 완료 (직접 HTTP 방식)")
        return agent
        
    except Exception as e:
        print(f"❌ Firebase 직접 HTTP 연결 실패: {e}")
        print("기본 에이전트로 폴백합니다.")
        
        # 기본 에이전트로 폴백
        return Agent(
            model='gemini-2.5-flash-preview-05-20',
            name='address_manager_fallback',
            description="주소 정보를 관리하는 폴백 에이전트입니다.",
            instruction='''주소 관리 전문 AI 어시스턴트입니다. 

현재 Firebase 연결에 문제가 있어 기본 모드로 동작합니다.
주소 관련 질문에 대해 일반적인 조언과 안내를 제공하겠습니다.

주소 관리 기능:
1. 주소 형식 안내
2. 주소 입력 방법 설명  
3. 주소 관리 팁 제공
4. 인테리어 프로젝트에서의 주소 활용 방법

모든 응답은 한국어로 해주세요.'''
        )

# ADK web에서 사용할 에이전트 인스턴스
print("=== 주소 관리 에이전트 직접 HTTP 초기화 시작 ===")
address_agent = create_address_agent()
print(f"=== 주소 관리 에이전트 초기화 완료: {address_agent.name} ===") 