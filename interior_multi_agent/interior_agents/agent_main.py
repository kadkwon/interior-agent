"""
🏠 인테리어 Firebase 에이전트 - 스마트 전체 기능 + 오타 보정 버전
"""

from typing import Optional, List
import difflib
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .mcp_client import firebase_client, email_client

# 🔧 컬렉션명 매핑 시스템
COLLECTION_MAPPINGS = {
    # 한글 → 영문
    "주소": "addressesJson",
    "주소컬렉션": "addressesJson", 
    "주소목록": "addressesJson",
    "스케쥴": "schedules",
    "스케줄": "schedules",
    "일정": "schedules",
    "견적서": "estimateVersionsV3",
    "견적": "estimateVersionsV3",
    "사용자": "users",
    "유저": "users",
    "결제": "payments",
    "주문": "orders",
    
    # 일반적인 오타들
    "schdules": "schedules",
    "shcedules": "schedules", 
    "shedules": "schedules",
    "adressesJson": "addressesJson",
    "addresJson": "addressesJson",
    "estimateVersionV3": "estimateVersionsV3",
    "estimateVersionsv3": "estimateVersionsV3",
    "usres": "users",
    "user": "users"
}

# 실제 컬렉션명 목록 (예시)
KNOWN_COLLECTIONS = [
    "addressesJson", "schedules", "estimateVersionsV3", "users", 
    "payments", "orders", "workOrders", "materials", "companies"
]

def normalize_collection_name(user_input: str) -> str:
    """컬렉션명 정규화 - 오타 보정 및 한글 매핑"""
    # 1. 공백 제거 및 소문자화
    cleaned = user_input.strip().replace(" ", "").replace("컬렉션", "").replace("컬랙션", "")
    
    # 2. 직접 매핑 확인
    if cleaned in COLLECTION_MAPPINGS:
        result = COLLECTION_MAPPINGS[cleaned]
        print(f"🔄 컬렉션명 매핑: '{user_input}' → '{result}'")
        return result
    
    # 3. 대소문자 구분 없이 매핑 확인
    cleaned_lower = cleaned.lower()
    for key, value in COLLECTION_MAPPINGS.items():
        if cleaned_lower == key.lower():
            result = value
            print(f"🔄 컬렉션명 매핑: '{user_input}' → '{result}'")
            return result
    
    # 4. 유사도 기반 오타 보정
    best_match = difflib.get_close_matches(cleaned, KNOWN_COLLECTIONS, n=1, cutoff=0.6)
    if best_match:
        result = best_match[0]
        print(f"🔧 오타 보정: '{user_input}' → '{result}' (유사도 매칭)")
        return result
    
    # 5. 매핑 키와 유사도 확인
    mapping_keys = list(COLLECTION_MAPPINGS.keys())
    key_match = difflib.get_close_matches(cleaned, mapping_keys, n=1, cutoff=0.6)
    if key_match:
        result = COLLECTION_MAPPINGS[key_match[0]]
        print(f"🔧 오타 보정: '{user_input}' → '{result}' (매핑 키 유사도)")
        return result
    
    # 6. 원본 반환
    print(f"📝 컬렉션명 그대로 사용: '{user_input}'")
    return user_input

# Firestore 도구들 (5개) - 오타 보정 기능 추가
async def firestore_list(collection: str, limit: Optional[int] = None):
    """컬렉션 문서 목록 조회 - 오타 보정 및 한글 지원"""
    # 컬렉션명 정규화
    normalized_collection = normalize_collection_name(collection)
    
    params = {"collection": normalized_collection}
    if limit is not None:
        params["limit"] = limit
    else:
        params["limit"] = 20
    return await firebase_client.call_tool("firestore_list_documents", params)

async def firestore_get(collection: str, document_id: str):
    """특정 문서 조회 - 오타 보정 및 한글 지원"""
    normalized_collection = normalize_collection_name(collection)
    return await firebase_client.call_tool("firestore_get_document", {
        "collection": normalized_collection,
        "id": document_id
    })

