"""
스케줄 관리 에이전트

schedules 컬렉션의 CRUD 작업을 담당하는 전용 에이전트입니다.
개별 공정 등록 및 스케줄 관리 기능을 제공합니다.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import json
import re


# Firebase MCP 호출 규칙 import 추가
try:
    from ..firebase_mcp_rules import (
        validate_mcp_call,
        execute_mcp_sequence,
        handle_mcp_error,
        safe_remove_data,
        validate_response,
        log_operation
    )
except ImportError:
    # ADK Web 환경에서는 절대 import
    from interior_agents.firebase_mcp_rules import (
        validate_mcp_call,
        execute_mcp_sequence,
        handle_mcp_error,
        safe_remove_data,
        validate_response,
        log_operation
    )

# Firebase 클라이언트 및 도구들
try:
    from ..client.firebase_client import firebase_client
    from ..tools.firebase_tools import query_any_collection
except ImportError:
    # ADK Web 환경에서는 절대 import
    from interior_agents.client.firebase_client import firebase_client
    from interior_agents.tools.firebase_tools import query_any_collection


def register_schedule_event(address: str, date: str, work_type: str, **kwargs) -> dict:
    """
    개별 공정 스케줄을 등록합니다.
    
    Args:
        address: 주소명 (schedules 컬렉션의 address 필드와 매칭)
        date: 날짜 (다양한 형식 지원)
        work_type: 작업 유형 (memo 필드에 저장)
        **kwargs: 추가 옵션들 (title, status 등)
        
    Returns:
        dict: 등록 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("schedule_register", "schedules", {"address": address, "date": date, "work_type": work_type}):
            log_operation("schedule_register", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 1. 필수 필드 검증
        if not address or not date or not work_type:
            log_operation("schedule_register", "schedules", {"error": "필수 필드 누락"}, False)
            return {
                "status": "error",
                "message": "주소, 날짜, 작업 유형은 필수입니다."
            }

        # 2. 날짜 파싱
        parsed_date = _parse_date_string(date)
        if not parsed_date:
            return {
                "status": "error",
                "message": "날짜 형식이 올바르지 않습니다. (예: 4월 7일, 2024-04-07)"
            }

        # 3. schedules 컬렉션에서 해당 주소 문서 검색
        schedule_doc = _find_schedule_document_by_address(address)
        
        if not schedule_doc["exists"]:
            log_operation("schedule_register", "schedules", {"error": "주소 문서 없음", "address": address}, False)
            return {
                "status": "error",
                "message": f"'{address}' 주소가 schedules에 등록되어 있지 않습니다. 주소를 먼저 등록해주세요."
            }

        # 4. 기존 eventsJson 파싱
        doc_id = schedule_doc["doc_id"]
        existing_doc_data = schedule_doc["data"]
        events_json_str = existing_doc_data.get("eventsJson", "{}")
        
        try:
            events_data = json.loads(events_json_str) if events_json_str else {}
        except json.JSONDecodeError:
            events_data = {}

        # 5. 새 이벤트 키 생성 (날짜_타임스탬프)
        timestamp_id = str(int(time.time() * 1000))
        event_key = f"{parsed_date}_{timestamp_id}"

        # 6. 새 이벤트 데이터 준비
        new_event = {
            "title": kwargs.get("title", ""),
            "status": kwargs.get("status", "scheduled"),
            "memo": work_type
        }

        # 7. 이벤트 추가
        events_data[event_key] = new_event

        # 8. Firebase 문서 업데이트
        update_data = {
            "eventsJson": json.dumps(events_data, ensure_ascii=False)
        }

        result = firebase_client.update_document(f"schedules/{doc_id}", update_data)

        # 호출 결과 확인 및 검증
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("Firebase 업데이트 실패"), "schedule_register")
            return {
                "status": "error",
                "message": error_msg
            }

        # 성공 처리
        if result and result.get("success"):
            log_operation("schedule_register", "schedules", {
                "doc_id": doc_id,
                "address": address,
                "date": parsed_date,
                "work_type": work_type
            }, True)
            
            return {
                "status": "success",
                "message": f"'{address}'에 {parsed_date} {work_type} 스케줄이 성공적으로 등록되었습니다.",
                "doc_id": doc_id,
                "event_key": event_key,
                "address": address,
                "date": parsed_date,
                "work_type": work_type
            }
        else:
            error_msg = handle_mcp_error(Exception("스케줄 저장 실패"), "schedule_register")
            return {
                "status": "error",
                "message": error_msg
            }

    except Exception as e:
        error_msg = handle_mcp_error(e, "schedule_register")
        log_operation("schedule_register", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": error_msg
        }


