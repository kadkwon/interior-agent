from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import time
import json
import re
import logging

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
        if not validate_mcp_call("query_any_collection", collection="schedules", address=address):
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
        if not validate_mcp_call("update_document", doc_id=doc_id, events=updated_events):
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

def register_new_schedule(address: str, date: str, work_type: str, memo: str = "") -> dict:
    """새로운 스케줄을 등록합니다.
    
    Args:
        address: 현장 주소 또는 특수 카테고리 ("개인 일정", "하자보수", "고객 상담")
        date: 스케줄 날짜 (다양한 형식 지원)
        work_type: 작업 유형
        memo: 추가 메모 (선택사항)
        
    Returns:
        dict: 등록 결과
    """
    try:
        # 입력 검증
        if not address or not date:
            return {"status": "error", "message": "❌ 주소와 날짜는 필수 입력사항입니다.", "error_type": "invalid_input"}
        
        # 날짜 파싱
        parsed_date = _parse_date_string(date)
        
        # 스케줄 메모 검증
        final_memo = memo or work_type
        if not validate_schedule_memo(final_memo):
            return {"status": "error", "message": "❌ 유효하지 않은 메모 내용입니다.", "error_type": "invalid_memo"}
        
        # 문서 검색
        found, doc_id, doc_data = _find_schedule_document(address)
        
        if not found:
            # 특수 카테고리인 경우 안내 메시지 변경
            if doc_data and doc_data.get("is_special_category"):
                return {
                    "status": "error",
                    "message": f"❌ '{address}' 카테고리의 스케줄 문서가 존재하지 않습니다. 먼저 해당 카테고리를 생성해주세요.",
                    "error_type": "category_not_found",
                    "available_categories": list(SPECIAL_SCHEDULE_CATEGORIES)
                }
            else:
                return {
                    "status": "error", 
                    "message": f"❌ '{address}' 주소를 찾을 수 없습니다. 주소를 먼저 등록해주세요.",
                    "error_type": "address_not_found",
                    "hint": f"특수 카테고리를 사용하려면: {', '.join(SPECIAL_SCHEDULE_CATEGORIES)}"
                }
        
        # 기존 eventsJson 파싱
        events_json_str = doc_data.get("eventsJson", "{}")
        try:
            existing_events = json.loads(events_json_str)
        except json.JSONDecodeError:
            existing_events = {}
        
        # 새 이벤트 생성
        event_key = f"{parsed_date}_{int(time.time() * 1000)}"
        event_data = {
            "title": "",
            "status": "scheduled",
            "memo": final_memo
        }
        
        # 이벤트 추가
        existing_events[event_key] = event_data
        
        # 문서 업데이트
        update_result = _update_events_json(doc_id, existing_events)
        
        if update_result.get("status") == "success":
            return {
                "status": "success",
                "message": f"✅ {address}에 {parsed_date} 스케줄이 등록되었습니다.",
                "data": {
                    "address": address,
                    "date": parsed_date,
                    "work_type": work_type,
                    "memo": final_memo,
                    "action": "registered"
                }
            }
        else:
            return {
                "status": "error",
                "message": f"❌ 스케줄 등록 중 오류가 발생했습니다: {update_result.get('message')}",
                "error_type": "update_failed"
            }
            
    except Exception as e:
        error_msg = handle_mcp_error(e, f"스케줄 등록 중 오류 (address: {address}, date: {date})")
        logger.error(error_msg)
        return {"status": "error", "message": f"❌ 스케줄 등록 실패: {error_msg}", "error_type": "system_error"}

