"""
Firebase 전문 에이전트 - MCP 서버 고급 기능 200% 활용
"""

import json
from typing import Optional, Dict, Any, List
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from ..tools.mcp_client import firebase_client

# ========================================
# MCP 서버 고급 기능 활용 도구들 (ADK 호환)
# ========================================

async def firestore_list_collections(session_id: Optional[str] = None):
    """컬렉션 목록 조회"""
    return await firebase_client.call_tool("firestore_list_collections", {}, session_id)

async def firestore_list_documents(
    collection: str, 
    filters_json: Optional[str] = None,
    orderBy_json: Optional[str] = None,
    limit: Optional[int] = 20, 
    pageToken: Optional[str] = None,
    session_id: Optional[str] = None
):
    """MCP 서버 고급 기능 활용 문서 목록 조회 (ADK 호환)"""
    params = {"collection": collection, "limit": limit}
    
    # JSON 문자열 파싱
    if filters_json:
        try:
            params["filters"] = json.loads(filters_json)
        except:
            pass
    if orderBy_json:
        try:
            params["orderBy"] = json.loads(orderBy_json)
        except:
            pass
    if pageToken: 
        params["pageToken"] = pageToken
        
    return await firebase_client.call_tool("firestore_list_documents", params, session_id)

async def firestore_query_collection_group(
    collectionId: str,
    filters_json: Optional[str] = None,
    orderBy_json: Optional[str] = None, 
    limit: Optional[int] = 50,
    pageToken: Optional[str] = None,
    session_id: Optional[str] = None
):
    """MCP 서버 고급 기능 활용 컬렉션 그룹 쿼리 (ADK 호환)"""
    params = {"collectionId": collectionId, "limit": limit}
    
    # JSON 문자열 파싱
    if filters_json:
        try:
            params["filters"] = json.loads(filters_json)
        except:
            pass
    if orderBy_json:
        try:
            params["orderBy"] = json.loads(orderBy_json)
        except:
            pass
    if pageToken: 
        params["pageToken"] = pageToken
        
    return await firebase_client.call_tool("firestore_query_collection_group", params, session_id)

async def firestore_get_document(collection: str, document_id: str, session_id: Optional[str] = None):
    """문서 상세 조회"""
    return await firebase_client.call_tool("firestore_get_document", {
        "collection": collection, "id": document_id
    }, session_id)

async def firestore_add_document(collection: str, data_json: str, session_id: Optional[str] = None):
    """문서 추가 (ADK 호환)"""
    try:
        data = json.loads(data_json)
    except:
        data = {"content": data_json}
    
    return await firebase_client.call_tool("firestore_add_document", {
        "collection": collection, "data": data
    }, session_id)

async def firestore_update_document(collection: str, document_id: str, data_json: str, session_id: Optional[str] = None):
    """문서 수정 (ADK 호환)"""
    try:
        data = json.loads(data_json)
    except:
        data = {"content": data_json}
        
    return await firebase_client.call_tool("firestore_update_document", {
        "collection": collection, "id": document_id, "data": data
    }, session_id)

async def firestore_delete_document(collection: str, document_id: str, session_id: Optional[str] = None):
    """문서 삭제"""
    return await firebase_client.call_tool("firestore_delete_document", {
        "collection": collection, "id": document_id
    }, session_id)