def register_multiple_schedule_events(schedule_list: List[dict]) -> dict:
    """
    여러 스케줄을 한 번에 등록합니다.
    
    Args:
        schedule_list: 스케줄 데이터 리스트
                      각 항목은 {"address": "주소", "date": "날짜", "work_type": "작업유형"} 형태
        
    Returns:
        dict: 일괄 등록 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("batch_schedule_register", "schedules", {"count": len(schedule_list)}):
            log_operation("batch_schedule_register", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        if not schedule_list or len(schedule_list) == 0:
            return {
                "status": "error",
                "message": "등록할 스케줄이 없습니다."
            }

        success_results = []
        error_results = []

        for i, schedule_data in enumerate(schedule_list):
            try:
                # 필수 필드 확인
                address = schedule_data.get("address", "")
                date = schedule_data.get("date", "")
                work_type = schedule_data.get("work_type", "")
                
                if not all([address, date, work_type]):
                    error_results.append({
                        "index": i,
                        "data": schedule_data,
                        "error": "필수 필드 누락 (address, date, work_type)"
                    })
                    continue

                # 개별 스케줄 등록
                result = register_schedule_event(
                    address=address,
                    date=date,
                    work_type=work_type,
                    **{k: v for k, v in schedule_data.items() if k not in ["address", "date", "work_type"]}
                )

                if result.get("status") == "success":
                    success_results.append({
                        "index": i,
                        "data": schedule_data,
                        "result": result
                    })
                else:
                    error_results.append({
                        "index": i,
                        "data": schedule_data,
                        "error": result.get("message", "알 수 없는 오류")
                    })

            except Exception as e:
                error_results.append({
                    "index": i,
                    "data": schedule_data,
                    "error": str(e)
                })

        # 결과 정리
        total_count = len(schedule_list)
        success_count = len(success_results)
        error_count = len(error_results)

        log_operation("batch_schedule_register", "schedules", {
            "total": total_count,
            "success": success_count,
            "errors": error_count
        }, error_count == 0)

        return {
            "status": "success" if error_count == 0 else "partial_success",
            "message": f"전체 {total_count}개 중 {success_count}개 성공, {error_count}개 실패",
            "total_count": total_count,
            "success_count": success_count,
            "error_count": error_count,
            "success_results": success_results,
            "error_results": error_results
        }

    except Exception as e:
        error_msg = handle_mcp_error(e, "batch_schedule_register")
        log_operation("batch_schedule_register", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": error_msg
        }


def get_schedule_by_date_range(start_date: str, end_date: str, address: str = None) -> dict:
    """
    날짜 범위로 스케줄을 조회합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD 또는 한국어 형식)
        end_date: 종료 날짜 (YYYY-MM-DD 또는 한국어 형식)
        address: 특정 주소로 필터링 (선택사항)
        
    Returns:
        dict: 날짜 범위 스케줄 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "schedules", {"date_range": f"{start_date} ~ {end_date}"}):
            log_operation("schedule_date_range", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 날짜 파싱
        parsed_start = _parse_date_string(start_date)
        parsed_end = _parse_date_string(end_date)
        
        if not parsed_start or not parsed_end:
            return {
                "status": "error",
                "message": "날짜 형식이 올바르지 않습니다. (예: 2024-04-07, 4월 7일)"
            }

        # 날짜 범위 검증
        if parsed_start > parsed_end:
            return {
                "status": "error",
                "message": "시작 날짜가 종료 날짜보다 늦습니다."
            }

        # 스케줄 조회
        result = list_schedules(address=address, date_range=(parsed_start, parsed_end), limit=500)
        
        if result.get("status") == "success":
            schedules = result.get("schedules", [])
            
            # 날짜별로 그룹핑
            date_groups = {}
            for schedule in schedules:
                date = schedule.get("date", "")
                if date not in date_groups:
                    date_groups[date] = []
                date_groups[date].append(schedule)
            
            log_operation("schedule_date_range", "schedules", {
                "start_date": parsed_start,
                "end_date": parsed_end,
                "address_filter": address,
                "total_events": len(schedules),
                "date_count": len(date_groups)
            }, True)
            
            return {
                "status": "success",
                "message": f"{parsed_start} ~ {parsed_end} 기간의 스케줄을 조회했습니다.",
                "start_date": parsed_start,
                "end_date": parsed_end,
                "address_filter": address,
                "schedules": schedules,
                "date_groups": date_groups,
                "total_count": len(schedules),
                "formatted_list": result.get("formatted_list", "")
            }
        else:
            return result

    except Exception as e:
        error_msg = handle_mcp_error(e, "schedule_date_range")
        log_operation("schedule_date_range", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": error_msg
        }


def mark_schedule_as_completed(identifier: str) -> dict:
    """
    스케줄을 완료 상태로 표시합니다.
    
    Args:
        identifier: 스케줄 식별자 (event_key 또는 주소)
        
    Returns:
        dict: 완료 처리 결과
    """
    try:
        return update_schedule_event(identifier, {"status": "completed"})
    except Exception as e:
        error_msg = handle_mcp_error(e, "schedule_complete")
        return {
            "status": "error",
            "message": error_msg
        }


def validate_schedule_data(schedule_data: dict) -> dict:
    """
    스케줄 데이터의 유효성을 검증합니다.
    
    Args:
        schedule_data: 검증할 스케줄 데이터
        
    Returns:
        dict: 검증 결과
    """
    try:
        errors = []
        warnings = []
        
        # 필수 필드 검증
        required_fields = ["address", "date", "work_type"]
        for field in required_fields:
            if not schedule_data.get(field):
                errors.append(f"필수 필드 '{field}'가 누락되었습니다.")
        
        # 날짜 형식 검증
        if schedule_data.get("date"):
            parsed_date = _parse_date_string(schedule_data["date"])
            if not parsed_date:
                errors.append("날짜 형식이 올바르지 않습니다.")
            else:
                # 과거 날짜 경고
                today = datetime.now().strftime("%Y-%m-%d")
                if parsed_date < today:
                    warnings.append("과거 날짜입니다.")
        
        # 주소 존재 여부 검증
        if schedule_data.get("address"):
            address_doc = _find_schedule_document_by_address(schedule_data["address"])
            if not address_doc["exists"]:
                errors.append(f"'{schedule_data['address']}' 주소가 schedules에 등록되어 있지 않습니다.")
        
        # 작업 유형 길이 검증
        if schedule_data.get("work_type") and len(schedule_data["work_type"]) > 100:
            warnings.append("작업 유형이 100자를 초과합니다.")
        
        validation_result = {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validated_data": schedule_data
        }
        
        # 날짜 정규화
        if schedule_data.get("date") and len(errors) == 0:
            validation_result["validated_data"]["date"] = _parse_date_string(schedule_data["date"])
        
        return {
            "status": "success",
            "validation": validation_result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"데이터 검증 중 오류가 발생했습니다: {str(e)}"
        }


def get_schedule_statistics(address: str = None) -> dict:
    """
    스케줄 통계 정보를 조회합니다.
    
    Args:
        address: 특정 주소로 필터링 (선택사항)
        
    Returns:
        dict: 통계 정보
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "schedules", {"stats": True}):
            log_operation("schedule_stats", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 전체 스케줄 조회
        result = list_schedules(address=address, limit=1000)
        
        if result.get("status") != "success":
            return result
        
        schedules = result.get("schedules", [])
        
        if not schedules:
            return {
                "status": "success",
                "message": "등록된 스케줄이 없습니다.",
                "statistics": {
                    "total_count": 0,
                    "completed_count": 0,
                    "scheduled_count": 0,
                    "address_count": 0,
                    "date_range": None
                }
            }
        
        # 통계 계산
        total_count = len(schedules)
        completed_count = len([s for s in schedules if s.get("status") == "completed"])
        scheduled_count = len([s for s in schedules if s.get("status") == "scheduled"])
        
        # 주소별 카운트
        address_counts = {}
        for schedule in schedules:
            addr = schedule.get("address", "Unknown")
            address_counts[addr] = address_counts.get(addr, 0) + 1
        
        # 날짜 범위
        dates = [s.get("date") for s in schedules if s.get("date")]
        date_range = {
            "earliest": min(dates) if dates else None,
            "latest": max(dates) if dates else None
        }
        
        # 월별 통계
        monthly_stats = {}
        for schedule in schedules:
            date = schedule.get("date", "")
            if date and len(date) >= 7:  # YYYY-MM-DD 형식
                month_key = date[:7]  # YYYY-MM
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {"total": 0, "completed": 0, "scheduled": 0}
                monthly_stats[month_key]["total"] += 1
                if schedule.get("status") == "completed":
                    monthly_stats[month_key]["completed"] += 1
                elif schedule.get("status") == "scheduled":
                    monthly_stats[month_key]["scheduled"] += 1
        
        statistics = {
            "total_count": total_count,
            "completed_count": completed_count,
            "scheduled_count": scheduled_count,
            "completion_rate": round((completed_count / total_count * 100), 2) if total_count > 0 else 0,
            "address_count": len(address_counts),
            "address_breakdown": address_counts,
            "date_range": date_range,
            "monthly_stats": monthly_stats
        }
        
        log_operation("schedule_stats", "schedules", {
            "address_filter": address,
            "total_count": total_count
        }, True)
        
        return {
            "status": "success",
            "message": f"스케줄 통계를 조회했습니다. (총 {total_count}개)",
            "statistics": statistics
        }
        
    except Exception as e:
        error_msg = handle_mcp_error(e, "schedule_stats")
        log_operation("schedule_stats", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": error_msg
        }


def list_schedules(address: str = None, date_range: tuple = None, limit: int = 100) -> dict:
    """
    스케줄 목록을 조회합니다.
    
    Args:
        address: 특정 주소로 필터링 (선택사항)
        date_range: 날짜 범위 튜플 (start_date, end_date) (선택사항)
        limit: 조회할 문서 개수 제한
        
    Returns:
        dict: 스케줄 목록과 조회 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "schedules"):
            log_operation("list_schedules", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # Firebase 데이터 조회
        result = query_any_collection("schedules", limit)
        
        # 호출 결과 확인 및 검증
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("스케줄 목록 조회 실패"), "list_schedules")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 성공적인 응답 처리
        if result and result.get("status") == "success":
            documents = result.get("data", {}).get("documents", [])
        else:
            error_msg = handle_mcp_error(Exception("응답 데이터 오류"), "list_schedules")
            return {
                "status": "error",
                "message": error_msg
            }

        schedules = []
        for doc in documents:
            # 문서 ID 추출
            doc_id = doc.get("id", "")
            doc_data = doc.get("data", {})
            
            # 주소 필터링
            doc_address = doc_data.get("address", "")
            if address and address not in doc_address:
                continue
            
            # eventsJson 파싱
            events_json_str = doc_data.get("eventsJson", "{}")
            try:
                events_data = json.loads(events_json_str) if events_json_str else {}
            except json.JSONDecodeError:
                events_data = {}
            
            # 이벤트들을 개별 스케줄로 변환
            for event_key, event_data in events_data.items():
                # 날짜 추출 (event_key에서 날짜 부분만)
                event_date = event_key.split("_")[0] if "_" in event_key else event_key
                
                # 날짜 범위 필터링
                if date_range:
                    start_date, end_date = date_range
                    if not (start_date <= event_date <= end_date):
                        continue
                
                schedules.append({
                    "doc_id": doc_id,
                    "address": doc_address,
                    "color": doc_data.get("color", "#4A90E2"),
                    "date": event_date,
                    "event_key": event_key,
                    "title": event_data.get("title", ""),
                    "status": event_data.get("status", "scheduled"),
                    "memo": event_data.get("memo", "")
                })
        
        # 날짜순 정렬
        schedules.sort(key=lambda x: x.get("date", ""))
        
        log_operation("list_schedules", "schedules", {"count": len(schedules), "address_filter": address}, True)
        
        # 사용자가 읽기 쉬운 형태로 포맷팅
        formatted_list = _format_schedule_display(schedules, address)
        
        return {
            "status": "success",
            "schedules": schedules,
            "total_count": len(schedules),
            "formatted_list": formatted_list,
            "message": formatted_list
        }
        
    except Exception as e:
        log_operation("list_schedules", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": handle_mcp_error(e, "list_schedules")
        }


