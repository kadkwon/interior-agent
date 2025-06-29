"""
🏠 인테리어 Firebase 에이전트 - AI 스마트 번역 + 즉시 실행 버전
"""

from typing import Optional, List
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .mcp_client import firebase_client, email_client

# 🔧 하드코딩 매핑 제거 - AI가 알아서 추론!

# 컬렉션 목록 조회 도구 추가
async def firestore_list_collections():
    """Firestore 루트 컬렉션 목록 조회"""
    return await firebase_client.call_tool("firestore_list_collections", {})

# Firestore 도구들 (6개) - 컬렉션 목록 조회 추가
async def firestore_list(collection: str, limit: Optional[int] = None):
    """컬렉션 문서 목록 조회 - AI 스마트 매칭"""
    params = {"collection": collection}
    if limit is not None:
        params["limit"] = limit
    else:
        params["limit"] = 20
    return await firebase_client.call_tool("firestore_list_documents", params)

async def firestore_get(collection: str, document_id: str):
    """특정 문서 조회"""
    return await firebase_client.call_tool("firestore_get_document", {
        "collection": collection,
        "id": document_id
    })

async def firestore_add(collection: str, data: dict):
    """문서 추가"""
    return await firebase_client.call_tool("firestore_add_document", {
        "collection": collection,
        "data": data
    })

async def firestore_update(collection: str, document_id: str, data: dict):
    """문서 수정"""
    return await firebase_client.call_tool("firestore_update_document", {
        "collection": collection,
        "id": document_id,
        "data": data
    })

async def firestore_delete(collection: str, document_id: str):
    """문서 삭제"""
    return await firebase_client.call_tool("firestore_delete_document", {
        "collection": collection,
        "id": document_id
    })

# Auth 도구 (1개)
async def auth_get_user(identifier: str):
    """사용자 정보 조회 (이메일 또는 UID)"""
    return await firebase_client.call_tool("auth_get_user", {
        "identifier": identifier
    })

# Storage 도구들 (4개)
async def storage_list(directory_path: Optional[str] = None):
    """파일 목록 조회"""
    params = {}
    if directory_path:
        params["directoryPath"] = directory_path
    return await firebase_client.call_tool("storage_list_files", params)

async def storage_info(file_path: str):
    """파일 정보 조회"""
    return await firebase_client.call_tool("storage_get_file_info", {
        "filePath": file_path
    })

async def storage_upload(file_path: str, content: str, content_type: Optional[str] = None):
    """파일 업로드"""
    params = {"filePath": file_path, "content": content}
    if content_type:
        params["contentType"] = content_type
    return await firebase_client.call_tool("storage_upload", params)

async def storage_upload_from_url(file_path: str, url: str, content_type: Optional[str] = None):
    """URL에서 파일 업로드"""
    params = {"filePath": file_path, "url": url}
    if content_type:
        params["contentType"] = content_type
    return await firebase_client.call_tool("storage_upload_from_url", params)

# 이메일 도구들 (2개)
async def send_estimate_email(email: str, address: str, process_data: List[dict]):
    """견적서 이메일 전송"""
    return await email_client.call_tool("send_estimate_email", {
        "email": email,
        "address": address,
        "process_data": process_data
    })

async def test_email_connection():
    """이메일 연결 테스트"""
    return await email_client.call_tool("test_connection", {"random_string": "test"})

# AI 스마트 Firebase 에이전트 - 즉시 실행 모드
interior_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='interior_firebase_agent',
    instruction='''
🏠 Firebase 전문가입니다. 컬렉션을 찾으면 바로 실행합니다!

## 🚀 즉시 실행 원칙 (절대 규칙):

### 📋 바로 실행해야 하는 패턴:
- "주소 확인해줘" → firestore_list_collections() → addressesJson 찾음 → firestore_list("addressesJson") 즉시 실행
- "주소 리스트 보여줘" → firestore_list_collections() → addressesJson 찾음 → firestore_list("addressesJson") 즉시 실행  
- "스케쥴 조회해줘" → firestore_list_collections() → schedules 찾음 → firestore_list("schedules") 즉시 실행
- "견적서 보여줘" → firestore_list_collections() → estimateVersionsV3 찾음 → firestore_list("estimateVersionsV3") 즉시 실행

## 🧠 AI 스마트 컬렉션 매칭:

### 📋 2단계 처리 과정:
1. **컬렉션 목록 확인**: firestore_list_collections() 먼저 실행
2. **적절한 컬렉션 선택 후 즉시 실행**: 
   - "주소" 관련 → addressesJson 선택 → firestore_list("addressesJson") 바로 실행
   - "스케쥴" 관련 → schedules 선택 → firestore_list("schedules") 바로 실행
   - "견적서" 관련 → estimateVersionsV3 선택 → firestore_list("estimateVersionsV3") 바로 실행

### 🔧 지능적 한글 해석:
- "주소" / "주소리스트" / "주소확인" → addressesJson
- "스케쥴" / "일정" / "스케줄" → schedules  
- "견적서" / "견적" → estimateVersionsV3
- "사용자" / "유저" → users
- "결제" → payments
- "주문" → orders

## 📊 결과 표시:
🔍 조회 결과:
• 항목명: 세부정보
• 항목명: 세부정보

📈 조회 완료

## ⚡ 핵심 규칙 (절대 준수):
1. **컬렉션을 찾으면 즉시 실행**: "어떤 작업을 해드릴까요?" 절대 금지
2. **2단계 처리**: 컬렉션 목록 확인 → 적절한 컬렉션 선택 → 바로 실행
3. **질문 금지**: 컬렉션을 찾으면 추가 질문 없이 바로 데이터 조회
4. **스마트 추론**: 실제 컬렉션 목록을 보고 가장 적절한 것 선택

🚫 절대 하지 말 것: 
- "어떤 작업을 해드릴까요?" 같은 질문
- 컬렉션을 찾고도 실행하지 않는 행위
✅ 반드시 할 것: 
- 컬렉션 찾으면 바로 firestore_list() 실행
- 데이터 조회 후 결과 표시

🔧 도구 (13개): firestore_list_collections, firestore_list, firestore_get, firestore_add, firestore_update, firestore_delete, auth_get_user, storage_list, storage_info, storage_upload, storage_upload_from_url, send_estimate_email, test_email_connection

🎯 실행 예시:
- 사용자: "주소 리스트 보여줘"
- AI: firestore_list_collections() 실행
- AI: addressesJson 컬렉션 발견
- AI: firestore_list("addressesJson") 즉시 실행
- AI: 결과 표시 (질문하지 않음!)
    ''',
    tools=[
        FunctionTool(firestore_list_collections),
        FunctionTool(firestore_list),
        FunctionTool(firestore_get),
        FunctionTool(firestore_add),
        FunctionTool(firestore_update),
        FunctionTool(firestore_delete),
        FunctionTool(auth_get_user),
        FunctionTool(storage_list),
        FunctionTool(storage_info),
        FunctionTool(storage_upload),
        FunctionTool(storage_upload_from_url),
        FunctionTool(send_estimate_email),
        FunctionTool(test_email_connection)
    ]
)

print(f"✅ AI 스마트 Firebase 에이전트 초기화 완료")
print(f"🚫 불필요한 질문 완전 차단")
print(f"⚡ 컬렉션 찾으면 즉시 실행 모드")
print(f"📦 총 도구: {len(interior_agent.tools)}개")
print(f"🎯 하드코딩 매핑 제거 - AI가 알아서 추론!")