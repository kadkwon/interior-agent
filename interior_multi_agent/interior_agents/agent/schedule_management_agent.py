from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import time
import json
import re
import logging
from ..client.mcp_client import FirebaseMCPClient

# 로깅 설정
logger = logging.getLogger(__name__)

# Firebase MCP 규칙 import
try:
    from ..firebase_mcp_rules import (
        validate_mcp_call, handle_mcp_error,
        validate_schedule_memo, validate_response, log_operation
    )
    MCP_RULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Firebase MCP 규칙 모듈 로드 실패: {e}")
    MCP_RULES_AVAILABLE = False
    
    # 폴백 함수들 정의
    def validate_mcp_call(*args, **kwargs): return True
    def handle_mcp_error(error, context=""): return str(error)
    def validate_schedule_memo(*args, **kwargs): return True
    def validate_response(response): return response is not None
    def log_operation(*args, **kwargs): pass

# Firebase 도구 import
try:
    from ..tools.firebase_tools import query_any_collection
    FIREBASE_TOOLS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Firebase 도구 모듈 로드 실패: {e}")
    FIREBASE_TOOLS_AVAILABLE = False
    
    # 폴백 함수
    def query_any_collection(collection_name: str, conditions: list = None) -> dict:
        return {"status": "error", "message": "Firebase 도구를 사용할 수 없습니다."}

# Firebase 클라이언트 import
try:
    from ..client.firebase_client import firebase_client
    FIREBASE_CLIENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Firebase 클라이언트 로드 실패: {e}")
    FIREBASE_CLIENT_AVAILABLE = False
    
    # 폴백 클라이언트 클래스
    class MockFirebaseClient:
        def update_document(self, doc_path: str, data: dict) -> dict:
            return {"status": "error", "message": "Firebase 클라이언트를 사용할 수 없습니다."}
    
    firebase_client = MockFirebaseClient()

# ==============================================================================
# 🔧 공통 헬퍼 함수들
# ==============================================================================

# 스케줄 컬렉션 특수 카테고리 (주소가 아닌 선택 가능한 항목들)
SPECIAL_SCHEDULE_CATEGORIES = {
    "개인 일정",
    "하자보수", 
    "고객 상담"
}

def _parse_date_string(date_str: str) -> str:
    """다양한 날짜 형식을 YYYY-MM-DD로 변환
    
    Args:
        date_str: 입력 날짜 문자열 ("6월 15일", "6/15", "2025-06-15" 등)
        
    Returns:
        str: YYYY-MM-DD 형식의 날짜 문자열
    """
    current_year = datetime.now().year
    
    # 이미 YYYY-MM-DD 형식인 경우
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # "6월 15일" 형식
    month_day_match = re.match(r'(\d{1,2})월\s*(\d{1,2})일', date_str)
    if month_day_match:
        month = int(month_day_match.group(1))
        day = int(month_day_match.group(2))
        return f"{current_year}-{month:02d}-{day:02d}"
    
    # "6/15" 형식
    slash_match = re.match(r'(\d{1,2})/(\d{1,2})$', date_str)
    if slash_match:
        month = int(slash_match.group(1))
        day = int(slash_match.group(2))
        return f"{current_year}-{month:02d}-{day:02d}"
    
    # "15일" 형식 (현재 월 기준)
    day_only_match = re.match(r'(\d{1,2})일$', date_str)
    if day_only_match:
        current_month = datetime.now().month
        day = int(day_only_match.group(1))
        return f"{current_year}-{current_month:02d}-{day:02d}"
    
    # 파싱 실패시 오늘 날짜 반환
    logger.warning(f"날짜 파싱 실패: {date_str}, 오늘 날짜 사용")
    return datetime.now().strftime("%Y-%m-%d")

def _find_schedule_document(address: str) -> Tuple[bool, Optional[str], Optional[dict]]:
    """address로 schedules 문서 찾기
    
    Args:
        address: 찾을 주소 또는 특수 카테고리 ("개인 일정", "하자보수", "고객 상담")
        
    Returns:
        tuple: (찾음 여부, 문서 ID, 문서 데이터)
    """
    try:
        # MCP 규칙 검증
        if not validate_mcp_call("query_collection", "schedules", {"address": address}):
            return False, None, None
        
        # schedules 컬렉션 조회
        result = query_any_collection("schedules")
        
        if not validate_response(result) or result.get("status") != "success":
            logger.error(f"스케줄 컬렉션 조회 실패: {result}")
            return False, None, None
        
        documents = result.get("data", {}).get("documents", [])
        
        # address 필드로 문서 검색 (실제 주소 또는 특수 카테고리)
        for doc in documents:
            doc_data = doc.get("data", {})
            if doc_data.get("address") == address:
                doc_id = doc.get("id")
                log_operation("find_schedule_document", "success", {"address": address, "doc_id": doc_id, "type": "found"})
                return True, doc_id, doc_data
        
        # 특수 카테고리인 경우 자동 생성 가능하다고 알림
        if address in SPECIAL_SCHEDULE_CATEGORIES:
            log_operation("find_schedule_document", "special_category", {"address": address, "type": "special"})
            return False, None, {"is_special_category": True}
        
        log_operation("find_schedule_document", "not_found", {"address": address, "type": "not_found"})
        return False, None, None

    except Exception as e:
        error_msg = handle_mcp_error(e, f"문서 검색 중 오류 (address: {address})")
        logger.error(error_msg)
        return False, None, None