def update_schedule_event(identifier: str, update_data: dict) -> dict:
    """
    기존 스케줄 이벤트를 수정합니다.
    
    Args:
        identifier: 수정할 이벤트 식별자 (주소 또는 event_key)
        update_data: 수정할 데이터 (title, status, memo 등)
        
    Returns:
        dict: 수정 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("schedule_update", "schedules", update_data):
            log_operation("schedule_update", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 1. 식별자로 스케줄 문서 및 이벤트 찾기
        schedule_info = _find_schedule_event_by_identifier(identifier)
        
        if not schedule_info["exists"]:
            return {
                "status": "error",
                "message": f"스케줄 '{identifier}'를 찾을 수 없습니다."
            }

        doc_id = schedule_info["doc_id"]
        event_key = schedule_info["event_key"]
        events_data = schedule_info["events_data"]

        # 2. 이벤트 데이터 업데이트
        current_event = events_data[event_key]
        
        for key, value in update_data.items():
            if key in ["title", "status", "memo"]:
                current_event[key] = value

        # 3. Firebase 문서 업데이트
        update_doc_data = {
            "eventsJson": json.dumps(events_data, ensure_ascii=False)
        }

        result = firebase_client.update_document(f"schedules/{doc_id}", update_doc_data)

        # 호출 결과 확인 및 검증
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("Firebase 업데이트 실패"), "schedule_update")
            return {
                "status": "error",
                "message": error_msg
            }

        # 성공 처리
        if result and result.get("success"):
            log_operation("schedule_update", "schedules", {
                "doc_id": doc_id,
                "event_key": event_key,
                "updated_fields": list(update_data.keys())
            }, True)
            
            return {
                "status": "success",
                "message": f"스케줄이 성공적으로 업데이트되었습니다.",
                "doc_id": doc_id,
                "event_key": event_key,
                "updated_fields": list(update_data.keys())
            }
        else:
            error_msg = handle_mcp_error(Exception("스케줄 업데이트 실패"), "schedule_update")
            return {
                "status": "error",
                "message": error_msg
            }

    except Exception as e:
        log_operation("schedule_update", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": handle_mcp_error(e, "schedule_update")
        }


def delete_schedule_event(identifier: str) -> dict:
    """
    스케줄 이벤트를 삭제합니다.
    
    Args:
        identifier: 삭제할 이벤트 식별자 (주소 또는 event_key)
        
    Returns:
        dict: 삭제 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("schedule_delete", "schedules"):
            log_operation("schedule_delete", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 1. 식별자로 스케줄 문서 및 이벤트 찾기
        schedule_info = _find_schedule_event_by_identifier(identifier)
        
        if not schedule_info["exists"]:
            return {
                "status": "error",
                "message": f"스케줄 '{identifier}'를 찾을 수 없습니다."
            }

        doc_id = schedule_info["doc_id"]
        event_key = schedule_info["event_key"]
        events_data = schedule_info["events_data"]
        
        # 삭제할 이벤트 정보 백업
        deleted_event = events_data[event_key].copy()

        # 2. 이벤트 삭제
        del events_data[event_key]

        # 3. Firebase 문서 업데이트
        update_data = {
            "eventsJson": json.dumps(events_data, ensure_ascii=False)
        }

        result = firebase_client.update_document(f"schedules/{doc_id}", update_data)

        # 호출 결과 확인 및 검증
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("Firebase 업데이트 실패"), "schedule_delete")
            return {
                "status": "error",
                "message": error_msg
            }

        # 성공 처리
        if result and result.get("success"):
            log_operation("schedule_delete", "schedules", {
                "doc_id": doc_id,
                "event_key": event_key
            }, True)
            
            return {
                "status": "success",
                "message": f"스케줄이 성공적으로 삭제되었습니다.",
                "doc_id": doc_id,
                "deleted_event_key": event_key,
                "deleted_event": deleted_event
            }
        else:
            error_msg = handle_mcp_error(Exception("스케줄 삭제 실패"), "schedule_delete")
            return {
                "status": "error",
                "message": error_msg
            }

    except Exception as e:
        log_operation("schedule_delete", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": handle_mcp_error(e, "schedule_delete")
        }


