import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math
from ..utils.address_validator import AddressValidator, validate_address, standardize_address

def request_site_address() -> str:
    """사용자에게 현장 주소 입력을 요청합니다.
    
    Returns:
        str: "현장 주소를 입력해 주세요."라는 안내 메시지
    """
    return "현장 주소를 입력해 주세요."

def search_address_info(address: str, firebase_query_function) -> dict:
    """addresses 컬렉션에서 주소 관련 정보를 조회합니다.
    
    Args:
        address: 검색할 현장 주소
        firebase_query_function: Firebase 컬렉션 조회 함수
        
    Returns:
        dict: 조회 결과와 추출된 정보
    """
    try:
        # 주소 검증 및 표준화
        validator = AddressValidator()
        validation_result = validator.validate_address_format(address)
        standardized_addr = validator.extract_address_components(address).standardized
        
        # 주소 검증 결과 출력
        if not validation_result['is_valid']:
            print(f"⚠️ 주소 검증 경고:")
            for issue in validation_result['issues']:
                print(f"  - {issue}")
            for suggestion in validation_result['suggestions']:
                print(f"  💡 {suggestion}")
            print(f"📍 표준화된 주소: {standardized_addr}")
        
        # addresses 컬렉션 조회
        response = firebase_query_function("addresses", limit=100)
        
        if not response.get("success"):
            return {
                "status": "error",
                "message": f"addresses 컬렉션 조회 실패: {response.get('message', '알 수 없는 오류')}"
            }
        
        documents = response.get("raw_data", {}).get("data", {}).get("documents", [])
        
        # 주소와 매칭되는 문서 찾기 (정확한 매칭 + 유사도 매칭)
        matching_doc = None
        all_addresses = []
        
        for doc in documents:
            doc_data = doc.get("data", {})
            doc_address = doc_data.get("address", "")
            all_addresses.append(doc_address)
            
            # 1차: 정확한 부분 매칭
            if (address.strip() in doc_address or doc_address in address.strip() or
                standardized_addr in doc_address or doc_address in standardized_addr):
                matching_doc = doc_data
                print(f"✅ 정확한 매칭 찾음: {doc_address}")
                break
        
        # 2차: 유사도 기반 매칭 (정확한 매칭이 없을 경우)
        if not matching_doc and all_addresses:
            similar_addresses = validator.find_similar_addresses(
                address, all_addresses, threshold=0.7
            )
            
            if similar_addresses:
                best_match, similarity = similar_addresses[0]
                print(f"📍 유사한 주소 발견 (유사도: {similarity:.2f}): {best_match}")
                
                # 유사도가 높은 주소로 다시 검색
                for doc in documents:
                    doc_data = doc.get("data", {})
                    if doc_data.get("address", "") == best_match:
                        matching_doc = doc_data
                        break
                
                # 다른 유사 주소들도 출력
                if len(similar_addresses) > 1:
                    print("🔍 다른 유사 주소들:")
                    for addr, sim in similar_addresses[1:4]:  # 상위 3개만
                        print(f"  - {addr} (유사도: {sim:.2f})")
        
        if not matching_doc:
            return {
                "status": "not_found",
                "message": f"주소 '{address}'와 매칭되는 정보를 찾을 수 없습니다.",
                "suggestions": validator.suggest_corrections(address) if validation_result else []
            }
        
        return {
            "status": "success",
            "data": {
                "address": matching_doc.get("address", ""),
                "startDate": matching_doc.get("startDate", ""),
                "endDate": matching_doc.get("endDate", ""),
                "totalAmount": matching_doc.get("totalAmount", ""),
                "phoneLastFourDigits": matching_doc.get("phoneLastFourDigits", "")
            },
            "message": "addresses 컬렉션에서 정보를 찾았습니다."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"addresses 컬렉션 조회 중 오류: {str(e)}"
        }

