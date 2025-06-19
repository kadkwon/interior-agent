# Firebase MCP-ADK 에이전트 연동 문제 해결 및 개발 가이드

## 📋 목차
1. [문제 상황 요약](#문제-상황-요약)
2. [문제 발생 원인 분석](#문제-발생-원인-분석)
3. [해결 과정](#해결-과정)
4. [최종 해결책](#최종-해결책)
5. [향후 에이전트 개발 가이드](#향후-에이전트-개발-가이드)
6. [프롬프트 작성 가이드](#프롬프트-작성-가이드)

---

## 문제 상황 요약

### 주요 증상
- `simple_api_server.py`에서 "도구 호출 성공" 로그가 지속적으로 출력
- ADK 에이전트가 Firebase MCP 도구를 인식하지 못함
- `httpx.HTTPStatusError: Client error '400 Bad Request'` 에러 발생

### 영향 범위
- 주소 관리 에이전트의 Firebase 데이터베이스 접근 불가
- 루트 에이전트와 서브 에이전트 간 작업 위임 실패

---

## 문제 발생 원인 분석

### 1. 헬스체크 로그 문제 🔍
**원인**: `/health` 엔드포인트가 Firebase 연결 상태를 확인하기 위해 실제 도구를 호출
```python
# simple_api_server.py의 헬스체크
async def health_check():
    try:
        # 실제 Firebase 도구 호출 → 성공 로그 출력
        result = await mcp_toolset.call_tool(
            "firestore_list_collections", 
            {"database_id": "(default)"}
        )
        return {"status": "healthy", "firebase": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "firebase": "disconnected"}
```

**왜 문제인가?**: 
- 모니터링 시스템이나 브라우저가 주기적으로 `/health`를 호출
- 매번 실제 Firebase 도구가 실행되어 불필요한 로그 생성
- 시스템 리소스 낭비

### 2. ADK 임포트 에러 ❌
**원인**: 잘못된 클래스 임포트
```python
# 잘못된 임포트 (존재하지 않는 클래스)
from google.adk.tools.tool import tool

# 올바른 임포트
from google.adk.tools import FunctionTool
```

**왜 발생했나?**: 
- ADK 라이브러리의 실제 구조와 문서/예제의 차이
- Python 패키지 구조에 대한 이해 부족

### 3. MCPToolset SSE 연결 실패 🔌
**원인**: Server-Sent Events(SSE) 방식의 호환성 문제
```python
# 실패한 방식
mcp_toolset = MCPToolset(
    server_url="https://firebase-mcp-server.com/mcp",
    transport_type="sse"
)
```

**왜 실패했나?**:
- Firebase MCP 서버의 SSE 구현과 ADK의 MCPToolset 간 호환성 부족
- HTTP 헤더, 프로토콜 버전 불일치
- 네트워크 환경의 프록시/방화벽 간섭

### 4. 비동기-동기 처리 혼재 ⚡
**원인**: ADK는 동기 함수를 요구하지만 HTTP 클라이언트는 비동기
```python
# ADK 도구는 동기 함수여야 함
def my_tool_function(param):
    return result

# 하지만 HTTP 요청은 비동기
async def http_request():
    async with aiohttp.ClientSession() as session:
        # ...
```

---

## 해결 과정

### 1단계: 문제 진단 🔍
- 로그 분석을 통한 헬스체크 호출 패턴 파악
- ADK 임포트 에러 식별
- MCPToolset 연결 실패 확인

### 2단계: 대안 방식 시도 🔄
- **MCPToolset 대신 직접 HTTP 클라이언트 사용 시도**
- **Streamable HTTP 방식 검토**
- **MCP Inspector를 통한 서버 상태 확인**

### 3단계: 근본적 해결책 구현 ✅
- **직접 HTTP 방식 구현**: aiohttp 기반 FirebaseDirectClient
- **비동기-동기 변환**: asyncio.new_event_loop() 활용
- **FunctionTool 래핑**: 각 Firebase 함수를 ADK 도구로 변환

---

## 최종 해결책

### 핵심 아키텍처
```python
# 직접 HTTP 클라이언트
class FirebaseDirectClient:
    async def call_mcp_tool(self, method, params):
        # JSON-RPC 2.0 직접 호출
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": f"tools/call",
            "params": {"name": method, "arguments": params}
        }
        # aiohttp로 직접 요청

# 비동기-동기 변환
def sync_wrapper(async_func):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

# ADK 도구 등록
firestore_add_tool = FunctionTool(
    name="firestore_add_document",
    description="Firestore에 문서 추가",
    func=sync_firestore_add_document
)
```

### 구현된 도구들
1. `firestore_list_collections` - 컬렉션 목록 조회
2. `firestore_list_documents` - 문서 목록 조회  
3. `firestore_add_document` - 문서 추가
4. `firestore_update_document` - 문서 수정
5. `firestore_delete_document` - 문서 삭제

---

## 향후 에이전트 개발 가이드

### ✅ 올바른 개발 절차

#### 1. 환경 설정 확인
```bash
# 필수 패키지 설치 확인
pip install google-adk aiohttp
```

#### 2. 임포트 구문 검증
```python
# ✅ 올바른 임포트
from google.adk.tools import FunctionTool
from google.adk.agents import Agent

# ❌ 잘못된 임포트 (이런 것들 피하기)
from google.adk.tools.tool import tool  # 존재하지 않음
from google.adk.tools.function import FunctionTool  # 잘못된 경로
```

#### 3. 외부 서비스 연동 패턴
```python
# 1) 직접 HTTP 클라이언트 구현
class ExternalServiceClient:
    def __init__(self, base_url, timeout=30):
        self.base_url = base_url
        self.timeout = timeout
    
    async def call_api(self, endpoint, data):
        # 실제 HTTP 호출 구현
        pass

# 2) 비동기-동기 변환 유틸리티
def make_sync(async_func):
    def sync_wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
    return sync_wrapper

# 3) ADK 도구로 래핑
def create_tool(name, description, async_func):
    sync_func = make_sync(async_func)
    return FunctionTool(
        name=name,
        description=description,
        func=sync_func
    )
```

#### 4. 에러 처리 패턴
```python
async def safe_api_call(client, method, params):
    try:
        result = await client.call_api(method, params)
        return {"success": True, "data": result}
    except aiohttp.ClientError as e:
        return {"success": False, "error": f"네트워크 에러: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"예상치 못한 에러: {str(e)}"}
```

---

## 프롬프트 작성 가이드

### 🎯 에이전트 생성 시 필수 프롬프트 템플릿

#### 기본 구조 요청
```
새로운 [에이전트명] 에이전트를 만들어주세요.

요구사항:
1. google.adk.tools.FunctionTool을 사용해서 도구 생성
2. 외부 서비스는 aiohttp로 직접 HTTP 호출
3. 비동기 함수는 asyncio.new_event_loop()로 동기화
4. 모든 도구는 FunctionTool로 래핑
5. 에러 처리 포함

기능:
- [구체적인 기능 1]
- [구체적인 기능 2]
- [구체적인 기능 3]

외부 연동:
- 서버 URL: [URL]
- 필요한 API: [API 목록]
```

#### 세부 기술 명세
```
기술 요구사항:
1. 임포트: from google.adk.tools import FunctionTool 사용
2. HTTP 클라이언트: aiohttp.ClientSession 사용
3. 비동기 처리: asyncio.new_event_loop() 패턴 적용
4. 에러 처리: try-except로 네트워크 에러 처리
5. 타임아웃: 30초 설정
6. 로깅: 작업 성공/실패 로그 포함
```

#### 예시 도구 함수 요청
```
다음과 같은 구조로 도구 함수들을 만들어주세요:

async def async_[기능명](param1, param2):
    # HTTP 호출 구현
    # 에러 처리 포함
    # 결과 반환

def sync_[기능명](param1, param2):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_[기능명](param1, param2))
    finally:
        loop.close()

# FunctionTool로 래핑
[기능명]_tool = FunctionTool(
    name="[도구명]",
    description="[상세 설명]",
    func=sync_[기능명]
)
```

### ❌ 피해야 할 프롬프트 패턴

#### 너무 간단한 요청
```
❌ "Firebase 연동 에이전트 만들어줘"
❌ "데이터베이스 접근하는 에이전트 필요해"
❌ "MCP 도구 사용해서 에이전트 생성"
```

#### 구체적이지 않은 요청
```
❌ "외부 API 호출하는 에이전트"
❌ "비동기로 처리하는 에이전트"
❌ "에러 처리 잘 되는 에이전트"
```

### ✅ 권장 프롬프트 패턴

#### 완전한 명세서 스타일
```
✅ [에이전트명] 에이전트 생성 요청

기술 스택:
- ADK Framework (google.adk.tools.FunctionTool)
- aiohttp (HTTP 클라이언트)
- asyncio (비동기-동기 변환)

연동 대상:
- 서비스: [서비스명]
- URL: [정확한 URL]
- 프로토콜: [HTTP/JSON-RPC 등]

구현할 기능:
1. [기능1] - [상세 설명]
2. [기능2] - [상세 설명]
3. [기능3] - [상세 설명]

에러 처리:
- 네트워크 에러 대응
- 타임아웃 처리 (30초)
- 예외 상황 로깅

출력 형식:
- 성공: {"success": True, "data": result}
- 실패: {"success": False, "error": "에러 메시지"}
```

---

## 📚 참고 자료

### 핵심 코드 위치
- `interior_multi_agent/interior_agents/address_management_agent.py` - 성공한 구현체
- `simple_api_server.py` - API 서버 및 헬스체크
- `test_address_query.py` - 테스트 코드

### 외부 자료
- [Google ADK 공식 문서](https://cloud.google.com/adk)
- [aiohttp 공식 문서](https://docs.aiohttp.org/)
- [JSON-RPC 2.0 명세](https://www.jsonrpc.org/specification)

### 트러블슈팅 체크리스트
1. ✅ 올바른 ADK 임포트 사용
2. ✅ 비동기-동기 변환 구현
3. ✅ HTTP 클라이언트 직접 구현
4. ✅ 적절한 에러 처리
5. ✅ 타임아웃 설정
6. ✅ 로깅 구현

---

**📝 작성일**: 2024년  
**📌 버전**: 1.0  
**👨‍💻 대상**: ADK 에이전트 개발자  
**🎯 목적**: Firebase MCP 연동 문제 해결 및 향후 개발 가이드 