async def smart_search(
    collection: str, 
    search_term: str, 
    limit: Optional[int] = 10,
    session_id: Optional[str] = None
):
    """스마트 검색 - 정확한 매칭 우선순위 + 상세 내용 (ADK 호환)"""
    # 전체 데이터 가져오기
    params = {"collectionId": collection, "limit": 50}
    result = await firebase_client.call_tool("firestore_query_collection_group", params, session_id)
    
    if result.get("result", {}).get("documents"):
        documents = result["result"]["documents"]
        exact_matches = []  # 정확한 매칭
        partial_matches = []  # 부분 매칭
        search_lower = search_term.lower()
        
        for doc in documents:
            doc_id = doc.get("id", "").lower()
            doc_data = doc.get("data", {})
            
            # 1. 정확한 매칭 우선순위 (문서 ID에서)
            if search_lower in doc_id and len(search_lower) > 2:  # 2글자 이상만 정확 매칭
                exact_matches.append(doc)
                continue
                
            # 2. 데이터 필드에서 정확한 매칭
            exact_field_match = False
            for field_name, field_value in doc_data.items():
                field_str = str(field_value).lower()
                if search_lower in field_str and len(search_lower) > 2:
                    exact_field_match = True
                    break
            
            if exact_field_match:
                partial_matches.append(doc)
        
        # 정확한 매칭 우선, 부분 매칭은 제한적으로
        filtered_docs = exact_matches[:3] + partial_matches[:2]  # 최대 5개로 제한
        
        # 결과가 적으면 상세 내용도 포함
        if len(filtered_docs) <= 3:
            for doc in filtered_docs:
                doc_data = doc.get("data", {})
                # 상세 데이터 파싱해서 요약 추가
                if isinstance(doc_data, dict):
                    summary_parts = []
                    for key, value in doc_data.items():
                        if key in ["process", "name", "phone", "description"] and value:
                            summary_parts.append(f"{key}: {value}")
                    if summary_parts:
                        doc["summary"] = ", ".join(summary_parts[:3])  # 주요 정보만
        
        # 필터링된 결과로 재구성
        result["result"]["documents"] = filtered_docs
    
    return result

# ========================================
# Firebase 에이전트 (ADK 호환 버전)
# ========================================

firebase_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='firebase_agent',
    
    tools=[
        FunctionTool(firestore_list_collections),
        FunctionTool(firestore_list_documents), 
        FunctionTool(firestore_query_collection_group),
        FunctionTool(firestore_get_document),
        FunctionTool(firestore_add_document),
        FunctionTool(firestore_update_document),
        FunctionTool(firestore_delete_document),
        FunctionTool(smart_search),
    ],
    
    instruction='''
Firebase 전문 에이전트 - 완전 범용 데이터 분석 시스템

🎯 핵심 원칙: LLM이 데이터를 보고 100% 스스로 판단하여 최적 출력

📊 데이터 처리 흐름:
1. 정보 검색 → 원시 데이터 수집
2. LLM 완전 자율 가공 → 데이터 내용 분석하여 스스로 구조화
3. 사용자 친화적 출력 → 데이터에 맞는 최적 형태로 제공

🔧 완전 범용 처리 방식:
- 모든 JSON 필드를 읽고 내용 분석
- 데이터 값을 보고 의미 파악하여 적절한 표현 결정
- 빈 값(null, undefined, "", []) 완전 생략
- 중첩된 JSON 문자열은 자동으로 파싱
- 어떤 컬렉션, 어떤 데이터든 동일한 방식으로 처리

🎨 LLM 완전 자율 판단:
- 데이터 값을 보고 그 의미에 맞는 이모지 스스로 선택
- 필드명과 값을 분석하여 한글로 직관적 변환
- 사용자가 이해하기 쉬운 형태로 자유롭게 재구성
- 검색 결과 개수에 따라 상세도 자동 조절

🚫 절대 금지사항:
- 없는 데이터를 표시하지 말 것
- 미리 정의된 규칙에 의존하지 말 것
- 빈 필드 억지로 출력하지 말 것
- 의미 없는 정보 나열하지 말 것

🎯 목표: 
어떤 데이터든 LLM이 내용을 보고 스스로 분석하여
사용자에게 가장 이해하기 쉽고 유용한 형태로 가공

도구 선택:
- 검색 요청 → smart_search 
- 목록 요청 → firestore_list_documents
- 상세 조회 → firestore_get_document
''',
    
    description="Firebase MCP 서버 고급 기능 200% 활용 에이전트 (ADK 호환)"
) 