def update_existing_schedule(address: str, date: str, new_memo: str, new_work_type: str = "") -> dict:
    """기존 스케줄을 수정합니다.
    
    Args:
        address: 현장 주소 또는 특수 카테고리 ("개인 일정", "하자보수", "고객 상담")
        date: 수정할 스케줄 날짜
        new_memo: 새로운 메모 내용
        new_work_type: 새로운 작업 유형 (선택사항)
        
    Returns:
        dict: 수정 결과
    """
    try:
        # 입력 검증
        if not address or not date or not new_memo:
            return {"status": "error", "message": "❌ 주소, 날짜, 새 메모는 필수 입력사항입니다.", "error_type": "invalid_input"}
        
        # 날짜 파싱
        parsed_date = _parse_date_string(date)
        
        # 메모 검증
        if not validate_schedule_memo(new_memo):
            return {"status": "error", "message": "❌ 유효하지 않은 메모 내용입니다.", "error_type": "invalid_memo"}
        
        # 문서 검색
        found, doc_id, doc_data = _find_schedule_document(address)
        
        if not found:
            # 특수 카테고리인 경우 안내 메시지 변경
            if doc_data and doc_data.get("is_special_category"):
                return {
                    "status": "error",
                    "message": f"❌ '{address}' 카테고리의 스케줄 문서가 존재하지 않습니다.",
                    "error_type": "category_not_found",
                    "available_categories": list(SPECIAL_SCHEDULE_CATEGORIES)
                }
            else:
                return {
                    "status": "error",
                    "message": f"❌ '{address}' 주소를 찾을 수 없습니다.",
                    "error_type": "address_not_found",
                    "hint": f"특수 카테고리: {', '.join(SPECIAL_SCHEDULE_CATEGORIES)}"
                }
        
        # 기존 eventsJson 파싱
        events_json_str = doc_data.get("eventsJson", "{}")
        try:
            existing_events = json.loads(events_json_str)
        except json.JSONDecodeError:
            existing_events = {}
        
        # 해당 날짜의 이벤트 찾기
        matching_keys = [key for key in existing_events.keys() if key.startswith(f"{parsed_date}_")]
        
        if not matching_keys:
            return {
                "status": "error",
                "message": f"❌ {parsed_date}에 등록된 스케줄을 찾을 수 없습니다.",
                "error_type": "date_not_found"
            }
        
        # 첫 번째 매칭되는 이벤트 수정 (보통 하루에 하나의 주요 일정)
        event_key = matching_keys[0]
        existing_events[event_key]["memo"] = new_memo
        
        # 작업 유형이 제공된 경우 업데이트
        if new_work_type:
            # title 필드가 있다면 업데이트 (기존 구조 유지)
            if "title" in existing_events[event_key]:
                existing_events[event_key]["title"] = new_work_type
        
        # 문서 업데이트
        update_result = _update_events_json(doc_id, existing_events)
        
        if update_result.get("status") == "success":
            return {
                "status": "success",
                "message": f"✅ {address}의 {parsed_date} 스케줄이 수정되었습니다.",
                "data": {
                    "address": address,
                    "date": parsed_date,
                    "new_memo": new_memo,
                    "new_work_type": new_work_type,
                    "action": "updated"
                }
            }
        else:
            return {
                "status": "error",
                "message": f"❌ 스케줄 수정 중 오류가 발생했습니다: {update_result.get('message')}",
                "error_type": "update_failed"
            }
            
    except Exception as e:
        error_msg = handle_mcp_error(e, f"스케줄 수정 중 오류 (address: {address}, date: {date})")
        logger.error(error_msg)
        return {"status": "error", "message": f"❌ 스케줄 수정 실패: {error_msg}", "error_type": "system_error"}