def search_schedule_info(address: str, firebase_query_function) -> dict:
    """schedules 컬렉션에서 공사 일정 정보를 조회합니다.
    
    Args:
        address: 검색할 현장 주소
        firebase_query_function: Firebase 컬렉션 조회 함수
        
    Returns:
        dict: 조회 결과와 시작일/마감일 정보
    """
    try:
        # 주소 검증 및 표준화
        validator = AddressValidator()
        standardized_addr = validator.extract_address_components(address).standardized
        
        # schedules 컬렉션 조회
        response = firebase_query_function("schedules", limit=100)
        
        if not response.get("success"):
            return {
                "status": "error",
                "message": f"schedules 컬렉션 조회 실패: {response.get('message', '알 수 없는 오류')}"
            }
        
        documents = response.get("raw_data", {}).get("data", {}).get("documents", [])
        
        # 주소와 매칭되는 문서 찾기 (정확한 매칭 + 유사도 매칭)
        matching_doc = None
        all_addresses = []
        
        for doc in documents:
            doc_data = doc.get("data", {})
            doc_id = doc.get("id", "")
            doc_address = doc_data.get("address", "")
            all_addresses.append(doc_address)
            
            # 1차: 정확한 매칭 (문서 ID 또는 address 필드에서)
            if (address.strip() in doc_address or doc_address in address.strip() or 
                address.strip() in doc_id or doc_id in address.strip() or
                standardized_addr in doc_address or doc_address in standardized_addr or
                standardized_addr in doc_id or doc_id in standardized_addr):
                matching_doc = doc_data
                print(f"✅ schedules에서 정확한 매칭 찾음: {doc_address}")
                break
        
        # 2차: 유사도 기반 매칭 (정확한 매칭이 없을 경우)
        if not matching_doc and all_addresses:
            similar_addresses = validator.find_similar_addresses(
                address, all_addresses, threshold=0.7
            )
            
            if similar_addresses:
                best_match, similarity = similar_addresses[0]
                print(f"📍 schedules에서 유사한 주소 발견 (유사도: {similarity:.2f}): {best_match}")
                
                # 유사도가 높은 주소로 다시 검색
                for doc in documents:
                    doc_data = doc.get("data", {})
                    if doc_data.get("address", "") == best_match:
                        matching_doc = doc_data
                        break
        
        if not matching_doc:
            return {
                "status": "not_found",
                "message": f"schedules 컬렉션에서 주소 '{address}'와 매칭되는 정보를 찾을 수 없습니다."
            }
        
        # eventsJson 파싱
        events_json = matching_doc.get("eventsJson", "")
        if not events_json:
            return {
                "status": "error",
                "message": "eventsJson 필드가 비어있습니다."
            }
        
        try:
            events = json.loads(events_json)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "eventsJson 파싱에 실패했습니다."
            }
        
        # 시작일과 마감일 찾기
        start_date = ""
        end_date = ""
        
        for event in events:
            title = event.get("title", "").replace(" ", "")  # 공백 제거
            date = event.get("date", "")
            
            # 철거 공사 찾기 (시작일)
            if "철거공사" in title:
                start_date = date
            
            # 실리콘 공사 찾기 (마감일)
            if "실리콘공사" in title:
                end_date = date
        
        return {
            "status": "success",
            "data": {
                "startDate": start_date,
                "endDate": end_date
            },
            "message": f"schedules 컬렉션에서 일정 정보를 찾았습니다. 시작일: {start_date}, 마감일: {end_date}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"schedules 컬렉션 조회 중 오류: {str(e)}"
        }

