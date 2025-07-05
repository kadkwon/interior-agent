"""
🔥 Firebase 전문 에이전트 - ADK 표준 LlmAgent 구현

🎯 Firebase 관련 모든 요청을 전문적으로 처리
- Firestore 조회, 추가, 수정, 삭제
- 한글 포맷팅 자동 적용
- 세션 관리 지원
"""

import json
from typing import Optional, Dict, Any
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from ..tools.mcp_client import firebase_client
from .formatter_agent import format_korean_response

# ========================================
# 🔥 Firebase 전문 도구 함수들
# ========================================

async def firestore_list_collections(session_id: Optional[str] = None):
    """Firestore 루트 컬렉션 목록 조회"""
    result = await firebase_client.call_tool("firestore_list_collections", {}, session_id)
    return format_korean_response(result, "list_collections")

async def firestore_list_documents(collection: str, limit: Optional[int] = 20, session_id: Optional[str] = None):
    """컬렉션 문서 목록 조회 - 한글 가독성 버전"""
    params = {"collection": collection, "limit": limit}
    result = await firebase_client.call_tool("firestore_list_documents", params, session_id)
    return format_korean_response(result, "list_documents")

async def firestore_get_document(collection: str, document_id: str, session_id: Optional[str] = None):
    """특정 문서 조회 - 한글 상세정보 버전"""
    print(f"🔍 [Firebase Agent] firestore_get_document: collection={collection}, document_id='{document_id}'")
    
    result = await firebase_client.call_tool("firestore_get_document", {
        "collection": collection,
        "id": document_id
    }, session_id)
    
    print(f"🔍 [Firebase Agent] MCP 서버 응답: {str(result)[:200]}...")
    return format_korean_response(result, "get_document")

async def firestore_add_document(collection: str, data: dict, session_id: Optional[str] = None):
    """문서 추가 - 한글 응답 버전"""
    result = await firebase_client.call_tool("firestore_add_document", {
        "collection": collection,
        "data": data
    }, session_id)
    return format_korean_response(result, "add_document")

async def firestore_update_document(collection: str, document_id: str, data: dict, session_id: Optional[str] = None):
    """문서 수정 - 한글 응답 버전"""
    result = await firebase_client.call_tool("firestore_update_document", {
        "collection": collection,
        "id": document_id,
        "data": data
    }, session_id)
    return format_korean_response(result, "update_document")

async def firestore_delete_document(collection: str, document_id: str, session_id: Optional[str] = None):
    """문서 삭제 - 한글 응답 버전"""
    result = await firebase_client.call_tool("firestore_delete_document", {
        "collection": collection,
        "id": document_id
    }, session_id)
    return format_korean_response(result, "delete_document")

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
    ],
    
    # Firebase 전문 Instructions
    instruction='''
🔥 Firebase 전문 에이전트입니다! Firestore 데이터베이스를 전문적으로 처리합니다.

## 🚨 **절대 규칙 - 반드시 준수!**

### 0. 🚫 **거짓 정보 생성 절대 금지! (최우선 규칙)**
- **실제 도구에서 받은 데이터만 출력**: Firebase에서 조회된 정보만 표시
- **절대 추측하지 않기**: 없는 정보는 만들어내지 않음
- **절대 가정하지 않기**: "아마도", "추정하면" 같은 표현 금지
- **절대 생성하지 않기**: 주소, 역할, 특이사항 등 실제 데이터에 없는 정보 추가 금지
- **있는 것만 출력**: Firebase 도구 결과에 있는 필드만 표시, 없는 것은 표시 안함
- **완전성보다 정확성**: 정보가 부족해도 잘못된 정보보다 낫음

### 1. 📋 **도구 결과 그대로 반환 (핵심!)**
- 도구 함수가 데이터를 반환하면 **그 결과를 수정 없이 그대로 출력**
- **절대 요약하지 않기**: "총 20개..." 같은 요약 금지
- **절대 추가 설명하지 않기**: "더 궁금하신가요?" 같은 멘트 금지
- **도구 결과만 출력하고 끝내기**

### 2. 🔍 **Firebase 조회 명령**
- "contractors 조회" → firestore_list_documents("contractors") → **도구 결과 그대로 출력**
- "견적서 목록" → firestore_list_documents("estimateVersionsV3") → **도구 결과 그대로 출력**
- "주소 리스트" → firestore_list_documents("addressesJson") → **도구 결과 그대로 출력**
- "문서명 상세 조회" → firestore_get_document("컬렉션", "문서명") → **도구 결과 그대로 출력**

### 3. ✏️ **Firebase 수정 명령 (기존 데이터 수정)**
- **기본 원칙**: 새 필드 생성이 아닌 기존 데이터 찾아서 수정
- **처리 순서**: 1) 데이터 위치 찾기 → 2) 해당 필드 수정 → 3) 결과 확인

#### 3-1. 수정 처리 프로세스 (반드시 실제 업데이트 실행):
1. **데이터 위치 탐색**: 수정할 값이 포함된 문서 찾기
   - 여러 컬렉션에서 검색 (contractors, estimateVersionsV3, addressesJson 등)
   - 스마트 검색 활용하여 정확한 문서 위치 파악
2. **기존 데이터 확인**: firestore_get_document으로 현재 데이터 상태 확인
3. **JSON 구조 분석**: 
   - contractorsJson, jsonData 등 JSON 필드 파싱
   - 배열 구조인지 객체 구조인지 확인
   - 수정할 정확한 필드 위치 파악
4. **JSON 데이터 수정 (구조 완전 보존)**:
   - **Step 1**: 기존 JSON 문자열을 반드시 JSON.parse()로 파싱
   - **Step 2**: 파싱된 객체에서 해당 필드만 수정 (다른 필드는 절대 건드리지 않음)
   - **Step 3**: 수정된 객체를 JSON.stringify()로 다시 문자열로 변환
   - **절대 금지**: 새로운 JSON 구조 생성, 기존 필드 삭제
5. **반드시 firestore_update_document 실행**: 
   - firestore_update_document(컬렉션, 문서ID, {JSON필드명: 수정된JSON문자열}) 호출
   - 절대 메시지만 출력하지 않고 반드시 실제 업데이트 수행
6. **결과 반환**: 수정 완료 메시지 + 수정된 데이터 표시

### 4. 🚨 **세션 관리**
- 모든 도구 함수 호출 시 session_id 전달
- 세션 ID는 상위 에이전트에서 전달받음

### 5. 💡 **응답 형식**
- 모든 응답은 한글로 포맷팅됨 (format_korean_response 자동 적용)
- 깔끔하고 읽기 쉬운 형태로 출력
- 불필요한 메타데이터 제거
''',
    
    description="Firebase Firestore 데이터베이스 전문 처리 에이전트"
) 