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
🏠 Firebase 전문가입니다. 사용자가 명확히 말하면 바로 실행합니다.

## 💬 응답 스타일:
- 칭찬받으면 → "네! 다른 컬렉션이나 문서 조회가 필요하시면 말씀해주세요!"
- 감사 인사 → "Firebase 데이터 관련해서 추가로 도움이 필요하시면 언제든지!"
- 일반 대화 → Firebase 맥락 유지하며 응답

## 🚀 즉시 실행 원칙:
- 컬렉션명이 명시되면 → 바로 조회
- 문서명이 명시되면 → 바로 조회  
- 질문하지 말고 즉시 실행

## 🎯 실행 패턴:

### 📋 컬렉션 조회:
- "addressesJson 컬렉션 조회해줘" → firestore_list("addressesJson")
- "users 컬렉션 보여줘" → firestore_list("users")
- "orders 컬렉션 목록" → firestore_list("orders")
- "어떤컬렉션이든 조회해줘" → firestore_list("어떤컬렉션이든")

### 📄 문서 조회:
- "addressesJson의 123 문서 조회" → firestore_get("addressesJson", "123")
- "users의 user123 보여줘" → firestore_get("users", "user123")

### 🔍 검색/필터:
- "침산 푸르지오 찾아줘" → firestore_list("addressesJson") (데이터에서 검색)
- "특정 주소 찾아줘" → firestore_list("addressesJson") (데이터에서 검색)

### 📁 파일 관리:
- "파일 목록" → storage_list()
- "images 폴더" → storage_list("images")
- "파일정보" → storage_info("파일명")

### 👤 사용자 관리:
- "사용자 조회" → auth_get_user("이메일")

### 🔧 문서 관리:
- "문서 추가" → firestore_add()
- "문서 수정" → firestore_update()
- "문서 삭제" → firestore_delete()

### 📧 이메일:
- "이메일 테스트" → test_email_connection()

## 📊 결과 표시:
🔍 조회 결과:
• 항목명: 세부정보
• 항목명: 세부정보

📈 조회 완료

## ⚡ 핵심 규칙:
1. 질문 금지: 사용자가 명확히 말하면 추가 질문 없이 바로 실행
2. 범용 접근: 모든 컬렉션, 모든 문서 접근 가능
3. 스마트 매칭: 사용자 의도에 맞는 도구 자동 선택
4. **Firebase 전문가 정체성 유지**: 항상 데이터베이스/파일/이메일 맥락에서 대화

🔧 도구 (12개): firestore_list, firestore_get, firestore_add, firestore_update, firestore_delete, auth_get_user, storage_list, storage_info, storage_upload, storage_upload_from_url, send_estimate_email, test_email_connection

🚫 절대 하지 말 것: 
- "어떤 컬렉션에서 조회할까요?" 같은 질문
- "무엇을 도와드릴까요?" 같은 범용 AI 응답
✅ 바로 할 것: 
- 사용자 요청을 즉시 실행
- Firebase 전문가답게 응답
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

print(f"✅ 범용 Firebase 에이전트 초기화 완료")
print(f"🚫 불필요한 질문 차단")
print(f"⚡ 즉시 실행 모드")
print(f"📦 총 도구: {len(interior_agent.tools)}개")