def merge_project_info(address_data: dict, schedule_data: dict) -> dict:
    """addresses와 schedules 데이터를 병합합니다.
    
    Args:
        address_data: addresses 컬렉션에서 가져온 데이터
        schedule_data: schedules 컬렉션에서 가져온 데이터
        
    Returns:
        dict: 병합된 프로젝트 정보
    """
    merged_data = address_data.copy()
    
    # startDate가 비어있으면 schedules에서 가져오기
    if not merged_data.get("startDate") and schedule_data.get("startDate"):
        merged_data["startDate"] = schedule_data["startDate"]
    
    # endDate가 비어있으면 schedules에서 가져오기
    if not merged_data.get("endDate") and schedule_data.get("endDate"):
        merged_data["endDate"] = schedule_data["endDate"]
    
    return merged_data

def calculate_payment_schedule(total_amount: int, start_date: str, end_date: str) -> dict:
    """분할 지급 계획을 계산합니다.
    
    Args:
        total_amount: 총 공사금액
        start_date: 공사 시작일 (YYYY-MM-DD)
        end_date: 공사 마감일 (YYYY-MM-DD)
        
    Returns:
        dict: 분할 지급 계획 데이터
    """
    try:
        # 막대금 고정값
        final_payment = 3000000  # 3,000,000원
        
        # 분할할 실제 금액
        remaining_amount = total_amount - final_payment
        
        # 1,000만원 단위로 분할
        unit_amount = 10000000  # 1,000만원
        full_payments = remaining_amount // unit_amount
        remainder = remaining_amount % unit_amount
        
        # 분할 회차 계산
        total_rounds = full_payments
        if remainder > 0:
            total_rounds += 1
        
        # 날짜 계산
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # 총 일수 계산
        total_days = (end_dt - start_dt).days
        
        # 회차별 일수 계산 (균등 분배)
        if total_rounds > 1:
            days_per_round = total_days // (total_rounds - 1)
        else:
            days_per_round = 0
        
        # 분할 계획 생성
        payment_schedule = []
        
        # 1차~n차 (1,000만원 단위)
        for i in range(full_payments):
            round_num = i + 1
            payment_date = start_dt + timedelta(days=i * days_per_round)
            
            # 한국시간 오후 2시로 설정 (UTC+9)
            scheduled_time = payment_date.replace(hour=14, minute=0, second=0, microsecond=0)
            scheduled_time_str = scheduled_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            payment_schedule.append({
                "round": f"{round_num}회차",
                "amount": unit_amount,
                "amount_formatted": f"{unit_amount:,}원",
                "scheduledDate": payment_date.strftime("%Y-%m-%d"),
                "scheduledTime": scheduled_time_str,
                "description": "1000단위 등분"
            })
        
        # 자투리 금액이 있는 경우 마지막 회차 추가
        if remainder > 0:
            final_round_num = full_payments + 1
            final_payment_date = end_dt
            
            # 한국시간 오후 2시로 설정
            final_scheduled_time = final_payment_date.replace(hour=14, minute=0, second=0, microsecond=0)
            final_scheduled_time_str = final_scheduled_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            payment_schedule.append({
                "round": f"{final_round_num}회차",
                "amount": remainder,
                "amount_formatted": f"{remainder:,}원",
                "scheduledDate": final_payment_date.strftime("%Y-%m-%d"),
                "scheduledTime": final_scheduled_time_str,
                "description": "자투리 금액만 지급"
            })
        
        # 막대금(+추가금) 추가
        payment_schedule.append({
            "round": "막대금(+추가금)",
            "amount": final_payment,
            "amount_formatted": f"{final_payment:,}원",
            "scheduledDate": "(날짜 없음)",
            "scheduledTime": "",
            "description": "마지막 별도 지급"
        })
        
        # 총액 검증
        calculated_total = sum(item["amount"] for item in payment_schedule)
        
        return {
            "status": "success",
            "payment_schedule": payment_schedule,
            "summary": {
                "total_amount": total_amount,
                "calculated_total": calculated_total,
                "total_rounds": total_rounds + 1,  # 막대금 포함
                "is_valid": calculated_total == total_amount
            },
            "message": f"분할 지급 계획이 생성되었습니다. 총 {total_rounds + 1}회차"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"분할 지급 계획 계산 중 오류: {str(e)}"
        }

