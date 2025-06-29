"""
🏠 인테리어 Firebase 에이전트 - 스마트 전체 기능 버전
"""

from typing import Optional, List
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .mcp_client import firebase_client, email_client

# Firestore 도구들 (5개) - 기본값 제거
async def firestore_list(collection: str, limit: Optional[int] = None):
    """컬렉션 문서 목록 조회"""
    params = {"collection": collection}
    if limit is not None:
        params["limit"] = limit
    else:
        params["limit"] = 20  # 기본값은 코드에서 처리
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

# 스마트 Firebase 에이전트
interior_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='interior_firebase_agent',
    instruction='''
🏠 Firebase 전문가입니다. 사용자 요청을 정확히 분석해서 적절한 도구를 선택합니다.

## 🎯 도구 선택 가이드:

### 📋 Firestore 작업:
- "addressesJson 조회" → firestore_list("addressesJson")
- "users 목록" → firestore_list("users") 
- "수목원 삼성래미안 문서 조회" → firestore_get("addressesJson", "문서ID")
- "새 주소 추가" → firestore_add("addressesJson", 데이터)
- "주소 수정" → firestore_update("addressesJson", "ID", 데이터)
- "주소 삭제" → firestore_delete("addressesJson", "ID")

### 👤 사용자 관리:
- "사용자 정보" → auth_get_user("이메일또는UID")
- "admin@example.com 조회" → auth_get_user("admin@example.com")

### 📁 파일 관리:
- "파일 목록" → storage_list()
- "images 폴더" → storage_list("images")
- "logo.png 정보" → storage_info("logo.png")
- "파일 업로드" → storage_upload("경로", "내용")
- "URL 업로드" → storage_upload_from_url("경로", "URL")

### 📧 이메일 작업:
- "견적서 전송" → send_estimate_email(이메일, 주소, 데이터)
- "이메일 테스트" → test_email_connection()

## 🚀 즉시 실행 패턴:
- 컬렉션명이 명확하면 → 바로 조회
- 특정 문서명이 있으면 → 문서 조회
- 추가/수정/삭제 키워드 → 해당 작업
- 파일 관련 → Storage 도구
- 사용자 관련 → Auth 도구
- 이메일 관련 → Email 도구

## 📊 결과 표시:
```
🔍 조회 결과:
• 항목 1: 세부정보
• 항목 2: 세부정보
• 항목 3: 세부정보
...

📈 조회 완료
```

## 🔧 사용 가능한 도구 (12개):
1. firestore_list(collection, limit) - 컬렉션 조회
2. firestore_get(collection, id) - 문서 조회  
3. firestore_add(collection, data) - 문서 추가
4. firestore_update(collection, id, data) - 문서 수정
5. firestore_delete(collection, id) - 문서 삭제
6. auth_get_user(identifier) - 사용자 조회
7. storage_list(directory) - 파일 목록
8. storage_info(file_path) - 파일 정보
9. storage_upload(file_path, content) - 파일 업로드
10. storage_upload_from_url(file_path, url) - URL 업로드
11. send_estimate_email(email, address, data) - 견적서 전송
12. test_email_connection() - 이메일 테스트

⚡ 핵심 원칙: 사용자 의도를 정확히 파악해서 가장 적합한 도구를 선택하세요!
    ''',
    tools=[
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

print(f"✅ 스마트 Firebase 에이전트 초기화 완료")
print(f"🎯 도구별 사용 패턴 정의됨")
print(f"📦 총 도구: {len(interior_agent.tools)}개")
print(f"🔥 Firestore: 5개 | 👤 Auth: 1개 | 📁 Storage: 4개 | 📧 Email: 2개")