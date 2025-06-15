# Firebase MCP 호출 규칙 import 추가
try:
    from ..firebase_mcp_rules import (
        validate_mcp_call,
        execute_mcp_sequence,
        handle_mcp_error,
        validate_response,
        log_operation
    )
except ImportError:
    # ADK Web 환경에서는 절대 import
    from interior_agents.firebase_mcp_rules import (
        validate_mcp_call,
        execute_mcp_sequence,
        handle_mcp_error,
        validate_response,
        log_operation
    )

# 스마트 검색을 위한 퓨지 매칭 라이브러리
try:
    from difflib import SequenceMatcher
    import re
    FUZZY_SEARCH_AVAILABLE = True
except ImportError:
    FUZZY_SEARCH_AVAILABLE = False

# Firebase 클라이언트 import
try:
    from ..client.firebase_client import firebase_client, schedule_formatter
    FIREBASE_AVAILABLE = True
except ImportError:
    # Firebase 클라이언트가 없을 경우 더미 객체 생성
    class DummyFirebaseClient:
        def query_collection(self, *args, **kwargs):
            return {"success": False, "error": "Firebase client를 사용할 수 없습니다."}
        def get_project_info(self):
            return {"success": False, "error": "Firebase client를 사용할 수 없습니다."}
        def list_collections(self):
            return {"success": False, "error": "Firebase client를 사용할 수 없습니다."}
        def list_files(self, *args, **kwargs):
            return {"success": False, "error": "Firebase client를 사용할 수 없습니다."}
    
    class DummyScheduleFormatter:
        def format_schedule_data(self, data):
            return "Firebase 연결이 필요합니다."
    
    firebase_client = DummyFirebaseClient()
    schedule_formatter = DummyScheduleFormatter()
    FIREBASE_AVAILABLE = False

# 스마트 검색 헬퍼 함수들
def _calculate_similarity(text1: str, text2: str) -> float:
    """두 텍스트 간의 유사도를 계산합니다 (0.0 ~ 1.0)"""
    if not FUZZY_SEARCH_AVAILABLE:
        return 1.0 if text1 == text2 else 0.0
    
    if text1 == text2:
        return 1.0
    
    # 공백 제거 후 비교
    clean1 = re.sub(r'\s+', '', text1.lower())
    clean2 = re.sub(r'\s+', '', text2.lower())
    
    if clean1 == clean2:
        return 0.95  # 공백만 다른 경우
    
    # SequenceMatcher로 유사도 계산
    matcher = SequenceMatcher(None, clean1, clean2)
    return matcher.ratio()

def _find_best_match_documents(target_id: str, documents: list, threshold: float = 0.7) -> list:
    """문서 목록에서 가장 유사한 문서들을 찾습니다"""
    if not documents:
        return []
    
    matches = []
    for doc in documents:
        doc_id = doc.get('id', '')
        similarity = _calculate_similarity(target_id, doc_id)
        if similarity >= threshold:
            matches.append({
                'document': doc,
                'similarity': similarity,
                'original_id': doc_id
            })
    
    # 유사도 순으로 정렬
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    return matches

def _smart_document_search(collection_path: str, document_id: str) -> dict:
    """스마트 문서 검색: 정확 매칭 실패 시 유사 문서를 찾습니다"""
    try:
        # 1단계: 전체 문서 목록 조회
        list_response = firebase_client.list_documents(
            collection_path=collection_path,
            limit=100  # 충분한 수량 조회
        )
        
        if not (list_response.get("success") and validate_response(list_response)):
            return {
                "status": "error",
                "message": f"문서 목록 조회 실패: {collection_path}"
            }
        
        documents = list_response.get("data", {}).get("documents", [])
        if not documents:
            return {
                "status": "not_found",
                "message": f"{collection_path} 컬렉션이 비어있습니다."
            }
        
        # 2단계: 유사 문서 검색
        matches = _find_best_match_documents(document_id, documents, threshold=0.7)
        
        if not matches:
            return {
                "status": "not_found",
                "message": f"'{document_id}'와 유사한 문서를 찾을 수 없습니다.",
                "available_documents": [doc.get('id', '') for doc in documents[:10]]  # 처음 10개만
            }
        
        best_match = matches[0]
        similarity = best_match['similarity']
        found_doc = best_match['document']
        original_id = best_match['original_id']
        
        # 3단계: 최적 매칭 문서 반환
        return {
            "status": "success",
            "document": found_doc,
            "exists": True,
            "smart_search": True,
            "original_query": document_id,
            "found_id": original_id,
            "similarity": similarity,
            "message": f"'{document_id}' 대신 '{original_id}' 문서를 찾았습니다 (유사도: {similarity:.1%})",
            "alternatives": [match['original_id'] for match in matches[1:3]]  # 다른 후보 최대 2개
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"스마트 검색 중 오류: {str(e)}"
        }