def format_payment_table(payment_schedule: List[dict]) -> str:
    """분할 지급 계획을 표 형식으로 포맷팅합니다.
    
    Args:
        payment_schedule: 분할 지급 계획 리스트
        
    Returns:
        str: 표 형식으로 포맷팅된 문자열
    """
    table = "📋 분할 지급 계획표\n\n"
    table += "| 회차 | 금액 | 지급일 | 설명 |\n"
    table += "|------|------|--------|------|\n"
    
    for item in payment_schedule:
        round_col = item["round"]
        amount_col = item["amount_formatted"]
        date_col = item["scheduledDate"]
        desc_col = item["description"]
        
        table += f"| {round_col} | {amount_col} | {date_col} | {desc_col} |\n"
    
    return table

def create_construction_payment_plan(address: str, firebase_query_function) -> dict:
    """공사 분할 지급 계획을 전체적으로 처리하는 메인 함수입니다.
    
    Args:
        address: 현장 주소
        firebase_query_function: Firebase 컬렉션 조회 함수
        
    Returns:
        dict: 완성된 분할 지급 계획
    """
    try:
        # 1. addresses 컬렉션 조회
        address_result = search_address_info(address, firebase_query_function)
        
        if address_result["status"] == "error":
            return address_result
        
        if address_result["status"] == "not_found":
            return {
                "status": "error",
                "message": f"주소 '{address}'에 대한 정보를 찾을 수 없습니다. 정확한 주소를 입력해 주세요."
            }
        
        address_data = address_result["data"]
        
        # 2. schedules 컬렉션 조회 (날짜 정보가 부족한 경우)
        schedule_data = {}
        if not address_data.get("startDate") or not address_data.get("endDate"):
            schedule_result = search_schedule_info(address, firebase_query_function)
            if schedule_result["status"] == "success":
                schedule_data = schedule_result["data"]
        
        # 3. 정보 병합
        merged_info = merge_project_info(address_data, schedule_data)
        
        # 4. 필수 정보 확인
        if not merged_info.get("totalAmount"):
            return {
                "status": "error",
                "message": "총 공사금액 정보가 없습니다. 총 공사금액을 입력해 주세요."
            }
        
        if not merged_info.get("startDate") or not merged_info.get("endDate"):
            return {
                "status": "error",
                "message": "공사 시작일 또는 마감일 정보가 부족합니다. schedules 컬렉션에서도 찾을 수 없었습니다."
            }
        
        # 5. 총 공사금액을 숫자로 변환
        try:
            total_amount = int(merged_info["totalAmount"])
        except (ValueError, TypeError):
            return {
                "status": "error",
                "message": f"총 공사금액 형식이 올바르지 않습니다: {merged_info['totalAmount']}"
            }
        
        # 6. 정보 요약
        summary_info = {
            "현장 주소": merged_info.get("address", ""),
            "총 공사금액": f"{total_amount:,}원",
            "공사 시작일": merged_info.get("startDate", ""),
            "공사 마감일": merged_info.get("endDate", ""),
            "고객 전화번호 뒷자리": merged_info.get("phoneLastFourDigits", "")
        }
        
        # 7. 분할 지급 계획 계산
        payment_result = calculate_payment_schedule(
            total_amount, 
            merged_info["startDate"], 
            merged_info["endDate"]
        )
        
        if payment_result["status"] == "error":
            return payment_result
        
        # 8. 표 형식 생성
        payment_table = format_payment_table(payment_result["payment_schedule"])
        
        return {
            "status": "success",
            "summary_info": summary_info,
            "payment_schedule": payment_result["payment_schedule"],
            "payment_table": payment_table,
            "calculation_summary": payment_result["summary"],
            "message": "공사 분할 지급 계획이 완성되었습니다."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"공사 분할 지급 계획 생성 중 오류: {str(e)}"
        } 