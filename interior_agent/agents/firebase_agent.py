"""
🔥 Firebase 전문 에이전트 - ADK 표준 LlmAgent 구현

📋 **Firebase 에이전트 역할 정의** 📋
┌─────────────────────────────────────────────────────┐
│ 🎯 핵심 역할: 데이터베이스 전문가 (모든 DB 작업 담당)        │
├─────────────────────────────────────────────────────┤
│ ✅ 해야 할 일:                                        │
│  1. 모든 Firebase/Firestore 작업 (CRUD)              │
│  2. 검색 및 필터링 로직 처리                           │
│  3. 비즈니스 로직 (어떤 컬렉션에서 검색할지 결정)         │
│  4. MCP 서버와 통신                                   │
│  5. 검색어 추출 및 처리                               │
│  6. 데이터 구조 이해 및 적절한 필드 선택                 │
│                                                     │
│ ❌ 절대 하지 말아야 할 일:                               │
│  1. 포맷팅이나 한글화 (포맷팅 도구 역할)                 │
│  2. 라우팅 결정 (메인 에이전트 역할)                    │
│  3. 이메일 전송 (이메일 에이전트 역할)                   │
│                                                     │
│ 🔄 처리 흐름:                                         │
│  요청 받음 → 검색어 추출 → MCP 호출 → 필터링 → 포맷팅 요청  │
└─────────────────────────────────────────────────────┘

🎯 Firebase 관련 모든 요청을 전문적으로 처리
- Firestore 조회, 추가, 수정, 삭제
- 범용 검색 및 필터링 (모든 컬렉션 지원)
- 포맷팅 에이전트에게 한글 변환 위임
- 세션 관리 지원
"""

import json
from typing import Optional, Dict, Any
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from ..tools.mcp_client import firebase_client

# ========================================
# 🔥 Firebase 전문 도구 함수들
# ========================================

async def firestore_list_collections(session_id: Optional[str] = None):
    """Firestore 루트 컬렉션 목록 조회"""
    result = await firebase_client.call_tool("firestore_list_collections", {}, session_id)
    return result

async def firestore_list_documents(collection: str, limit: Optional[int] = 20, session_id: Optional[str] = None):
    """컬렉션 문서 목록 조회"""
    params = {"collection": collection, "limit": limit}
    result = await firebase_client.call_tool("firestore_list_documents", params, session_id)
    return result

async def firestore_get_document(collection: str, document_id: str, session_id: Optional[str] = None):
    """특정 문서 조회"""
    print(f"🔍 [Firebase Agent] firestore_get_document: collection={collection}, document_id='{document_id}'")
    
    result = await firebase_client.call_tool("firestore_get_document", {
        "collection": collection,
        "id": document_id
    }, session_id)
    
    print(f"🔍 [Firebase Agent] MCP 서버 응답: {str(result)[:200]}...")
    return result

async def firestore_add_document(collection: str, data: dict, session_id: Optional[str] = None):
    """문서 추가"""
    result = await firebase_client.call_tool("firestore_add_document", {
        "collection": collection,
        "data": data
    }, session_id)
    return result

async def firestore_update_document(collection: str, document_id: str, data: dict, session_id: Optional[str] = None):
    """문서 수정"""
    result = await firebase_client.call_tool("firestore_update_document", {
        "collection": collection,
        "id": document_id,
        "data": data
    }, session_id)
    return result

async def firestore_delete_document(collection: str, document_id: str, session_id: Optional[str] = None):
    """문서 삭제"""
    result = await firebase_client.call_tool("firestore_delete_document", {
        "collection": collection,
        "id": document_id
    }, session_id)
    return result

async def firestore_query_collection_group(collection_id: str, limit: Optional[int] = 50, search_term: Optional[str] = None, session_id: Optional[str] = None):
    """컬렉션 그룹 쿼리 - 전체 문서 검색용"""
    params = {"collectionId": collection_id, "limit": limit}
    result = await firebase_client.call_tool("firestore_query_collection_group", params, session_id)
    
    # Firebase 에이전트에서 검색 필터링 처리
    if search_term and result.get("result", {}).get("documents"):
        result = _filter_documents_by_search_term(result, search_term)
    
    return result

def _filter_documents_by_search_term(result: Dict[str, Any], search_term: str) -> Dict[str, Any]:
    """Firebase 에이전트에서 검색 필터링 처리"""
    documents = result.get("result", {}).get("documents", [])
    filtered_docs = []
    search_lower = search_term.lower()
    
    for doc in documents:
        doc_data = doc.get("data", {})
        found_match = False
        
        # 모든 필드에서 검색어 찾기 (범용화)
        for field_name, field_value in doc_data.items():
            # 모든 값을 문자열로 변환해서 검색
            field_str = str(field_value).lower()
            if search_lower in field_str:
                found_match = True
                break
        
        if found_match:
            filtered_docs.append(doc)
    
    # 필터링된 결과로 result 구조 재구성
    filtered_result = result.copy()
    filtered_result["result"]["documents"] = filtered_docs
    return filtered_result

async def search_documents(collection_id: str, search_term: str, limit: Optional[int] = 50, session_id: Optional[str] = None):
    """범용 검색 함수 - 모든 컬렉션에서 검색 가능"""
    return await firestore_query_collection_group(collection_id, limit, search_term, session_id)

# ========================================
# 🤖 Firebase 전문 LlmAgent 정의
# ========================================

