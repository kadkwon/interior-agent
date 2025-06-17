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

# ==============================================================================
# 🎯 핵심 기능 5가지
# ==============================================================================

client = FirebaseMCPClient()

def register_new_schedule(address_id: str, date: str, description: str, category: str = "일반") -> Dict[str, Any]:
    """
    새로운 일정을 등록합니다.
    
    Args:
        address_id: 주소 ID
        date: 날짜 (YYYY-MM-DD)
        description: 일정 설명
        category: 일정 카테고리 (기본값: "일반")
        
    Returns:
        Dict: 등록 결과
    """
    try:
        # MCP 규칙 검증
        if not validate_mcp_call("add", "schedules", {
            "address": address_id,
            "date": date,
            "description": description,
            "category": category
        }):
            return {"status": "error", "message": "MCP 규칙 검증 실패"}
            
        # 날짜 형식 변환
        formatted_date = _parse_date_string(date)
        
        # 일정 등록
        result = client.add_schedule(
            address_id=address_id,
            date=formatted_date,
            description=description,
            category=category
        )
        
        if validate_response(result):
            log_operation("register_schedule", "success", {
                "address": address_id,
                "date": formatted_date
            })
            return {"status": "success", "data": result}
        else:
            return {"status": "error", "message": "일정 등록 실패"}
            
    except Exception as e:
        error_msg = handle_mcp_error(e, "일정 등록 중 오류")
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

def update_existing_schedule(schedule_id: str, date: str = None, description: str = None, category: str = None) -> Dict[str, Any]:
    """
    기존 일정을 수정합니다.
    
    Args:
        schedule_id: 일정 ID
        date: 수정할 날짜 (선택)
        description: 수정할 설명 (선택)
        category: 수정할 카테고리 (선택)
        
    Returns:
        Dict: 수정 결과
    """
    try:
        # 수정할 데이터 준비
        update_data = {}
        if date:
            update_data["date"] = _parse_date_string(date)
        if description:
            update_data["description"] = description
        if category:
            update_data["category"] = category
            
        # MCP 규칙 검증
        if not validate_mcp_call("update", "schedules", {
            "schedule_id": schedule_id,
            **update_data
        }):
            return {"status": "error", "message": "MCP 규칙 검증 실패"}
            
        # 일정 수정
        result = client.update_schedule(schedule_id, update_data)
        
        if validate_response(result):
            log_operation("update_schedule", "success", {
                "schedule_id": schedule_id,
                "fields": list(update_data.keys())
            })
            return {"status": "success", "data": result}
        else:
            return {"status": "error", "message": "일정 수정 실패"}
            
    except Exception as e:
        error_msg = handle_mcp_error(e, f"일정 수정 중 오류 (ID: {schedule_id})")
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

def delete_schedule_record(schedule_id: str) -> Dict[str, Any]:
    """
    일정을 삭제합니다.
    
    Args:
        schedule_id: 삭제할 일정 ID
        
    Returns:
        Dict: 삭제 결과
    """
    try:
        # MCP 규칙 검증
        if not validate_mcp_call("delete", "schedules", {"schedule_id": schedule_id}):
            return {"status": "error", "message": "MCP 규칙 검증 실패"}
            
        # 일정 삭제
        result = client.delete_schedule(schedule_id)
        
        if validate_response(result):
            log_operation("delete_schedule", "success", {"schedule_id": schedule_id})
            return {"status": "success", "data": result}
        else:
            return {"status": "error", "message": "일정 삭제 실패"}
            
    except Exception as e:
        error_msg = handle_mcp_error(e, f"일정 삭제 중 오류 (ID: {schedule_id})")
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

def list_schedules_by_date(date: str) -> List[Dict[str, Any]]:
    """
    특정 날짜의 일정을 조회합니다.
    
    Args:
        date: 조회할 날짜
        
    Returns:
        List: 일정 목록
    """
    try:
        # 날짜 형식 변환
        formatted_date = _parse_date_string(date)
        
        # MCP 규칙 검증
        if not validate_mcp_call("query", "schedules", {"date": formatted_date}):
            return []
            
        # 일정 조회
        result = client.list_schedules_by_date(formatted_date)
        
        if validate_response(result):
            log_operation("list_schedules", "success", {"date": formatted_date})
            return result.get("data", [])
        else:
            return []
            
    except Exception as e:
        error_msg = handle_mcp_error(e, f"일정 조회 중 오류 (날짜: {date})")
        logger.error(error_msg)
        return []

def list_schedules_by_address(address_id: str) -> List[Dict[str, Any]]:
    """
    특정 주소의 일정을 조회합니다.
    
    Args:
        address_id: 조회할 주소 ID
        
    Returns:
        List: 일정 목록
    """
    try:
        # MCP 규칙 검증
        if not validate_mcp_call("query", "schedules", {"address": address_id}):
            return []
            
        # 일정 조회
        result = client.list_schedules_by_address(address_id)
        
        if validate_response(result):
            log_operation("list_schedules", "success", {"address": address_id})
            return result.get("data", [])
        else:
            return []
            
    except Exception as e:
        error_msg = handle_mcp_error(e, f"일정 조회 중 오류 (주소: {address_id})")
        logger.error(error_msg)
        return []

# 초기화 로그
logger.info("📅 스케줄 관리 에이전트가 초기화되었습니다.")
logger.info(f"   - MCP 규칙: {'✅ 사용 가능' if MCP_RULES_AVAILABLE else '⚠️ 폴백 모드'}")
logger.info(f"   - 제공 기능: 스케줄 등록/수정/삭제/날짜별조회/주소별조회 (5개 도구)")
logger.info(f"   - 특수 카테고리: {', '.join(SPECIAL_SCHEDULE_CATEGORIES)}") 