def delete_schedule_record(address: str, date: str) -> dict:
    """특정 날짜의 스케줄을 삭제합니다.
    
    Args:
        address: 현장 주소 또는 특수 카테고리 ("개인 일정", "하자보수", "고객 상담")
        date: 삭제할 스케줄 날짜
        
    Returns:
        dict: 삭제 결과
    """
    try:
        # 입력 검증
        if not address or not date:
            return {"status": "error", "message": "❌ 주소와 날짜는 필수 입력사항입니다.", "error_type": "invalid_input"}
        
        # 날짜 파싱
        parsed_date = _parse_date_string(date)
        
        # 문서 검색
        found, doc_id, doc_data = _find_schedule_document(address)
        
        if not found:
            # 특수 카테고리인 경우 안내 메시지 변경
            if doc_data and doc_data.get("is_special_category"):
                return {
                    "status": "error",
                    "message": f"❌ '{address}' 카테고리의 스케줄 문서가 존재하지 않습니다.",
                    "error_type": "category_not_found",
                    "available_categories": list(SPECIAL_SCHEDULE_CATEGORIES)
                }
            else:
                return {
                    "status": "error",
                    "message": f"❌ '{address}' 주소를 찾을 수 없습니다.",
                    "error_type": "address_not_found",
                    "hint": f"특수 카테고리: {', '.join(SPECIAL_SCHEDULE_CATEGORIES)}"
                }
        
        # 기존 eventsJson 파싱
        events_json_str = doc_data.get("eventsJson", "{}")
        try:
            existing_events = json.loads(events_json_str)
        except json.JSONDecodeError:
            existing_events = {}
        
        # 해당 날짜의 이벤트 찾기 및 삭제
        keys_to_delete = [key for key in existing_events.keys() if key.startswith(f"{parsed_date}_")]
        
        if not keys_to_delete:
            return {
                "status": "error",
                "message": f"❌ {parsed_date}에 삭제할 스케줄을 찾을 수 없습니다.",
                "error_type": "date_not_found"
            }
        
        # 이벤트 삭제
        deleted_count = 0
        for key in keys_to_delete:
            del existing_events[key]
            deleted_count += 1
        
        # 문서 업데이트
        update_result = _update_events_json(doc_id, existing_events)
        
        if update_result.get("status") == "success":
            return {
                "status": "success",
                "message": f"✅ {address}의 {parsed_date} 스케줄 {deleted_count}개가 삭제되었습니다.",
                "data": {
                    "address": address,
                    "date": parsed_date,
                    "deleted_count": deleted_count,
                    "action": "deleted"
                }
            }
        else:
            return {
                "status": "error",
                "message": f"❌ 스케줄 삭제 중 오류가 발생했습니다: {update_result.get('message')}",
                "error_type": "update_failed"
            }
            
    except Exception as e:
        error_msg = handle_mcp_error(e, f"스케줄 삭제 중 오류 (address: {address}, date: {date})")
        logger.error(error_msg)
        return {"status": "error", "message": f"❌ 스케줄 삭제 실패: {error_msg}", "error_type": "system_error"}

def list_schedules_by_date(date: str) -> dict:
    """특정 날짜의 모든 스케줄을 조회합니다.
    
    Args:
        date: 조회할 날짜
        
    Returns:
        dict: 조회 결과
    """
    try:
        # 입력 검증
        if not date:
            return {"status": "error", "message": "❌ 날짜는 필수 입력사항입니다.", "error_type": "invalid_input"}
        
        # 날짜 파싱
        parsed_date = _parse_date_string(date)
        
        # MCP 규칙 검증
        if not validate_mcp_call("query_any_collection", collection="schedules", date=parsed_date):
            return {"status": "error", "message": "❌ MCP 규칙 검증 실패", "error_type": "mcp_validation_failed"}
        
        # 모든 schedules 문서 조회
        result = query_any_collection("schedules")
        
        if not validate_response(result) or result.get("status") != "success":
            return {"status": "error", "message": "❌ 스케줄 컬렉션 조회 실패", "error_type": "query_failed"}
        
        documents = result.get("data", {}).get("documents", [])
        schedules = []
        
        # 각 문서에서 해당 날짜의 이벤트 검색
        for doc in documents:
            doc_data = doc.get("data", {})
            address = doc_data.get("address", "알 수 없는 주소")
            events_json_str = doc_data.get("eventsJson", "{}")
            
            try:
                events = json.loads(events_json_str)
                
                # 해당 날짜의 이벤트 찾기
                for event_key, event_data in events.items():
                    if event_key.startswith(f"{parsed_date}_"):
                        schedule_info = {
                            "address": address,
                            "date": parsed_date,
                            "memo": event_data.get("memo", ""),
                            "status": event_data.get("status", "unknown"),
                            "title": event_data.get("title", ""),
                            "event_key": event_key
                        }
                        schedules.append(schedule_info)
                        
            except json.JSONDecodeError:
                logger.warning(f"eventsJson 파싱 실패 (address: {address})")
                continue
        
        # 결과 정렬 (주소별)
        schedules.sort(key=lambda x: x["address"])
        
        log_operation("list_schedules_by_date", "success", {"date": parsed_date, "count": len(schedules)})
        
        return {
            "status": "success",
            "message": f"✅ {parsed_date}의 스케줄 {len(schedules)}개를 조회했습니다.",
            "data": {
                "date": parsed_date,
                "schedules": schedules,
                "count": len(schedules),
                "action": "listed"
            }
        }
        
    except Exception as e:
        error_msg = handle_mcp_error(e, f"스케줄 조회 중 오류 (date: {date})")
        logger.error(error_msg)
        return {"status": "error", "message": f"❌ 스케줄 조회 실패: {error_msg}", "error_type": "system_error"}

