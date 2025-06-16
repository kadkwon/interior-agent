"""
주소 관리 에이전트

addressesJson 컬렉션의 CRUD 작업을 담당하는 전용 에이전트입니다.
단순하고 직접적인 주소 관리 행동들을 제공합니다.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import time
import json
from ..client.mcp_client import FirebaseMCPClient

client = FirebaseMCPClient()

def register_new_address(address: str, description: str = "", data_json: str = "{}") -> Dict[str, Any]:
    """
    새로운 현장 주소를 등록합니다.
    
    Args:
        address: 현장 주소
        description: 주소 설명
        data_json: 추가 데이터 (JSON 문자열)
        
    Returns:
        Dict: 등록된 주소 정보
    """
    doc_data = {
        "address": address,
        "description": description,
        "dataJson": data_json,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return client.create_document("addresses", doc_data)

def update_existing_address(address_id: str, address: str = None, description: str = None, data_json: str = None) -> Dict[str, Any]:
    """
    기존 주소 정보를 업데이트합니다.
    
    Args:
        address_id: 주소 문서 ID
        address: 새로운 주소 (선택)
        description: 새로운 설명 (선택)
        data_json: 새로운 추가 데이터 (선택)
        
    Returns:
        Dict: 업데이트된 주소 정보
    """
    update_data = {}
    if address is not None:
        update_data["address"] = address
    if description is not None:
        update_data["description"] = description
    if data_json is not None:
        update_data["dataJson"] = data_json
    update_data["updated_at"] = datetime.now().isoformat()
    
    return client.update_document("addresses", address_id, update_data)

def delete_address_record(address_id: str) -> Dict[str, Any]:
    """
    주소 레코드를 삭제합니다.
    
    Args:
        address_id: 삭제할 주소 문서 ID
        
    Returns:
        Dict: 삭제 결과
    """
    return client.delete_document("addresses", address_id)

def list_all_addresses(limit: int = 10) -> List[Dict[str, Any]]:
    """
    등록된 모든 주소 목록을 조회합니다.
    
    Args:
        limit: 조회할 최대 문서 수
        
    Returns:
        List[Dict]: 주소 목록
    """
    return client.list_documents("addresses", limit=limit)

def search_addresses_by_keyword(keyword: str, field: str = "address", limit: int = 10) -> List[Dict[str, Any]]:
    """
    키워드로 주소를 검색합니다.
    
    Args:
        keyword: 검색 키워드
        field: 검색할 필드 이름
        limit: 조회할 최대 문서 수
        
    Returns:
        List[Dict]: 검색된 주소 목록
    """
    return client.search_documents("addresses", field, keyword, limit=limit)

# =================
# 헬퍼 함수들
# =================

def _get_document_by_id(doc_id: str) -> dict:
    """문서 ID로 특정 문서 조회"""
    try:
        # addressesJson 컬렉션에서 모든 문서 조회 후 ID로 필터링
        result = query_any_collection("addressesJson", limit=500)
        if result.get("status") == "success":
            # 응답 구조에 따라 documents 추출
            documents = []
            try:
                if isinstance(result, dict):
                    if result.get("status") == "success":
                        documents = result.get("raw_data", {}).get("data", {}).get("documents", [])
                    elif result.get("success"):
                        documents = result.get("data", {}).get("documents", [])
            except Exception:
                # 추가 시도: data 직접 접근
                documents = result.get("data", {}).get("documents", [])
            
            for doc in documents:
                doc_id_check = doc.get("id") or doc.get("_id") or doc.get("name", "").split("/")[-1]
                if doc_id_check == doc_id:
                    doc_data = doc.get("data", {})
                    # dataJson 파싱
                    data_json_str = doc_data.get("dataJson", "{}")
                    try:
                        data_json = json.loads(data_json_str) if data_json_str else {}
                    except json.JSONDecodeError:
                        data_json = {}
                    
                    return {
                        "exists": True,
                        "data": doc_data  # 원본 doc_data 반환 (description 포함)
                    }
        
        return {"exists": False}
        
    except Exception:
        return {"exists": False}


def _check_related_data(address: str) -> dict:
    """관련 데이터 존재 여부 확인 (schedules 등)"""
    try:
        related_collections = []
        
        # schedules 컬렉션 확인
        schedules_result = query_any_collection("schedules", limit=100)
        if schedules_result.get("status") == "success":
            documents = schedules_result.get("data", {}).get("documents", [])
            
            for doc in documents:
                doc_data = doc.get("data", {})
                # schedules 컬렉션에서 주소는 description 필드에 있을 수 있음
                doc_address = doc_data.get("description", "")
                
                if address and doc_address and (address in doc_address or doc_address in address):
                    related_collections.append("schedules")
                    break
        
        return {
            "has_related": len(related_collections) > 0,
            "collections": related_collections
        }
        
    except Exception:
        return {"has_related": False, "collections": []}

 