async def firestore_add(collection: str, data: dict):
    """문서 추가 - 오타 보정 및 한글 지원"""
    normalized_collection = normalize_collection_name(collection)
    return await firebase_client.call_tool("firestore_add_document", {
        "collection": normalized_collection,
        "data": data
    })

async def firestore_update(collection: str, document_id: str, data: dict):
    """문서 수정 - 오타 보정 및 한글 지원"""
    normalized_collection = normalize_collection_name(collection)
    return await firebase_client.call_tool("firestore_update_document", {
        "collection": normalized_collection,
        "id": document_id,
        "data": data
    })

async def firestore_delete(collection: str, document_id: str):
    """문서 삭제 - 오타 보정 및 한글 지원"""
    normalized_collection = normalize_collection_name(collection)
    return await firebase_client.call_tool("firestore_delete_document", {
        "collection": normalized_collection,
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

# 스마트 Firebase 에이전트 - 오타 보정 & 한글 지원
interior_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='interior_firebase_agent',
    instruction='''
🏠 Firebase 전문가입니다. 오타 보정과 한글 컬렉션명을 지원합니다!

## 🔧 스마트 컬렉션명 지원:

### 🇰🇷 한글 컬렉션명:
- "주소" / "주소컬렉션" → addressesJson
- "스케쥴" / "스케줄" / "일정" → schedules  
- "견적서" / "견적" → estimateVersionsV3
- "사용자" / "유저" → users
- "결제" → payments
- "주문" → orders

### 🔧 자동 오타 보정:
- "schdules" → schedules ✅
- "adressesJson" → addressesJson ✅
- "usres" → users ✅
- "estimateVersionV3" → estimateVersionsV3 ✅

## 🚀 즉시 실행 예시:

### 📋 한글 컬렉션 조회:
- "스케쥴 조회해줘" → firestore_list("schedules")
- "견적서 보여줘" → firestore_list("estimateVersionsV3") 
- "주소 목록" → firestore_list("addressesJson")
- "사용자 조회" → firestore_list("users")

### 🔧 오타 자동 보정:
- "schdules 컬랙션 조회해" → firestore_list("schedules")
- "adressesJson 보여줘" → firestore_list("addressesJson")
- "usres 목록" → firestore_list("users")

### 📄 문서 조회:
- "스케쥴의 abc123 문서" → firestore_get("schedules", "abc123")
- "견적서 문서 추가" → firestore_add("estimateVersionsV3", 데이터)

### 📁 파일 & 기타:
- "파일 목록" → storage_list()
- "사용자 정보" → auth_get_user()
- "이메일 테스트" → test_email_connection()

## �� 응답 스타일:
- 오타 보정 시: "오타를 보정해서 조회했습니다!"
- 한글 매핑 시: "한글 컬렉션명을 영문으로 변환해서 조회합니다!"
- 칭찬받으면: "네! 다른 컬렉션이나 문서 조회가 필요하시면 말씀해주세요!"

## 📊 결과 표시:
🔍 조회 결과:
• 항목명: 세부정보
• 항목명: 세부정보

📈 조회 완료

## ⚡ 핵심 기능:
1. **오타 자동 보정**: 철자 오류 자동 수정
2. **한글 컬렉션명 지원**: 한국어로 컬렉션 조회 가능
3. **즉시 실행**: 질문 없이 바로 실행
4. **스마트 매칭**: 유사도 기반 최적 매칭

🔧 도구 (12개): firestore_list, firestore_get, firestore_add, firestore_update, firestore_delete, auth_get_user, storage_list, storage_info, storage_upload, storage_upload_from_url, send_estimate_email, test_email_connection

🎯 특별 기능: 
✅ "schdules" → "schedules" 자동 보정
✅ "스케쥴" → "schedules" 한글 매핑  
✅ "견적서" → "estimateVersionsV3" 한글 매핑
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
print(f"🔧 오타 보정 기능 활성화")
print(f"🇰🇷 한글 컬렉션명 지원")
print(f"📦 총 도구: {len(interior_agent.tools)}개")
print(f"🎯 지원 한글명: 스케쥴, 견적서, 주소, 사용자, 결제, 주문")