def search_schedules_by_keyword(keyword: str, date_filter: str = None) -> dict:
    """
    키워드로 스케줄을 검색합니다.
    
    Args:
        keyword: 검색할 키워드 (주소, 작업 유형, 메모에서 검색)
        date_filter: 날짜 필터 (선택사항)
        
    Returns:
        dict: 검색 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "schedules", {"keyword": keyword}):
            log_operation("search_schedules", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 유효성 검증
        if not keyword or keyword.strip() == "":
            return {
                "status": "error",
                "message": "검색 키워드를 입력해주세요."
            }

        # 전체 스케줄 목록 조회
        all_schedules_result = list_schedules(limit=500)
        
        if not validate_response(all_schedules_result):
            error_msg = handle_mcp_error(Exception("스케줄 목록 조회 실패"), "search_schedules")
            return {
                "status": "error",
                "message": error_msg
            }

        if all_schedules_result.get("status") == "success":
            schedules = all_schedules_result.get("schedules", [])
        else:
            error_msg = handle_mcp_error(Exception("스케줄 검색용 데이터 오류"), "search_schedules")
            return {
                "status": "error",
                "message": error_msg
            }

        # 키워드 매칭 검색
        matched_schedules = []
        keyword_lower = keyword.lower().strip()
        
        for schedule in schedules:
            address_text = schedule.get("address", "").lower()
            memo_text = schedule.get("memo", "").lower()
            title_text = schedule.get("title", "").lower()
            
            # 키워드 포함 검색
            if (keyword_lower in address_text or 
                keyword_lower in memo_text or
                keyword_lower in title_text):
                
                # 날짜 필터 적용
                if date_filter:
                    schedule_date = schedule.get("date", "")
                    if date_filter not in schedule_date:
                        continue
                
                matched_schedules.append(schedule)

        log_operation("search_schedules", "schedules", {
            "keyword": keyword, 
            "matches": len(matched_schedules)
        }, True)
        
        # 검색 결과 포맷팅
        formatted_results = _format_schedule_display(matched_schedules, None, f"'{keyword}' 검색 결과")
        
        return {
            "status": "success",
            "schedules": matched_schedules,
            "total_matches": len(matched_schedules),
            "search_keyword": keyword,
            "formatted_results": formatted_results,
            "message": formatted_results
        }

    except Exception as e:
        log_operation("search_schedules", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": handle_mcp_error(e, "search_schedules")
        }


def register_new_schedule_category(address: str, color: str = "#4A90E2", events_data: dict = None) -> dict:
    """
    새로운 스케줄 카테고리를 schedules 컬렉션에 등록합니다.
    
    Args:
        address: 주소명 또는 카테고리명 (예: "개인 일정")
        color: 색상 코드 (기본값: "#4A90E2")
        events_data: 초기 이벤트 데이터 (선택사항)
        
    Returns:
        dict: 등록 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("schedule_category_register", "schedules", {"address": address}):
            log_operation("schedule_category_register", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 1. 필수 필드 검증
        if not address:
            log_operation("schedule_category_register", "schedules", {"error": "필수 필드 누락"}, False)
            return {
                "status": "error",
                "message": "주소/카테고리명은 필수입니다."
            }

        # 2. 기존 스케줄 카테고리 중복 확인
        result = query_any_collection("schedules", limit=1000)
        
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("스케줄 목록 조회 실패"), "schedule_category_register")
            return {
                "status": "error", 
                "message": error_msg
            }
        
        documents = []
        try:
            if isinstance(result, dict):
                if result.get("status") == "success":
                    documents = result.get("data", {}).get("documents", [])
                elif result.get("success"):
                    documents = result.get("data", {}).get("documents", [])
        except Exception as e:
            log_operation("schedule_category_register", "schedules", {"error": f"문서 파싱 실패: {e}"}, False)

        # 3. 중복 주소 확인 (address 필드 기준, 완전일치)
        for doc in documents:
            doc_address = doc.get("data", {}).get("address", "").strip()
            if doc_address == address.strip():
                log_operation("schedule_category_register", "schedules", {"error": "중복 주소", "address": address}, False)
                return {
                    "status": "error",
                    "message": f"'{address}' 카테고리가 이미 존재합니다."
                }

        # 4. 초기 eventsJson 데이터 준비
        if events_data is None:
            events_json_str = "{}"
        else:
            events_json_str = json.dumps(events_data, ensure_ascii=False)

        # 5. Firebase 문서 구조 준비
        document_data = {
            "address": address,
            "color": color,
            "eventsJson": events_json_str
        }

        # 6. 타임스탬프 기반 문서 ID 생성
        timestamp_id = str(int(time.time() * 1000))

        # Firebase 문서 추가
        result = firebase_client.add_document("schedules", document_data, timestamp_id)

        # 호출 결과 확인 및 검증
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("문서 추가 실패"), "schedule_category_register")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 성공 처리
        if result and (result.get("success") or result.get("status") == "success"):
            log_operation("schedule_category_register", "schedules", {
                "doc_id": timestamp_id,
                "address": address,
                "color": color
            }, True)
            
            return {
                "status": "success",
                "message": f"스케줄 카테고리 '{address}'가 성공적으로 등록되었습니다.",
                "doc_id": timestamp_id,
                "address": address,
                "color": color
            }
        else:
            error_msg = handle_mcp_error(Exception("문서 저장 실패"), "schedule_category_register")
            return {
                "status": "error",
                "message": error_msg
            }

    except Exception as e:
        error_msg = handle_mcp_error(e, "schedule_category_register")
        log_operation("schedule_category_register", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": error_msg
        }