def _update_events_json(doc_id: str, updated_events: dict) -> dict:
    """eventsJson 필드를 안전하게 업데이트
    
    Args:
        doc_id: 업데이트할 문서 ID
        updated_events: 업데이트할 이벤트 딕셔너리
        
    Returns:
        dict: 업데이트 결과
    """
    try:
        # MCP 규칙 검증
        if not validate_mcp_call("update", "schedules", {"doc_id": doc_id, "events": updated_events}):
            return {"status": "error", "message": "MCP 규칙 검증 실패"}
        
        # JSON 문자열로 변환
        events_json_str = json.dumps(updated_events, ensure_ascii=False)
        
        # 문서 업데이트
        doc_path = f"schedules/{doc_id}"
        update_data = {
            "eventsJson": events_json_str,
            "updatedAt": datetime.now().isoformat()
        }
        
        result = firebase_client.update_document(doc_path, update_data)
        
        if validate_response(result):
            log_operation("update_events_json", "success", {"doc_id": doc_id, "events_count": len(updated_events)})
            return {"status": "success", "data": result}
        else:
            return {"status": "error", "message": "문서 업데이트 실패"}
        
    except Exception as e:
        error_msg = handle_mcp_error(e, f"eventsJson 업데이트 중 오류 (doc_id: {doc_id})")
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

# ==============================================================================
# 🎯 핵심 기능 5가지
# ==============================================================================

client = FirebaseMCPClient()

def register_new_schedule(address_id: str, date: str, description: str, category: str = "일반") -> Dict[str, Any]:
    """
    새로운 일정을 등록합니다.
    
    Args:
        address_id: 현장 주소 ID
        date: 일정 날짜 (YYYY-MM-DD)
        description: 일정 설명
        category: 일정 카테고리
        
    Returns:
        Dict: 등록된 일정 정보
    """
    doc_data = {
        "address_id": address_id,
        "date": date,
        "description": description,
        "category": category,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return client.create_document("schedules", doc_data)

def update_existing_schedule(schedule_id: str, date: str = None, description: str = None, category: str = None) -> Dict[str, Any]:
    """
    기존 일정을 업데이트합니다.
    
    Args:
        schedule_id: 일정 문서 ID
        date: 새로운 날짜 (선택)
        description: 새로운 설명 (선택)
        category: 새로운 카테고리 (선택)
        
    Returns:
        Dict: 업데이트된 일정 정보
    """
    update_data = {}
    if date is not None:
        update_data["date"] = date
    if description is not None:
        update_data["description"] = description
    if category is not None:
        update_data["category"] = category
    update_data["updated_at"] = datetime.now().isoformat()
    
    return client.update_document("schedules", schedule_id, update_data)

def delete_schedule_record(schedule_id: str) -> Dict[str, Any]:
    """
    일정을 삭제합니다.
    
    Args:
        schedule_id: 삭제할 일정 문서 ID
        
    Returns:
        Dict: 삭제 결과
    """
    return client.delete_document("schedules", schedule_id)

def list_schedules_by_date(date: str) -> List[Dict[str, Any]]:
    """
    특정 날짜의 모든 일정을 조회합니다.
    
    Args:
        date: 조회할 날짜 (YYYY-MM-DD)
        
    Returns:
        List[Dict]: 일정 목록
    """
    return client.query_documents("schedules", "date", "==", date)

def list_schedules_by_address(address_id: str) -> List[Dict[str, Any]]:
    """
    특정 주소의 모든 일정을 조회합니다.
    
    Args:
        address_id: 현장 주소 ID
        
    Returns:
        List[Dict]: 일정 목록
    """
    return client.query_documents("schedules", "address_id", "==", address_id)

# ==============================================================================
# 🔧 모듈 초기화 로깅
# ==============================================================================

logger.info("📅 스케줄 관리 에이전트가 초기화되었습니다.")
logger.info(f"   - MCP 규칙: {'✅ 사용 가능' if MCP_RULES_AVAILABLE else '⚠️ 폴백 모드'}")
logger.info(f"   - Firebase 도구: {'✅ 사용 가능' if FIREBASE_TOOLS_AVAILABLE else '⚠️ 폴백 모드'}")
logger.info(f"   - Firebase 클라이언트: {'✅ 사용 가능' if FIREBASE_CLIENT_AVAILABLE else '⚠️ 폴백 모드'}")
logger.info("   - 제공 기능: 스케줄 등록/수정/삭제/날짜별조회/주소별조회 (5개 도구)")
logger.info(f"   - 특수 카테고리: {', '.join(SPECIAL_SCHEDULE_CATEGORIES)}") 