def query_schedule_collection(limit: int = 50) -> dict:
    """
    Firebase Firestore의 schedules 컬렉션을 조회합니다.
    Firebase MCP 호출 규칙을 적용하여 모든 데이터 조회를 MCP를 통해 처리합니다.
    
    Args:
        limit: 조회할 일정 수 제한 (기본값: 50)
        
    Returns:
        dict: 일정 목록과 포맷팅된 결과
    """
    try:
        # 🚨 0.1 Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "schedules", {"limit": limit}):
            log_operation("query_schedules", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 🚨 0.2-1 사용자 요청 분석 및 필요한 Firebase 컬렉션 식별
        log_operation("query_schedules", "schedules", {"step": "MCP 호출 시작", "limit": limit}, True)
        
        # 🚨 0.2-2 적절한 Firebase MCP 함수 호출
        response = firebase_client.query_collection("schedules", limit=limit)
        
        # 🚨 0.2-3 호출 결과 확인 및 검증
        # 안전한 응답 처리 - bool 타입 체크 추가
        if not isinstance(response, dict):
            log_operation("query_schedules", "schedules", {"error": "응답이 dict 타입이 아님"}, False)
            return {
                "status": "error",
                "message": "Firebase 응답 형식이 올바르지 않습니다."
            }
        
        # validate_response는 bool을 반환하므로 response를 직접 사용
        is_valid = validate_response(response)
        
        if is_valid and response.get("success"):
            # schedules 컬렉션 데이터 포맷팅
            data = response.get("data", {})
            documents = data.get("documents", [])
            
            # 스케줄 데이터를 사용자 친화적으로 포맷팅
            formatted_result = _format_schedules_data(documents)
            
            log_operation("query_schedules", "schedules", {"limit": limit, "count": len(documents)}, True)
            return {
                "status": "success",
                "formatted_result": formatted_result,
                "raw_data": response,
                "schedules": documents,
                "total_count": len(documents),
                "message": f"schedules 컬렉션에서 {len(documents)}개 문서를 조회했습니다."
            }
        else:
            return {
                "status": "error",
                "message": handle_mcp_error(Exception(f"schedules 컬렉션 조회 실패: {response.get('message', '알 수 없는 오류') if isinstance(response, dict) else '응답 없음'}"), "query_schedules")
            }
            
    except Exception as e:
        log_operation("query_schedules", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": handle_mcp_error(e, "query_schedules")
        }

def get_firebase_project_info() -> dict:
    """
    Firebase 프로젝트 정보를 조회합니다.
    Firebase MCP 호출 규칙을 적용하여 모든 프로젝트 정보 조회를 MCP를 통해 처리합니다.
    
    Returns:
        dict: 프로젝트 정보
    """
    try:
        # 🚨 0.1 Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "project_info"):
            log_operation("get_project_info", "project_info", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 🚨 0.2-2 적절한 Firebase MCP 함수 호출
        response = firebase_client.get_project_info()
        
        # 🚨 0.2-3 호출 결과 확인 및 검증
        is_valid = validate_response(response)
        
        if is_valid and response.get("success"):
            project_data = response.get("data", {})
            
            log_operation("get_project_info", "project_info", {"project_id": project_data.get('projectId', 'Unknown')}, True)
            return {
                "status": "success",
                "project_info": project_data,
                "message": f"프로젝트 '{project_data.get('projectId', 'Unknown')}'에 연결되었습니다."
            }
        else:
            return handle_mcp_error(Exception(f"프로젝트 정보 조회 실패: {response.get('message', '알 수 없는 오류') if isinstance(response, dict) else '응답 없음'}"), "get_project_info")
            
    except Exception as e:
        log_operation("get_project_info", "project_info", {"error": str(e)}, False)
        return handle_mcp_error(e, "get_project_info")

def list_firestore_collections() -> dict:
    """
    Firestore의 모든 컬렉션 목록을 조회합니다.
    Firebase MCP 호출 규칙을 적용하여 모든 컬렉션 목록 조회를 MCP를 통해 처리합니다.
    
    Returns:
        dict: 컬렉션 목록
    """
    try:
        # 🚨 0.1 Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("collection_list", "firestore"):
            log_operation("list_collections", "firestore", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 🚨 0.2-2 적절한 Firebase MCP 함수 호출
        response = firebase_client.list_collections()
        
        # 🚨 0.2-3 호출 결과 확인 및 검증
        is_valid = validate_response(response)
        
        if is_valid and response.get("success"):
            collections = response.get("data", {}).get("collections", [])
            
            formatted_list = "📋 Firestore 컬렉션 목록:\n"
            for i, collection in enumerate(collections, 1):
                formatted_list += f"{i}. {collection}\n"
            
            log_operation("list_collections", "firestore", {"count": len(collections)}, True)
            return {
                "status": "success",
                "collections": collections,
                "formatted_list": formatted_list,
                "total_count": len(collections),
                "message": f"총 {len(collections)}개의 컬렉션이 있습니다."
            }
        else:
            return handle_mcp_error(Exception(f"컬렉션 목록 조회 실패: {response.get('message', '알 수 없는 오류') if isinstance(response, dict) else '응답 없음'}"), "list_collections")
            
    except Exception as e:
        log_operation("list_collections", "firestore", {"error": str(e)}, False)
        return handle_mcp_error(e, "list_collections")

def query_any_collection(collection_name: str, limit: int = 10) -> dict:
    """
    지정된 컬렉션을 쿼리합니다. (단순 조회, 필터 없음)
    Firebase MCP 호출 규칙을 적용하여 모든 컬렉션 쿼리를 MCP를 통해 처리합니다.
    
    Args:
        collection_name: 조회할 컬렉션 이름
        limit: 조회할 문서 수 제한
        
    Returns:
        dict: 쿼리 결과
    """
    try:
        # 🚨 0.1 Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", collection_name):
            log_operation("query_collection", collection_name, {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 🚨 0.2-2 적절한 Firebase MCP 함수 호출
        response = firebase_client.query_collection(collection_name, limit=limit)
        
        # 🚨 0.2-3 호출 결과 확인 및 검증
        if not validate_response(response):
            error_msg = handle_mcp_error(Exception("컬렉션 쿼리 실패"), "query_collection")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 성공적인 응답 처리
        if response and response.get("success"):
            data = response.get("data", {})
            documents = data.get("documents", [])
            
            log_operation("query_collection", collection_name, {"count": len(documents)}, True)
            return {
                "status": "success",
                "collection": collection_name,
                "count": len(documents),
                "data": data,
                "raw_data": response,
                "message": f"{collection_name} 컬렉션에서 {len(documents)}개 문서를 조회했습니다."
            }
        else:
            error_msg = handle_mcp_error(Exception("쿼리 응답 오류"), "query_collection")
            return {
                "status": "error",
                "message": error_msg
            }
            
    except Exception as e:
        log_operation("query_collection", collection_name, {"error": str(e)}, False)
        error_msg = handle_mcp_error(e, "query_collection")
        return {
            "status": "error",
            "message": error_msg
        }

def list_storage_files(prefix: str = "") -> dict:
    """
    Firebase Storage의 파일 목록을 조회합니다.
    Firebase MCP 호출 규칙을 적용하여 모든 Storage 조회를 MCP를 통해 처리합니다.
    
    Args:
        prefix: 파일 경로 접두사 (폴더 지정용)
        
    Returns:
        dict: 파일 목록
    """
    try:
        # 🚨 0.1 Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "storage", {"prefix": prefix}):
            log_operation("list_storage", "storage", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 🚨 0.2-2 적절한 Firebase MCP 함수 호출
        response = firebase_client.list_files(prefix=prefix)
        
        # 🚨 0.2-3 호출 결과 확인 및 검증
        is_valid = validate_response(response)
        
        if is_valid and response.get("success"):
            files = response.get("data", {}).get("files", [])
            
            formatted_list = f"📁 Firebase Storage 파일 목록 (prefix: '{prefix}'):\n"
            formatted_list += f"총 {len(files)}개의 파일이 있습니다.\n\n"
            
            for i, file_info in enumerate(files, 1):
                name = file_info.get("name", "Unknown")
                size = file_info.get("size", "Unknown")
                updated = file_info.get("updated", "Unknown")
                
                formatted_list += f"{i}. {name}\n"
                formatted_list += f"   크기: {size} bytes\n"
                formatted_list += f"   수정일: {updated}\n"
                formatted_list += f"   {'-' * 30}\n\n"
            
            log_operation("list_storage", "storage", {"files_count": len(files), "prefix": prefix}, True)
            return {
                "status": "success",
                "files": files,
                "formatted_list": formatted_list,
                "total_count": len(files),
                "prefix": prefix,
                "message": f"'{prefix}' 경로에서 {len(files)}개의 파일을 조회했습니다."
            }
        else:
            return handle_mcp_error(Exception(f"Storage 파일 목록 조회 실패: {response.get('message', '알 수 없는 오류') if isinstance(response, dict) else '응답 없음'}"), "list_storage")
            
    except Exception as e:
        log_operation("list_storage", "storage", {"error": str(e), "prefix": prefix}, False)
        return handle_mcp_error(e, "list_storage")

# =================
# 🔥 CORE APIs
# =================

def get_firebase_project_info() -> dict:
    """
    Firebase 프로젝트 정보를 조회합니다.
    Firebase MCP 호출 규칙을 적용하여 모든 프로젝트 정보 조회를 MCP를 통해 처리합니다.
    """
    try:
        # 🚨 0.1 Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "project_info"):
            log_operation("get_project_info", "project_info", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 🚨 0.2-2 적절한 Firebase MCP 함수 호출
        response = firebase_client.get_project_info()
        
        # 🚨 0.2-3 호출 결과 확인 및 검증
        is_valid = validate_response(response)
        
        if is_valid and response.get("success"):
            project_data = response.get("data", {})
            
            log_operation("get_project_info", "project_info", {"project_id": project_data.get('projectId', 'Unknown')}, True)
            return {
                "status": "success",
                "project_info": project_data,
                "message": f"프로젝트 '{project_data.get('projectId', 'Unknown')}'에 연결되었습니다."
            }
        else:
            return handle_mcp_error(Exception(f"프로젝트 정보 조회 실패: {response.get('message', '알 수 없는 오류') if isinstance(response, dict) else '응답 없음'}"), "get_project_info")
            
    except Exception as e:
        log_operation("get_project_info", "project_info", {"error": str(e)}, False)
        return handle_mcp_error(e, "get_project_info")

def list_firestore_collections() -> dict:
    """Firestore의 모든 컬렉션 목록을 조회합니다."""
    try:
        if not validate_mcp_call("collection_list", "firestore"):
            log_operation("list_collections", "firestore", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다."
            }

        response = firebase_client.list_collections()
        is_valid = validate_response(response)
        
        if is_valid and response.get("success"):
            collections = response.get("data", {}).get("collections", [])
            
            formatted_list = "📋 Firestore 컬렉션 목록:\n"
            for i, collection in enumerate(collections, 1):
                formatted_list += f"{i}. {collection}\n"
            
            log_operation("list_collections", "firestore", {"count": len(collections)}, True)
            return {
                "status": "success",
                "collections": collections,
                "formatted_list": formatted_list,
                "total_count": len(collections),
                "message": f"총 {len(collections)}개의 컬렉션이 있습니다."
            }
        else:
            return handle_mcp_error(Exception(f"컬렉션 목록 조회 실패"), "list_collections")
            
    except Exception as e:
        log_operation("list_collections", "firestore", {"error": str(e)}, False)
        return handle_mcp_error(e, "list_collections")

def query_any_collection(collection_name: str, limit: int = 10) -> dict:
    """지정된 컬렉션을 쿼리합니다."""
    try:
        if not validate_mcp_call("data_query", collection_name):
            log_operation("query_collection", collection_name, {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다."
            }

        response = firebase_client.query_collection(collection_name, limit=limit)
        
        if not validate_response(response):
            error_msg = handle_mcp_error(Exception("컬렉션 쿼리 실패"), "query_collection")
            return {
                "status": "error",
                "message": error_msg
            }
        
        if response and response.get("success"):
            data = response.get("data", {})
            documents = data.get("documents", [])
            
            log_operation("query_collection", collection_name, {"count": len(documents)}, True)
            return {
                "status": "success",
                "collection": collection_name,
                "count": len(documents),
                "data": data,
                "raw_data": response,
                "message": f"{collection_name} 컬렉션에서 {len(documents)}개 문서를 조회했습니다."
            }
        else:
            error_msg = handle_mcp_error(Exception("쿼리 응답 오류"), "query_collection")
            return {
                "status": "error",
                "message": error_msg
            }
            
    except Exception as e:
        log_operation("query_collection", collection_name, {"error": str(e)}, False)
        error_msg = handle_mcp_error(e, "query_collection")
        return {
            "status": "error",
            "message": error_msg
        }

def list_storage_files(prefix: str = "") -> dict:
    """Storage 파일 목록을 조회합니다."""
    try:
        if not validate_mcp_call("data_query", "storage", {"prefix": prefix}):
            log_operation("list_storage", "storage", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다."
            }

        response = firebase_client.list_files(prefix=prefix)
        is_valid = validate_response(response)
        
        if is_valid and response.get("success"):
            files = response.get("data", {}).get("files", [])
            
            formatted_list = f"📁 Firebase Storage 파일 목록 (prefix: '{prefix}'):\n"
            formatted_list += f"총 {len(files)}개의 파일이 있습니다.\n\n"
            
            for i, file_info in enumerate(files, 1):
                name = file_info.get("name", "Unknown")
                size = file_info.get("size", "Unknown")
                updated = file_info.get("updated", "Unknown")
                
                formatted_list += f"{i}. {name}\n"
                formatted_list += f"   크기: {size} bytes\n"
                formatted_list += f"   수정일: {updated}\n"
                formatted_list += f"   {'-' * 30}\n\n"
            
            log_operation("list_storage", "storage", {"files_count": len(files), "prefix": prefix}, True)
            return {
                "status": "success",
                "files": files,
                "formatted_list": formatted_list,
                "total_count": len(files),
                "prefix": prefix,
                "message": f"'{prefix}' 경로에서 {len(files)}개의 파일을 조회했습니다."
            }
        else:
            return handle_mcp_error(Exception(f"Storage 파일 목록 조회 실패"), "list_storage")
            
    except Exception as e:
        log_operation("list_storage", "storage", {"error": str(e), "prefix": prefix}, False)
        return handle_mcp_error(e, "list_storage")

# =================
# 🔍 SMART SEARCH
# =================

def smart_search(search_query: str, collection_path: str = None, 
                search_fields: list = None, search_type: str = 'fuzzy',
                threshold: float = 0.3, sort_by: str = 'score',
                sort_field: str = '', sort_direction: str = 'desc',
                limit: int = 20) -> dict:
    """
    범용 스마트 검색을 수행합니다.
    
    Args:
        search_query: 검색어 (필수)
        collection_path: 검색할 특정 컬렉션 (선택)
        search_fields: 검색할 필드 목록 (선택)
        search_type: 검색 방식 (fuzzy/exact/regex)
        threshold: 유사도 임계값 (0.0~1.0)
        sort_by: 정렬 기준 (score/field)
        sort_field: 정렬 기준 필드명
        sort_direction: 정렬 방향 (asc/desc)
        limit: 검색 결과 제한
    """
    try:
        if not validate_mcp_call("smart_search", collection_path or "all"):
            return {
                "status": "error",
                "message": "스마트 검색 호출 검증 실패"
            }

        response = firebase_client.smart_search(
            search_query=search_query,
            collection_path=collection_path,
            search_fields=search_fields,
            search_type=search_type,
            threshold=threshold,
            sort_by=sort_by,
            sort_field=sort_field,
            sort_direction=sort_direction,
            limit=limit
        )
        
        if not validate_response(response):
            return {
                "status": "error",
                "message": "검색 결과 검증 실패"
            }
            
        if response.get("success"):
            data = response.get("data", {})
            results = data.get("results", [])
            
            log_operation("smart_search", collection_path or "all", {
                "query": search_query,
                "found": len(results)
            }, True)
            
            return {
                "status": "success",
                "results": results,
                "query_info": data.get("query", {}),
                "total_found": data.get("totalFound", 0),
                "has_more": data.get("hasMore", False),
                "message": f"검색어 '{search_query}'에 대해 {len(results)}개의 결과를 찾았습니다."
            }
        else:
            return {
                "status": "error",
                "message": response.get("message", "검색 실패")
            }
            
    except Exception as e:
        log_operation("smart_search", collection_path or "all", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": f"검색 중 오류 발생: {str(e)}"
        }

def _format_schedules_data(documents: list) -> str:
    """
    schedules 컬렉션 데이터를 사용자가 읽기 쉬운 형태로 포맷팅합니다.
    
    Args:
        documents: Firebase에서 조회한 문서 리스트
        
    Returns:
        str: 포맷팅된 스케줄 목록 문자열
    """
    import json
    
    if not documents:
        return "📅 등록된 스케줄이 없습니다.\n\n새로운 스케줄을 등록하려면 '주소명 날짜 작업유형 등록해줘' 형태로 요청해주세요."
    
    formatted_list = "📅 **스케줄 컬렉션 정리**\n\n"
    
    for i, doc in enumerate(documents, 1):
        doc_id = doc.get("id", "Unknown")
        doc_data = doc.get("data", {})
        
        address = doc_data.get("address", "주소 없음")
        color = doc_data.get("color", "#4A90E2")
        events_json_str = doc_data.get("eventsJson", "{}")
        
        formatted_list += f"**{i}. {address}**\n"
        formatted_list += f"   - 색상: {color}\n"
        formatted_list += f"   - 문서ID: {doc_id}\n"
        
        # eventsJson 파싱
        try:
            events_data = json.loads(events_json_str) if events_json_str else {}
        except json.JSONDecodeError:
            events_data = {}
        
        if events_data:
            formatted_list += f"   - 이벤트 수: {len(events_data)}개\n"
            formatted_list += f"   - 이벤트 목록:\n"
            
            # 이벤트를 날짜순으로 정렬
            sorted_events = sorted(events_data.items(), key=lambda x: x[0].split("_")[0] if "_" in x[0] else x[0])
            
            for event_key, event_data in sorted_events[:5]:  # 최대 5개만 표시
                event_date = event_key.split("_")[0] if "_" in event_key else event_key
                event_title = event_data.get("title", "")
                event_memo = event_data.get("memo", "")
                event_status = event_data.get("status", "scheduled")
                
                status_icon = "✅" if event_status == "completed" else "⏰"
                
                formatted_list += f"     {status_icon} {event_date}: {event_memo}\n"
                if event_title:
                    formatted_list += f"        제목: {event_title}\n"
            
            if len(events_data) > 5:
                formatted_list += f"     ... (추가 {len(events_data) - 5}개 이벤트)\n"
        else:
            formatted_list += f"   - 이벤트: 없음\n"
        
        formatted_list += "\n"
    
    formatted_list += f"**총 {len(documents)}개의 스케줄 카테고리가 등록되어 있습니다.**\n"
    formatted_list += "\n💡 상세 스케줄 관리가 필요하면 스케줄 관리 전용 함수들을 사용해주세요."
    
    return formatted_list 