# =================
# 헬퍼 함수들
# =================

def _find_schedule_document_by_address(address: str) -> dict:
    """주소로 schedules 컬렉션의 문서를 찾습니다."""
    try:
        result = query_any_collection("schedules", limit=500)
        if result.get("status") == "success":
            documents = result.get("data", {}).get("documents", [])
            
            for doc in documents:
                doc_id = doc.get("id", "")
                doc_data = doc.get("data", {})
                doc_address = doc_data.get("address", "")
                
                # 주소 매칭 (정확한 일치 또는 포함)
                if doc_address == address or address in doc_address:
                    return {
                        "exists": True,
                        "doc_id": doc_id,
                        "data": doc_data
                    }
        
        return {"exists": False}
        
    except Exception:
        return {"exists": False}


def _find_schedule_event_by_identifier(identifier: str) -> dict:
    """식별자로 특정 스케줄 이벤트를 찾습니다."""
    try:
        result = query_any_collection("schedules", limit=500)
        if result.get("status") == "success":
            documents = result.get("data", {}).get("documents", [])
            
            for doc in documents:
                doc_id = doc.get("id", "")
                doc_data = doc.get("data", {})
                doc_address = doc_data.get("address", "")
                
                # eventsJson 파싱
                events_json_str = doc_data.get("eventsJson", "{}")
                try:
                    events_data = json.loads(events_json_str) if events_json_str else {}
                except json.JSONDecodeError:
                    events_data = {}
                
                # event_key로 직접 검색
                if identifier in events_data:
                    return {
                        "exists": True,
                        "doc_id": doc_id,
                        "event_key": identifier,
                        "events_data": events_data
                    }
                
                # 주소로 검색하여 최신 이벤트 반환
                if doc_address == identifier or identifier in doc_address:
                    if events_data:
                        # 최신 이벤트 키 찾기 (타임스탬프 기준)
                        latest_key = max(events_data.keys(), key=lambda k: k.split("_")[-1] if "_" in k else "0")
                        return {
                            "exists": True,
                            "doc_id": doc_id,
                            "event_key": latest_key,
                            "events_data": events_data
                        }
        
        return {"exists": False}
        
    except Exception:
        return {"exists": False}


