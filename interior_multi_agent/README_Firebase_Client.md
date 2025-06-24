# 🔥 Firebase 공통 클라이언트 모듈 가이드

## 📋 개요

이 문서는 `firebase_client.py` 공통 모듈의 역할과 사용법을 설명합니다.

### 🎯 모듈의 목적

`FirebaseDirectClient`는 **Firebase MCP 서버와의 HTTP 통신을 전담**하는 공통 클라이언트입니다. 모든 ADK 에이전트가 이 모듈을 통해 Firebase 기능을 사용할 수 있습니다.

## 🏗️ 아키텍처

### 변경 전 (중복 구조)
```
📋 address_management_agent.py
├── FirebaseDirectClient 클래스 (159줄)
├── 주소 관리 로직
└── ...

📅 schedule_management_agent.py (예정)
├── FirebaseDirectClient 클래스 (159줄) ❌ 중복!
├── 스케줄 관리 로직
└── ...
```

### 변경 후 (공통 모듈)
```
🔌 firebase_client.py (공통 모듈)
├── FirebaseDirectClient 클래스
├── 연결 관리
├── 에러 처리
└── 로깅

📋 address_management_agent.py
├── from .firebase_client import FirebaseDirectClient ✅
├── 주소 관리 로직 (단일 책임)
└── ...

📅 schedule_management_agent.py (예정)
├── from .firebase_client import FirebaseDirectClient ✅ 재사용!
├── 스케줄 관리 로직 (단일 책임)
└── ...
```

## 🔧 주요 기능

### 1. Firebase MCP 서버 연결
- **URL**: `https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp`
- **프로토콜**: JSON-RPC 2.0
- **세션 관리**: 자동 세션 ID 생성 및 관리

### 2. 지원하는 Firebase 도구
- `firestore_list_collections`: 컬렉션 목록 조회
- `firestore_list_documents`: 문서 목록 조회
- `firestore_get_document`: 특정 문서 조회
- `firestore_add_document`: 문서 추가
- `firestore_update_document`: 문서 업데이트
- `firestore_delete_document`: 문서 삭제

### 3. 에러 처리 및 로깅
- 타임아웃 처리 (30초)
- 연결 실패 대응
- SSE 응답 파싱
- 상세 디버깅 로그

## 🔌 사용 방법

### 기본 사용법
```python
from .firebase_client import FirebaseDirectClient

# 클라이언트 생성
firebase_client = FirebaseDirectClient()

# 도구 호출
result = await firebase_client.call_tool("firestore_list_documents", {
    "collection": "addressesJson",
    "limit": 10
})
```

### 에이전트에서 사용
```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from .firebase_client import FirebaseDirectClient

def create_my_agent():
    # 공통 클라이언트 사용
    firebase_client = FirebaseDirectClient()
    
    # 래퍼 함수 생성
    async def my_firestore_function(collection: str):
        return await firebase_client.call_tool("firestore_list_documents", {
            "collection": collection,
            "limit": 20
        })
    
    # 에이전트 생성
    agent = Agent(
        name='my_agent',
        tools=[FunctionTool(my_firestore_function)]
    )
    
    return agent
```

## 📊 로그 분석

### 정상 동작 시 로그
```
📦 Firebase 공통 클라이언트 모듈 로드 완료 (v1.0.0)
🔥 Firebase 클라이언트 생성 완료 (ID: dc29440d)
🔥 [dc29440d] Firebase MCP 초기화 시도...
🔥 [dc29440d] MCP 초기화 응답: 200 - ...
🔥 [dc29440d] MCP 세션 ID 설정: adk-dc29440d-1699...
🔥 [dc29440d] Firebase MCP 도구 호출: firestore_list_documents
✅ [dc29440d] Firebase MCP 성공: firestore_list_documents
```

### 에러 발생 시 로그
```
❌ [dc29440d] Firebase MCP 연결 에러: Connection error
❌ [dc29440d] Firebase MCP 타임아웃: firestore_list_documents
❌ [dc29440d] HTTP 에러 400: Bad Request
```

## 🎯 장점 분석

### 1. 코드 중복 제거 (DRY 원칙)
- **변경 전**: 각 에이전트마다 159줄의 연결 코드 중복
- **변경 후**: 한 곳에서 관리, 모든 에이전트가 재사용

### 2. 유지보수 중앙화
- **URL 변경**: `firebase_client.py` 한 파일만 수정
- **에러 처리 개선**: 모든 에이전트에 자동 적용
- **새 기능 추가**: 한 번에 모든 에이전트가 사용 가능

### 3. 일관성 보장
- 모든 에이전트가 동일한 연결 방식 사용
- 동일한 에러 처리 로직
- 통일된 로깅 형식

### 4. 테스트 용이성
```python
# 공통 모듈 단위 테스트
def test_firebase_client():
    client = FirebaseDirectClient()
    # 연결 테스트만 한 번 작성

# 에이전트 테스트 (Firebase 모킹)
@mock.patch('firebase_client.FirebaseDirectClient')
def test_address_agent(mock_client):
    # 비즈니스 로직만 테스트
```

## 🚀 확장 계획

### 1. 새로운 에이전트 추가
```python
# schedule_management_agent.py (예정)
from .firebase_client import FirebaseDirectClient  # ✅ 바로 사용 가능

def create_schedule_agent():
    firebase_client = FirebaseDirectClient()  # 검증된 연결
    # 스케줄 관리 로직만 집중
```

### 2. 새로운 Firebase 기능
```python
# firebase_client.py에 추가
async def batch_call_tools(self, requests):
    """여러 도구를 한 번에 호출"""
    # 모든 에이전트가 자동으로 사용 가능
```

## 🔍 디버깅 가이드

### 연결 문제 해결
1. **서버 상태 확인**
   ```python
   status = await firebase_client.get_server_status()
   print(status)
   ```

2. **로그 분석**
   - 클라이언트 ID로 특정 세션 추적
   - HTTP 상태 코드 확인
   - 에러 메시지 분석

3. **타임아웃 조정**
   ```python
   # firebase_client.py에서 타임아웃 수정
   timeout=aiohttp.ClientTimeout(total=60)  # 30초 → 60초
   ```

## 📝 변경 이력

### v1.0.0 (2024-01-XX)
- ✅ 공통 Firebase 클라이언트 모듈 생성
- ✅ address_management_agent.py 리팩토링
- ✅ 로깅 및 에러 처리 강화
- ✅ 문서화 완료

### 향후 계획
- 🔄 schedule_management_agent.py 생성
- 🔄 배치 요청 기능 추가
- 🔄 캐싱 기능 추가
- 🔄 재시도 로직 강화

## 🤝 기여 가이드

새로운 에이전트를 만들 때:

1. **공통 모듈 사용**
   ```python
   from .firebase_client import FirebaseDirectClient
   ```

2. **단일 책임 원칙**
   - Firebase 연결: `firebase_client.py`가 담당
   - 비즈니스 로직: 각 에이전트가 담당

3. **일관된 에러 처리**
   - 공통 모듈의 에러 응답 형식 사용
   - 적절한 로깅 수준 유지

4. **문서 업데이트**
   - 새 기능 추가 시 README 업데이트
   - 사용 예제 추가

---

## 🔗 관련 파일

- `firebase_client.py`: 공통 클라이언트 모듈
- `address_management_agent.py`: 주소 관리 에이전트 (리팩토링됨)
- `agent_main.py`: 루트 에이전트
- `simple_api_server.py`: FastAPI 서버

## 📞 문의

Firebase 공통 모듈 관련 질문이나 개선 사항이 있으시면 언제든 말씀해 주세요! 