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
        operation_type: 작업 유형 ('read', 'write', 'update', 'delete', 'data_query', 'collection_list')
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
            'read', 'write', 'update', 'delete',
            'data_query', 'collection_list', 'project_info',
            'address_register', 'address_update', 'address_delete',
            'query_collection', 'list_collections',
            'single_document', 'advanced_list'  # 새로운 MCP 호환 작업 유형
        ]
        if operation_type not in valid_operations:
            raise MCPValidationError(f"지원되지 않는 작업 유형: {operation_type}")
        
        # 컬렉션 이름 검증 (문자열이 아닌 경우도 허용)
        if isinstance(collection, str):
            valid_collections = ['addressesJson', 'schedules', 'sites', 'payments']
            if collection not in valid_collections:
                logger.warning(f"알 수 없는 컬렉션: {collection}")
        
        # 쓰기 작업 시 데이터 검증
        if operation_type in ['write', 'update'] and not data:
            raise MCPValidationError("쓰기/업데이트 작업에는 데이터가 필요합니다.")
        
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
    for attempt in range(max_retries):
        try:
            # 1. 사용자 요청 분석 및 필요한 Firebase 컬렉션 식별
            logger.info(f"MCP 호출 시도 {attempt + 1}/{max_retries}: {func.__name__}")
            
            # 2. 적절한 Firebase MCP 함수 호출
            result = func(*args, **kwargs)
            
            # 3. 호출 결과 확인 및 검증
            if validate_response(result):
                # 4. 검증된 결과를 바탕으로 응답
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
    
    # 오류 유형별 대응
    if isinstance(error, MCPValidationError):
        return f"데이터 검증 오류: {str(error)}"
    elif isinstance(error, MCPCallError):
        return "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    else:
        return "예상치 못한 오류가 발생했습니다. 관리자에게 문의하세요."

def safe_remove_data(collection: str, doc_id: str, data_type: str = "content") -> Dict[str, Any]:
    """
    0.4 데이터 제거 처리 방식
    
    Args:
        collection: 컬렉션 이름
        doc_id: 문서 ID
        data_type: 제거할 데이터 유형
    
    Returns:
        Dict[str, Any]: 업데이트할 데이터
    """
    try:
        if collection == "schedules":
            # schedules 컬렉션: eventsJson 필드를 빈 객체로 업데이트
            return {"eventsJson": "{}"}
        
        elif collection == "addressesJson":
            # addressesJson 컬렉션: 주소 문서는 유지하되 상세 정보만 초기화
            return {
                "success": True,
                "data": {
                    "dataJson": "{}",
                    "description": "",
                    "updated_at": datetime.now().isoformat()
                }
            }
        
        else:
            # 기타 컬렉션: 기본 초기화
            return {
                "data": "{}",
                "status": "removed",
                "updated_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"안전한 데이터 제거 실패: {e}")
        return {"error": "데이터 제거 중 오류 발생"}

def validate_schedule_memo(schedule_type: str, memo: str, title: str = "") -> bool:
    """
    0.5 특수 일정 메모 등록 규칙
    
    Args:
        schedule_type: 일정 유형 ('개인일정', '하자보수', '고객상담')
        memo: 메모 내용
        title: 제목 (특수 일정의 경우 빈 문자열이어야 함)
    
    Returns:
        bool: 검증 통과 여부
    """
    try:
        special_types = ['개인일정', '하자보수', '고객상담', '고객 상담', '개인 일정', '하자 보수']
        
        if schedule_type in special_types:
            # 특수 일정: memo 필드 필수, title은 빈 문자열
            if not memo or memo.strip() == "":
                raise MCPValidationError(f"{schedule_type}에는 memo 필드가 필수입니다.")
            
            if title and title.strip() != "":
                logger.warning(f"{schedule_type}의 title은 빈 문자열로 처리됩니다.")
            
            # 내용별 검증
            if schedule_type in ['개인일정', '개인 일정']:
                if len(memo) < 5:
                    raise MCPValidationError("개인일정 memo는 최소 5자 이상이어야 합니다.")
            
            elif schedule_type in ['하자보수', '하자 보수']:
                required_keywords = ['보수', '수리', '교체', '점검']
                if not any(keyword in memo for keyword in required_keywords):
                    logger.warning("하자보수 memo에 작업 내용을 명확히 기술하세요.")
            
            elif schedule_type in ['고객상담', '고객 상담']:
                if '상담' not in memo:
                    logger.warning("고객상담 memo에 상담 내용을 포함하세요.")
        
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
        
        # 문자열 응답
        if isinstance(response, str):
            if response.strip() == "":
                return False
            # "error"가 포함되어도 정상 응답일 수 있으므로 제거
        
        # 딕셔너리 응답 (Firebase 응답 형식)
        elif isinstance(response, dict):
            # Firebase success 필드 확인
            if "success" in response:
                return response.get("success") == True
            
            # 명시적 에러 상태 확인
            if response.get("status") == "error":
                return False
            
            # error 필드가 있으면 실패
            if "error" in response and response.get("error"):
                return False
                
            # 기본적으로 딕셔너리 응답은 성공으로 간주
            return True
        
        # 리스트 응답
        elif isinstance(response, list):
            # 빈 리스트도 유효한 응답으로 간주
            return True
        
        # 기타 응답도 성공으로 간주
        return True
        
    except Exception as e:
        logger.error(f"응답 검증 실패: {e}")
        return False

def log_operation(operation: str, collection: str, result: Any, success: bool = True) -> None:
    """
    작업 로깅 함수
    
    Args:
        operation: 수행된 작업
        collection: 대상 컬렉션
        result: 작업 결과
        success: 성공 여부
    """
    timestamp = datetime.now().isoformat()
    status = "SUCCESS" if success else "FAILED"
    
    log_entry = {
        "timestamp": timestamp,
        "operation": operation,
        "collection": collection,
        "status": status,
        "result_preview": str(result)[:100] if result else "None"
    }
    
    if success:
        logger.info(f"작업 성공: {json.dumps(log_entry, ensure_ascii=False)}")
    else:
        logger.error(f"작업 실패: {json.dumps(log_entry, ensure_ascii=False)}")

# 사용 예시 및 테스트 함수들
def test_mcp_rules():
    """MCP 규칙 테스트 함수"""
    print("🔥 Firebase MCP 규칙 테스트 시작")
    
    # 1. 검증 테스트
    assert validate_mcp_call("read", "addressesJson") == True
    assert validate_mcp_call("", "addressesJson") == False
    
    # 2. 안전한 데이터 제거 테스트
    schedule_remove = safe_remove_data("schedules", "test_doc")
    assert schedule_remove["eventsJson"] == "{}"
    
    # 3. 특수 일정 메모 검증 테스트
    assert validate_schedule_memo("개인일정", "다이슨드라이기 수리", "") == True
    assert validate_schedule_memo("하자보수", "욕실 타일 들뜸 보수", "") == True
    assert validate_schedule_memo("고객상담", "리모델링 상담 - 주방 확장", "") == True
    
    # 4. 응답 검증 테스트
    assert validate_response({"name": "테스트", "address": "서울시"}) == True
    assert validate_response({"error": "failed"}) == False
    
    print("✅ 모든 MCP 규칙 테스트 통과!")

if __name__ == "__main__":
    test_mcp_rules() 