def list_schedules_by_address(address: str) -> dict:
    """특정 주소/카테고리의 모든 스케줄을 조회합니다.
    
    Args:
        address: 조회할 주소 또는 특수 카테고리 ("개인 일정", "하자보수", "고객 상담")
        
    Returns:
        dict: 조회 결과
    """
    try:
        # 입력 검증
        if not address:
            return {"status": "error", "message": "❌ 주소 또는 카테고리는 필수 입력사항입니다.", "error_type": "invalid_input"}
        
        # MCP 규칙 검증
        if not validate_mcp_call("query_any_collection", collection="schedules", address=address):
            return {"status": "error", "message": "❌ MCP 규칙 검증 실패", "error_type": "mcp_validation_failed"}
        
        # 문서 검색
        found, doc_id, doc_data = _find_schedule_document(address)
        
        if not found:
            # 특수 카테고리인 경우 안내 메시지 변경
            if doc_data and doc_data.get("is_special_category"):
                return {
                    "status": "error",
                    "message": f"❌ '{address}' 카테고리의 스케줄 문서가 존재하지 않습니다.",
                    "error_type": "category_not_found",
                    "available_categories": list(SPECIAL_SCHEDULE_CATEGORIES)
                }
            else:
                return {
                    "status": "error",
                    "message": f"❌ '{address}' 주소를 찾을 수 없습니다.",
                    "error_type": "address_not_found",
                    "hint": f"특수 카테고리: {', '.join(SPECIAL_SCHEDULE_CATEGORIES)}"
                }
        
        # eventsJson 파싱
        events_json_str = doc_data.get("eventsJson", "{}")
        try:
            events = json.loads(events_json_str)
        except json.JSONDecodeError:
            events = {}
        
        # 모든 이벤트를 날짜별로 정리
        schedules = []
        for event_key, event_data in events.items():
            # 이벤트 키에서 날짜 추출 (YYYY-MM-DD_timestamp 형식)
            date_part = event_key.split('_')[0] if '_' in event_key else "알 수 없는 날짜"
            
            schedule_info = {
                "address": address,
                "date": date_part,
                "memo": event_data.get("memo", ""),
                "status": event_data.get("status", "unknown"),
                "title": event_data.get("title", ""),
                "event_key": event_key
            }
            schedules.append(schedule_info)
        
        # 날짜순 정렬
        schedules.sort(key=lambda x: x["date"])
        
        log_operation("list_schedules_by_address", "success", {"address": address, "count": len(schedules)})
        
        return {
            "status": "success",
            "message": f"✅ '{address}'의 스케줄 {len(schedules)}개를 조회했습니다.",
            "data": {
                "address": address,
                "schedules": schedules,
                "count": len(schedules),
                "action": "listed_by_address"
            }
        }
        
    except Exception as e:
        error_msg = handle_mcp_error(e, f"주소별 스케줄 조회 중 오류 (address: {address})")
        logger.error(error_msg)
        return {"status": "error", "message": f"❌ 스케줄 조회 실패: {error_msg}", "error_type": "system_error"}

# ==============================================================================
# 🔧 모듈 초기화 로깅
# ==============================================================================

logger.info("📅 스케줄 관리 에이전트가 초기화되었습니다.")
logger.info(f"   - MCP 규칙: {'✅ 사용 가능' if MCP_RULES_AVAILABLE else '⚠️ 폴백 모드'}")
logger.info(f"   - Firebase 도구: {'✅ 사용 가능' if FIREBASE_TOOLS_AVAILABLE else '⚠️ 폴백 모드'}")
logger.info(f"   - Firebase 클라이언트: {'✅ 사용 가능' if FIREBASE_CLIENT_AVAILABLE else '⚠️ 폴백 모드'}")
logger.info("   - 제공 기능: 스케줄 등록/수정/삭제/날짜별조회/주소별조회 (5개 도구)")
logger.info(f"   - 특수 카테고리: {', '.join(SPECIAL_SCHEDULE_CATEGORIES)}") 