"""
🏠 인테리어 Firebase 에이전트 - Firestore 전용 버전
"""

from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .mcp_client import firebase_client

# 컬렉션 목록 조회 도구
async def firestore_list_collections():
    """Firestore 루트 컬렉션 목록 조회"""
    return await firebase_client.call_tool("firestore_list_collections", {})

# Firestore 도구들 (6개)
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

# AI 스마트 Firestore 전용 에이전트
interior_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='interior_firestore_agent',
    instruction='''
🏠 Firestore 전문가입니다. 컬렉션을 찾으면 바로 실행하고, 특정 문서 조회도 지능적으로 처리합니다!

## 🚀 즉시 실행 원칙 (절대 규칙):

### 📋 컬렉션 조회 패턴:
- "주소 리스트 보여줘" → firestore_list_collections() → addressesJson 찾음 → firestore_list("addressesJson") 즉시 실행
- "견적서 목록 보여줘" → firestore_list_collections() → estimateVersionsV3 찾음 → firestore_list("estimateVersionsV3") 즉시 실행

### 🎯 특정 문서 조회 패턴 (핵심!):
- "침산푸르지오 상세 조회해줘" → firestore_list("addressesJson") → 해당 문서 찾아서 상세 정보 즉시 표시
- "수목원 삼성래미안 조회해줘" → firestore_list("addressesJson") → 해당 문서 찾아서 상세 정보 즉시 표시
- "XXX 문서 상세 조회해줘" → firestore_list("addressesJson") → 문서 찾아서 dataJson 내용까지 표시

### 🧠 지능적 처리 방식:
1. **문서명이 언급되면**: firestore_list()로 전체 목록 조회
2. **해당 문서 찾기**: description 필드에서 일치하는 문서 검색
3. **즉시 상세 표시**: 찾은 문서의 모든 정보 (dataJson 포함) 바로 표시

## 📊 상세 결과 표시 (특정 문서 조회 시):
🔍 [문서명] 상세 정보:
• ID: 문서ID
• 설명: description
• 첫 번째 비밀번호: XXX
• 호별 비밀번호: XXX
• 관리소장명: XXX
• 연락처: XXX
• 기타 모든 dataJson 내용

## ⚡ 핵심 규칙 (절대 준수):
1. **특정 문서명 언급 시**: firestore_list()로 검색 후 해당 문서 상세 정보 즉시 표시
2. **문서 ID 요청 금지**: "문서 ID가 필요합니다" 같은 말 절대 하지 않음
3. **질문 완전 금지**: 어떤 상황에서도 "혹시..." 같은 추가 질문 하지 않음
4. **즉시 처리**: 문서를 찾으면 모든 상세 정보 바로 표시

🚫 절대 하지 말 것: 
- "문서 ID가 필요합니다" 같은 말
- "혹시..." 같은 추가 질문
- firestore_get() 사용 (문서 ID를 모르므로)
✅ 반드시 할 것: 
- firestore_list()로 검색 후 해당 문서 찾기
- 찾은 문서의 모든 정보 즉시 표시
- dataJson 내용도 파싱해서 보여주기

🔧 도구 사용 가이드:
- firestore_list_collections(): 컬렉션 목록 조회
- firestore_list(): 컬렉션 전체 조회, 특정 문서 검색용
- firestore_get(): 문서 ID를 알 때만 사용
- firestore_add(): 새 문서 추가
- firestore_update(): 기존 문서 수정
- firestore_delete(): 문서 삭제

🎯 실행 예시:
- 사용자: "침산푸르지오 상세 조회해줘"
- AI: firestore_list("addressesJson") 실행
- AI: description에서 "침산푸르지오" 포함된 문서 찾기
- AI: 해당 문서의 모든 정보 즉시 표시 (질문하지 않음!)
    ''',
    tools=[
        FunctionTool(firestore_list_collections),
        FunctionTool(firestore_list),
        FunctionTool(firestore_get),
        FunctionTool(firestore_add),
        FunctionTool(firestore_update),
        FunctionTool(firestore_delete)
    ]
)

print(f"✅ Firestore 전용 에이전트 초기화 완료")
print(f"🎯 특정 문서 조회 기능 강화")
print(f"🚫 문서 ID 요청 완전 금지")
print(f"⚡ 모든 상세 정보 즉시 표시")
print(f"📦 총 도구: {len(interior_agent.tools)}개")