firebase_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='firebase_agent',
    
    # Firebase 전문 도구들
    tools=[
        FunctionTool(firestore_list_collections),
        FunctionTool(firestore_list_documents),
        FunctionTool(firestore_get_document),
        FunctionTool(firestore_add_document),
        FunctionTool(firestore_update_document),
        FunctionTool(firestore_delete_document),
        FunctionTool(firestore_query_collection_group),
        FunctionTool(search_documents),
    ],
    
    # Firebase 전문 Instructions (instruction만으로 포맷팅 처리)
    instruction='''
Firebase 전문 에이전트입니다. Firestore 데이터베이스를 전문적으로 처리합니다.

절대 규칙 - 반드시 준수:

0. 거짓 정보 생성 절대 금지 (최우선 규칙)
- 실제 도구에서 받은 데이터만 처리: Firebase에서 조회된 정보만 사용
- 절대 추측하지 않기: 없는 정보는 만들어내지 않음
- 있는 것만 처리: 도구 결과에 있는 내용만 사용

1. 하드코딩 명령어 처리
- "주소 목록 보여줘" -> firestore_list_documents("addressesJson") 실행
- "견적서 목록 보여줘" -> firestore_list_documents("estimateVersionsV3") 실행

2. 한글 출력 형식 (instruction으로 직접 변환)
도구 함수 결과를 받으면 다음 형식으로 한글 변환해서 출력:

문서 목록 (list_documents):
```
문서 목록 (N개):

문서ID - 설명내용
문서ID - 설명내용
```

문서 상세 (get_document):
```
문서ID 상세 정보:

주소: (실제 설명 내용)
1층비밀번호: (실제 비밀번호)
세대비밀번호: (실제 비밀번호)
담당자: (실제 담당자명)
계약금액: (실제 계약금액)
전화번호: (실제 전화번호)
이메일: (실제 이메일)
생성일: (실제 생성일)
현장번호: (실제 현장번호)
```

검색 결과 (query_collection_group):
```
검색 결과 (N개):

문서ID - 설명내용
문서ID - 설명내용
```

작업 완료:
```
문서가 성공적으로 추가되었습니다.
문서가 성공적으로 수정되었습니다.
문서가 성공적으로 삭제되었습니다.
```

3. 강력한 검색 명령 패턴 (모든 검색 요청 처리)

A. 검색 패턴 인식 (사용자 요청을 다음 패턴으로 분석):
  패턴 1: "XXX에서 YYY 찾아줘" → search_documents("XXX", "YYY")
  패턴 2: "YYY 찾아줘" → search_documents("addressesJson", "YYY") 
  패턴 3: "비밀번호가 YYY 있는" → search_documents("addressesJson", "YYY")
  패턴 4: "주소에서 YYY" → search_documents("addressesJson", "YYY")
  패턴 5: "컬렉션명 조회" → firestore_list_documents("컬렉션명")

B. 검색어 추출 규칙:
  1. 사용자 요청에서 핵심 키워드 추출
  2. "에서", "찾아줘", "있는", "조회" 등 불용어 제거
  3. 컬렉션명이 명시되면 해당 컬렉션 사용, 없으면 기본 addressesJson
  4. 추출된 검색어로 search_documents 실행

C. 구체적 처리 예시:
  - "주소 리스트에서 비밀번호가 9094# 있는 주소를 찾아줘" 
    → 검색어: "9094#", 컬렉션: "addressesJson"
    → search_documents("addressesJson", "9094#")
  
  - "users에서 김철수를 찾아줘"
    → 검색어: "김철수", 컬렉션: "users" 
    → search_documents("users", "김철수")
  
  - "8284629 찾아줘"
    → 검색어: "8284629", 컬렉션: "addressesJson"(기본)
    → search_documents("addressesJson", "8284629")
  
  - "수성 효성 찾아줘"
    → 검색어: "수성", 컬렉션: "addressesJson"(기본)
    → search_documents("addressesJson", "수성")

D. 검색 실행 원칙:
  1. 반드시 search_documents 함수 사용 (검색 필터링 포함)
  2. firestore_list_documents는 "목록 보여줘"일 때만 사용
  3. 검색 결과만 출력, 전체 목록 절대 금지
  4. 결과 없으면 "검색어에 대한 결과가 없습니다" 메시지
  5. 결과 있으면 한글 형식으로 깔끔하게 출력

E. 검색 vs 목록 구분:
  - 검색: "찾아줘", "있는", "검색" → search_documents 사용
  - 목록: "목록", "리스트", "조회" → firestore_list_documents 사용
  - 애매하면 search_documents 우선 사용

F. 검색 범위:
  - 모든 필드의 모든 내용에서 검색
  - 대소문자 구분 없음
  - 부분 문자열 매칭
  - JSON 문자열 내부도 검색 대상

5. Firebase 수정 명령
- 문서 추가, 수정, 삭제는 firestore_add/update/delete_document 사용
- JSON 문자열 수정 시 문자열 치환만 사용 (JSON 파싱 금지)

6. 중요 처리 원칙
- 도구 결과를 받으면 즉시 위 한글 형식으로 변환해서 출력
- 절대 원본 JSON을 그대로 출력하지 않기
- 사용자 친화적인 한글 메시지로 변환
- 결과가 없으면 "해당 컬렉션에 문서가 없습니다" 등으로 안내
- instruction만으로 모든 포맷팅 처리
''',
    
    description="Firebase Firestore 데이터베이스 전문 처리 에이전트 (instruction만으로 한글 포맷팅)"
) 