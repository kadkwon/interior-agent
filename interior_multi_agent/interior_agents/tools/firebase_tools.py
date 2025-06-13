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

def query_schedule_collection(limit: int = 50) -> dict:
    """
    Firebase Firestore의 schedule 컬렉션을 조회합니다.
    Firebase MCP 호출 규칙을 적용하여 모든 데이터 조회를 MCP를 통해 처리합니다.
    
    Args:
        limit: 조회할 일정 수 제한 (기본값: 50)
        
    Returns:
        dict: 일정 목록과 포맷팅된 결과
    """
    try:
        # 🚨 0.1 Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "schedule", {"limit": limit}):
            log_operation("query_schedule", "schedule", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 🚨 0.2-1 사용자 요청 분석 및 필요한 Firebase 컬렉션 식별
        log_operation("query_schedule", "schedule", {"step": "MCP 호출 시작", "limit": limit}, True)
        
        # 🚨 0.2-2 적절한 Firebase MCP 함수 호출
        response = firebase_client.query_collection("schedule", limit=limit)
        
        # 🚨 0.2-3 호출 결과 확인 및 검증
        validated_response = validate_response(response)
        
        if validated_response.get("success"):
            # 포맷팅된 결과 생성
            formatted_result = schedule_formatter.format_schedule_data(validated_response)
            
            log_operation("query_schedule", "schedule", {"limit": limit}, True)
            return {
                "status": "success",
                "formatted_result": formatted_result,
                "raw_data": validated_response,
                "message": f"schedule 컬렉션에서 {limit}개까지 조회했습니다."
            }
        else:
            return handle_mcp_error("query_schedule", f"schedule 컬렉션 조회 실패: {validated_response.get('message', '알 수 없는 오류')}")
        
    except Exception as e:
        log_operation("query_schedule", "schedule", {"error": str(e)}, False)
        return handle_mcp_error("query_schedule", f"schedule 컬렉션 조회 중 오류 발생: {str(e)}")

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
        validated_response = validate_response(response)
        
        if validated_response.get("success"):
            project_data = validated_response.get("data", {})
            
            log_operation("get_project_info", "project_info", {"project_id": project_data.get('projectId', 'Unknown')}, True)
            return {
                "status": "success",
                "project_info": project_data,
                "message": f"프로젝트 '{project_data.get('projectId', 'Unknown')}'에 연결되었습니다."
            }
        else:
            return handle_mcp_error("get_project_info", f"프로젝트 정보 조회 실패: {validated_response.get('message', '알 수 없는 오류')}")
            
    except Exception as e:
        log_operation("get_project_info", "project_info", {"error": str(e)}, False)
        return handle_mcp_error("get_project_info", f"Firebase 프로젝트 정보 조회 중 오류: {str(e)}")

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
        validated_response = validate_response(response)
        
        if validated_response.get("success"):
            collections = validated_response.get("data", {}).get("collections", [])
            
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
            return handle_mcp_error("list_collections", f"컬렉션 목록 조회 실패: {validated_response.get('message', '알 수 없는 오류')}")
            
    except Exception as e:
        log_operation("list_collections", "firestore", {"error": str(e)}, False)
        return handle_mcp_error("list_collections", f"컬렉션 목록 조회 중 오류: {str(e)}")

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
        validated_response = validate_response(response)
        
        if validated_response.get("success"):
            files = validated_response.get("data", {}).get("files", [])
            
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
            return handle_mcp_error("list_storage", f"Storage 파일 목록 조회 실패: {validated_response.get('message', '알 수 없는 오류')}")
            
    except Exception as e:
        log_operation("list_storage", "storage", {"error": str(e), "prefix": prefix}, False)
        return handle_mcp_error("list_storage", f"Firebase Storage 파일 목록 조회 중 오류: {str(e)}") 