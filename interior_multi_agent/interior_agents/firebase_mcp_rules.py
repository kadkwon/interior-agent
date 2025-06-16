"""
Firebase MCP 호출 규칙 구현 모듈

0.1 Firebase MCP 호출 의무화
0.2 Firebase MCP 호출 확인 절차
0.3 실패 시 대응 방법
0.4 데이터 제거 처리 방식
0.5 특수 일정 메모 등록 규칙
12.1/12.2 오류 처리 및 데이터 검증 의무화
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from .client.mcp_client import FirebaseMCPClient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPValidationError(Exception):
    """MCP 검증 실패 시 발생하는 예외"""
    pass

class MCPCallError(Exception):
    """MCP 호출 실패 시 발생하는 예외"""
    pass

def validate_mcp_call(operation_type: str, collection: str, data: Optional[Dict[str, Any]] = None) -> bool:
    """
    0.1 Firebase MCP 호출 의무화 검증
    
    Args:
        operation_type: 작업 유형
        collection: Firebase 컬렉션 이름
        data: 처리할 데이터 (선택적)
    
    Returns:
        bool: 검증 통과 여부
    """
    try:
        # 필수 매개변수 검증
        if not operation_type or not collection:
            raise MCPValidationError("작업 유형과 컬렉션이 필요합니다.")
        
        # 지원되는 작업 유형 검증
        valid_operations = [
            # Firestore 작업
            'firestore_get_document',
            'firestore_list_documents',
            'firestore_query_collection',
            'firestore_create_document',
            'firestore_update_document',
            'firestore_delete_document',
            
            # Storage 작업
            'storage_list_files',
            'storage_upload_file',
            'storage_download_file',
            'storage_delete_file',
            
            # Auth 작업
            'auth_get_user',
            'auth_create_user',
            'auth_update_user',
            'auth_delete_user',
            
            # 프로젝트 관리
            'firebase_get_project_info',
            'firebase_list_projects',
            'firebase_deploy_functions'
        ]
        
        if operation_type not in valid_operations:
            raise MCPValidationError(f"지원되지 않는 작업 유형: {operation_type}")
        
        # 컬렉션 이름 검증
        valid_collections = [
            'addressesJson',
            'schedules',
            'sites',
            'payments',
            'project_info',
            'firestore'
        ]
        
        if isinstance(collection, str) and collection not in valid_collections:
            logger.warning(f"알 수 없는 컬렉션: {collection}")
        
        # 데이터가 필요한 작업 검증
        operations_requiring_data = [
            'firestore_create_document',
            'firestore_update_document',
            'firestore_query_collection',
            'storage_upload_file',
            'storage_download_file',
            'auth_create_user',
            'auth_update_user'
        ]
        
        if operation_type in operations_requiring_data and not data:
            raise MCPValidationError(f"{operation_type} 작업에는 데이터가 필요합니다.")
        
        logger.info(f"MCP 호출 검증 통과: {operation_type} on {collection}")
        return True
        
    except Exception as e:
        logger.error(f"MCP 호출 검증 실패: {e}")
        return False

def execute_mcp_sequence(func, *args, max_retries: int = 3, **kwargs) -> Tuple[bool, Any]:
    """
    0.2 Firebase MCP 호출 확인 절차 & 0.3 실패 시 대응 방법
    
    Args:
        func: 실행할 MCP 함수
        max_retries: 최대 재시도 횟수
        *args, **kwargs: 함수 매개변수
    
    Returns:
        Tuple[bool, Any]: (성공 여부, 결과 데이터)
    """
    client = FirebaseMCPClient()
    
    for attempt in range(max_retries):
        try:
            logger.info(f"MCP 호출 시도 {attempt + 1}/{max_retries}: {func.__name__}")
            
            result = func(*args, **kwargs)
            
            if validate_response(result):
                logger.info(f"MCP 호출 성공: {func.__name__}")
                return True, result
            else:
                raise MCPCallError("응답 검증 실패")
                
        except Exception as e:
            logger.error(f"MCP 호출 실패 (시도 {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"MCP 호출 최종 실패: {func.__name__}")
                return False, "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    
    return False, "최대 재시도 횟수 초과"

def handle_mcp_error(error: Exception, context: str = "") -> str:
    """
    12.1 오류 처리 의무화
    
    Args:
        error: 발생한 오류
        context: 오류 발생 컨텍스트
    
    Returns:
        str: 사용자에게 표시할 오류 메시지
    """
    error_msg = f"MCP 오류 발생 {context}: {str(error)}"
    logger.error(error_msg)
    
    if isinstance(error, MCPValidationError):
        return f"데이터 검증 오류: {str(error)}"
    elif isinstance(error, MCPCallError):
        return "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    else:
        return "예상치 못한 오류가 발생했습니다. 관리자에게 문의하세요."

def safe_remove_data(collection: str, doc_id: str) -> Dict[str, Any]:
    """
    0.4 데이터 제거 처리 방식
    
    Args:
        collection: 컬렉션 이름
        doc_id: 문서 ID
    
    Returns:
        Dict[str, Any]: 업데이트할 데이터
    """
    client = FirebaseMCPClient()
    
    try:
        if collection == "schedules":
            return client.update_document(collection, doc_id, {"eventsJson": "{}"})
        
        elif collection == "addressesJson":
            return client.update_document(collection, doc_id, {
                "dataJson": "{}",
                "description": "",
                "updated_at": datetime.now().isoformat()
            })
        
        else:
            return client.delete_document(collection, doc_id)
            
    except Exception as e:
        logger.error(f"데이터 제거 실패: {e}")
        return {
            "success": False,
            "error": str(e),
            "collection": collection,
            "doc_id": doc_id
        }

def validate_schedule_memo(schedule_type: str, memo: str, title: str = "") -> bool:
    """
    0.5 특수 일정 메모 등록 규칙
    
    Args:
        schedule_type: 일정 유형
        memo: 메모 내용
        title: 일정 제목
    
    Returns:
        bool: 검증 통과 여부
    """
    try:
        if not schedule_type or not memo:
            return False
            
        if schedule_type == "payment":
            required_fields = ["금액", "결제방법", "계약내용"]
            for field in required_fields:
                if field not in memo:
                    return False
                    
        elif schedule_type == "visit":
            if len(memo) < 10:
                return False
                
        elif schedule_type == "contract":
            if not title or "계약" not in title:
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"일정 메모 검증 실패: {e}")
        return False

def validate_response(response: Any) -> bool:
    """
    12.2 데이터 검증 의무화
    
    Args:
        response: 검증할 응답 데이터
    
    Returns:
        bool: 검증 통과 여부
    """
    try:
        if response is None:
            return False
            
        if isinstance(response, dict):
            if "error" in response:
                return False
                
            if "success" in response and not response["success"]:
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"응답 검증 실패: {e}")
        return False

def log_operation(operation: str, collection: str, result: Any, success: bool = True) -> None:
    """
    작업 로깅
    
    Args:
        operation: 작업 유형
        collection: 컬렉션 이름
        result: 작업 결과
        success: 성공 여부
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "collection": collection,
        "success": success,
        "result": result
    }
    
    logger.info(json.dumps(log_data, ensure_ascii=False, indent=2))

def test_mcp_rules():
    """MCP 규칙 테스트"""
    client = FirebaseMCPClient()
    
    # 1. 프로젝트 정보 조회 테스트
    project_info = client.get_project_info()
    assert validate_response(project_info)
    
    # 2. 문서 생성 및 조회 테스트
    test_data = {"test": "data"}
    doc = client.add_document("test_collection", test_data)
    assert validate_response(doc)
    
    # 3. 문서 업데이트 테스트
    update_data = {"updated": True}
    update = client.update_document("test_collection", doc["id"], update_data)
    assert validate_response(update)
    
    # 4. 문서 삭제 테스트
    delete = client.delete_document("test_collection", doc["id"])
    assert validate_response(delete)
    
    logger.info("✅ MCP 규칙 테스트 통과")

if __name__ == "__main__":
    test_mcp_rules() 