def _parse_date_string(date_str: str) -> Optional[str]:
    """날짜 문자열을 YYYY-MM-DD 형식으로 파싱합니다."""
    try:
        date_str = date_str.strip()
        current_year = datetime.now().year
        
        # 이미 YYYY-MM-DD 형식인 경우
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # "4월 7일" 형식
        month_day_match = re.match(r'(\d{1,2})월\s*(\d{1,2})일', date_str)
        if month_day_match:
            month = int(month_day_match.group(1))
            day = int(month_day_match.group(2))
            return f"{current_year}-{month:02d}-{day:02d}"
        
        # "2024-4-7" 형식
        ymd_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if ymd_match:
            year = int(ymd_match.group(1))
            month = int(ymd_match.group(2))
            day = int(ymd_match.group(3))
            return f"{year}-{month:02d}-{day:02d}"
        
        return None
        
    except Exception:
        return None


def get_today_schedules() -> dict:
    """
    오늘 날짜의 스케줄을 조회합니다.
    
    Returns:
        dict: 오늘 스케줄 목록
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        return get_schedule_by_date_range(today, today)
    except Exception as e:
        error_msg = handle_mcp_error(e, "today_schedules")
        return {
            "status": "error",
            "message": error_msg
        }


def get_upcoming_schedules(days: int = 7) -> dict:
    """
    앞으로 지정된 일수 동안의 스케줄을 조회합니다.
    
    Args:
        days: 조회할 일수 (기본값: 7일)
        
    Returns:
        dict: 예정된 스케줄 목록
    """
    try:
        today = datetime.now()
        end_date = today + timedelta(days=days)
        
        start_str = today.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        return get_schedule_by_date_range(start_str, end_str)
    except Exception as e:
        error_msg = handle_mcp_error(e, "upcoming_schedules")
        return {
            "status": "error",
            "message": error_msg
        }


def copy_schedule_to_new_date(event_key: str, new_date: str) -> dict:
    """
    기존 스케줄을 새로운 날짜로 복사합니다.
    
    Args:
        event_key: 복사할 스케줄의 이벤트 키
        new_date: 새로운 날짜
        
    Returns:
        dict: 복사 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("schedule_copy", "schedules", {"event_key": event_key, "new_date": new_date}):
            log_operation("schedule_copy", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 기존 스케줄 찾기
        schedule_info = _find_schedule_event_by_identifier(event_key)
        
        if not schedule_info["exists"]:
            return {
                "status": "error",
                "message": f"스케줄 '{event_key}'를 찾을 수 없습니다."
            }

        # 기존 이벤트 데이터 가져오기
        events_data = schedule_info["events_data"]
        original_event = events_data[event_key]
        
        # 주소 정보 가져오기
        result = query_any_collection("schedules", limit=500)
        if not validate_response(result):
            return {
                "status": "error",
                "message": "스케줄 정보 조회에 실패했습니다."
            }
        
        documents = result.get("data", {}).get("documents", [])
        doc_id = schedule_info["doc_id"]
        
        address = None
        for doc in documents:
            if doc.get("id") == doc_id:
                address = doc.get("data", {}).get("address", "")
                break
        
        if not address:
            return {
                "status": "error",
                "message": "주소 정보를 찾을 수 없습니다."
            }

        # 새로운 날짜로 스케줄 등록
        result = register_schedule_event(
            address=address,
            date=new_date,
            work_type=original_event.get("memo", ""),
            title=original_event.get("title", ""),
            status=original_event.get("status", "scheduled")
        )
        
        if result.get("status") == "success":
            log_operation("schedule_copy", "schedules", {
                "original_event_key": event_key,
                "new_date": new_date,
                "address": address
            }, True)
            
            return {
                "status": "success",
                "message": f"스케줄이 {new_date}로 성공적으로 복사되었습니다.",
                "original_event_key": event_key,
                "new_event_info": result
            }
        else:
            return result

    except Exception as e:
        error_msg = handle_mcp_error(e, "schedule_copy")
        log_operation("schedule_copy", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": error_msg
        }


def bulk_update_schedule_status(event_keys: List[str], new_status: str) -> dict:
    """
    여러 스케줄의 상태를 일괄 업데이트합니다.
    
    Args:
        event_keys: 업데이트할 이벤트 키 리스트
        new_status: 새로운 상태 ("scheduled", "completed", "cancelled" 등)
        
    Returns:
        dict: 일괄 업데이트 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("bulk_schedule_update", "schedules", {"count": len(event_keys), "status": new_status}):
            log_operation("bulk_schedule_update", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        if not event_keys or len(event_keys) == 0:
            return {
                "status": "error",
                "message": "업데이트할 스케줄이 없습니다."
            }

        success_results = []
        error_results = []

        for event_key in event_keys:
            try:
                result = update_schedule_event(event_key, {"status": new_status})
                
                if result.get("status") == "success":
                    success_results.append({
                        "event_key": event_key,
                        "result": result
                    })
                else:
                    error_results.append({
                        "event_key": event_key,
                        "error": result.get("message", "알 수 없는 오류")
                    })

            except Exception as e:
                error_results.append({
                    "event_key": event_key,
                    "error": str(e)
                })

        # 결과 정리
        total_count = len(event_keys)
        success_count = len(success_results)
        error_count = len(error_results)

        log_operation("bulk_schedule_update", "schedules", {
            "total": total_count,
            "success": success_count,
            "errors": error_count,
            "status": new_status
        }, error_count == 0)

        return {
            "status": "success" if error_count == 0 else "partial_success",
            "message": f"전체 {total_count}개 중 {success_count}개 상태 업데이트 성공, {error_count}개 실패",
            "new_status": new_status,
            "total_count": total_count,
            "success_count": success_count,
            "error_count": error_count,
            "success_results": success_results,
            "error_results": error_results
        }

    except Exception as e:
        error_msg = handle_mcp_error(e, "bulk_schedule_update")
        log_operation("bulk_schedule_update", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": error_msg
        }


def generate_schedule_report(start_date: str, end_date: str, address: str = None) -> dict:
    """
    지정된 기간의 스케줄 리포트를 생성합니다.
    
    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
        address: 특정 주소 필터링 (선택사항)
        
    Returns:
        dict: 스케줄 리포트
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("schedule_report", "schedules", {"period": f"{start_date} ~ {end_date}"}):
            log_operation("schedule_report", "schedules", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 기간 내 스케줄 조회
        schedules_result = get_schedule_by_date_range(start_date, end_date, address)
        
        if schedules_result.get("status") != "success":
            return schedules_result
        
        schedules = schedules_result.get("schedules", [])
        
        # 리포트 데이터 생성
        report = {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "address_filter": address
            },
            "summary": {
                "total_schedules": len(schedules),
                "completed": len([s for s in schedules if s.get("status") == "completed"]),
                "scheduled": len([s for s in schedules if s.get("status") == "scheduled"]),
                "other_status": len([s for s in schedules if s.get("status") not in ["completed", "scheduled"]])
            },
            "daily_breakdown": {},
            "address_breakdown": {},
            "work_type_summary": {}
        }
        
        # 일별 분석
        for schedule in schedules:
            date = schedule.get("date", "Unknown")
            if date not in report["daily_breakdown"]:
                report["daily_breakdown"][date] = {
                    "total": 0,
                    "completed": 0,
                    "scheduled": 0,
                    "events": []
                }
            
            report["daily_breakdown"][date]["total"] += 1
            report["daily_breakdown"][date]["events"].append({
                "address": schedule.get("address", ""),
                "memo": schedule.get("memo", ""),
                "status": schedule.get("status", ""),
                "event_key": schedule.get("event_key", "")
            })
            
            if schedule.get("status") == "completed":
                report["daily_breakdown"][date]["completed"] += 1
            elif schedule.get("status") == "scheduled":
                report["daily_breakdown"][date]["scheduled"] += 1
        
        # 주소별 분석
        for schedule in schedules:
            addr = schedule.get("address", "Unknown")
            if addr not in report["address_breakdown"]:
                report["address_breakdown"][addr] = {
                    "total": 0,
                    "completed": 0,
                    "scheduled": 0
                }
            
            report["address_breakdown"][addr]["total"] += 1
            if schedule.get("status") == "completed":
                report["address_breakdown"][addr]["completed"] += 1
            elif schedule.get("status") == "scheduled":
                report["address_breakdown"][addr]["scheduled"] += 1
        
        # 작업 유형별 분석
        for schedule in schedules:
            work_type = schedule.get("memo", "Unknown")
            if work_type not in report["work_type_summary"]:
                report["work_type_summary"][work_type] = {
                    "count": 0,
                    "addresses": set()
                }
            
            report["work_type_summary"][work_type]["count"] += 1
            report["work_type_summary"][work_type]["addresses"].add(schedule.get("address", "Unknown"))
        
        # set을 list로 변환 (JSON 직렬화를 위해)
        for work_type in report["work_type_summary"]:
            report["work_type_summary"][work_type]["addresses"] = list(report["work_type_summary"][work_type]["addresses"])
        
        # 완료율 계산
        if report["summary"]["total_schedules"] > 0:
            report["summary"]["completion_rate"] = round(
                (report["summary"]["completed"] / report["summary"]["total_schedules"]) * 100, 2
            )
        else:
            report["summary"]["completion_rate"] = 0
        
        log_operation("schedule_report", "schedules", {
            "period": f"{start_date} ~ {end_date}",
            "address_filter": address,
            "total_schedules": len(schedules)
        }, True)
        
        return {
            "status": "success",
            "message": f"{start_date} ~ {end_date} 기간의 스케줄 리포트를 생성했습니다.",
            "report": report
        }

    except Exception as e:
        error_msg = handle_mcp_error(e, "schedule_report")
        log_operation("schedule_report", "schedules", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": error_msg
        }


def _format_schedule_display(schedules: List[dict], address_filter: str = None, title: str = None) -> str:
    """스케줄 목록을 사용자가 읽기 쉬운 형태로 포맷팅합니다."""
    if not schedules:
        if address_filter:
            return f"📅 '{address_filter}' 주소에 등록된 스케줄이 없습니다."
        else:
            return "📅 등록된 스케줄이 없습니다.\n\n새로운 스케줄을 등록하려면 '주소명 날짜 작업유형 등록해줘' 형태로 요청해주세요."
    
    formatted_list = f"📅 **{title or '스케줄 목록'}**\n\n"
    
    # 주소별로 그룹핑
    address_groups = {}
    for schedule in schedules:
        addr = schedule.get("address", "알 수 없음")
        if addr not in address_groups:
            address_groups[addr] = []
        address_groups[addr].append(schedule)
    
    for address, addr_schedules in address_groups.items():
        formatted_list += f"🏠 **{address}**\n"
        
        # 날짜순 정렬
        addr_schedules.sort(key=lambda x: x.get("date", ""))
        
        for schedule in addr_schedules:
            date = schedule.get("date", "날짜 없음")
            memo = schedule.get("memo", "작업 없음")
            status = schedule.get("status", "scheduled")
            status_icon = "✅" if status == "completed" else "⏰"
            
            formatted_list += f"   {status_icon} {date} - {memo}\n"
        
        formatted_list += "\n"
    
    formatted_list += f"**총 {len(schedules)}개의 스케줄이 등록되어 있습니다.**"
    
    return formatted_list