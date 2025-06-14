"""
주소 관리 에이전트

addressesJson 컬렉션의 CRUD 작업을 담당하는 전용 에이전트입니다.
단순하고 직접적인 주소 관리 행동들을 제공합니다.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import time
import json


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





def register_new_address(address_data: dict) -> dict:
    """
    새 주소를 addressesJson 컬렉션에 등록합니다.
    """
    try:
        # 📋 입력 데이터 정규화 - name을 address로 자동 매핑
        if address_data.get('name') and not address_data.get('address'):
            address_data['address'] = address_data['name']
        elif not address_data.get('address') and not address_data.get('name'):
            # 둘 다 없으면 기본값 설정
            address_data['address'] = address_data.get('name', '새 주소')

        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("write", "addressesJson", address_data):
            log_operation("address_register", "addressesJson", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 1. 필수 필드 검증 (주소만 필수)
        if not address_data.get('address'):
            log_operation("address_register", "addressesJson", {"error": "필수 필드 누락"}, False)
            return {
                "status": "error",
                "message": "주소 정보는 필수입니다."
            }

        # 입력된 주소 그대로 사용
        main_address = address_data['address'].strip()

        # Firebase 데이터 조회
        result = query_any_collection("addressesJson", limit=1000)
        
        # 호출 결과 확인 및 검증
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("주소 목록 조회 실패"), "address_register")
            return {
                "status": "error", 
                "message": error_msg
            }
        
        documents = []
        try:
            if isinstance(result, dict):
                if result.get("status") == "success":
                    documents = result.get("raw_data", {}).get("data", {}).get("documents", [])
                elif result.get("success"):
                    documents = result.get("data", {}).get("documents", [])
        except Exception as e:
            log_operation("address_register", "addressesJson", {"error": f"문서 파싱 실패: {e}"}, False)

        # 3. 중복 주소 확인 (description 필드 기준, 완전일치)
        for doc in documents:
            doc_desc = doc.get("data", {}).get("description", "").strip()
            if doc_desc == main_address:
                log_operation("address_register", "addressesJson", {"error": "중복 주소", "address": main_address}, False)
                return {
                    "status": "error",
                    "message": "이미 등록된 주소입니다."
                }

        # 4. 현재 시간 기록

        now = datetime.now().isoformat()

        # 5. dataJson 모든 필드 준비 (address 필드는 포함하지 않음)
        data_json_content = {
            "date": address_data.get('date', ''),
            "firstFloorPassword": address_data.get('firstFloorPassword', ''),
            "unitPassword": address_data.get('unitPassword', ''),
            "supervisorName": address_data.get('supervisorName', ''),
            "contractAmount": address_data.get('contractAmount', address_data.get('totalAmount', '')),
            "contractDate": address_data.get('contractDate', address_data.get('startDate', '')),
            "phoneLastFourDigits": address_data.get('phoneLastFourDigits', ''),
            "email": address_data.get('email', ''),
            "isCompleted": address_data.get('isCompleted', True),
            "createdAt": now,
            # 신규 필드 (지침 기반, address 제외)
            "area": address_data.get('area', ''),
            "startDate": address_data.get('startDate', ''),
            "endDate": address_data.get('endDate', ''),
            "hasSashWork": address_data.get('hasSashWork', False),
            "clientName": address_data.get('clientName', ''),
            "clientAddress": address_data.get('clientAddress', ''),
            "clientId": address_data.get('clientId', ''),
            "contractorContact": address_data.get('contractorContact', ''),
            "lastModified": now,
            "lastSaved": now
        }

        # 7. Firebase 문서 구조 - description에만 주요 주소 정보 저장
        document_data = {
            "dataJson": json.dumps(data_json_content, ensure_ascii=False),
            "description": main_address
        }

        # 8. 타임스탬프 기반 문서 ID 생성
        timestamp_id = str(int(time.time() * 1000))

        # Firebase 문서 추가
        result = firebase_client.add_document("addressesJson", document_data, timestamp_id)

        # 호출 결과 확인 및 검증
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("문서 추가 실패"), "address_register")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 성공 처리
        if result and (result.get("success") or result.get("status") == "success"):
            log_operation("address_register", "addressesJson", {
                "doc_id": timestamp_id,
                "address": main_address
            }, True)
            
            return {
                "status": "success",
                "message": f"주소 '{main_address}'가 성공적으로 등록되었습니다.",
                "doc_id": timestamp_id,
                "address": main_address
            }
        else:
            error_msg = handle_mcp_error(Exception("문서 저장 실패"), "address_register")
            return {
                "status": "error",
                "message": error_msg
            }

    except Exception as e:
        error_msg = handle_mcp_error(e, "address_register")
        log_operation("address_register", "addressesJson", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": error_msg
        }


def update_existing_address(identifier: str, update_data: dict) -> dict:
    """
    기존 주소 정보를 수정합니다.
    
    Args:
        identifier: 수정할 주소 식별자 (doc_id 또는 주소명/description)
        update_data: 수정할 데이터 (description, dataJson 내 필드들)
        
    Returns:
        dict: 수정 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("address_update", "addressesJson", update_data):
            log_operation("address_update", "addressesJson", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 1. identifier가 doc_id인지 주소명(description)인지 판단하고 문서 찾기
        doc_id = None
        existing_doc = None
        found_by_address = False
        
        # 숫자로만 구성되고 길이가 10자리 이상이면 타임스탬프 doc_id로 먼저 시도
        if identifier.isdigit() and len(identifier) >= 10:
            existing_doc = _get_document_by_id(identifier)
            if existing_doc['exists']:
                doc_id = identifier
        
        # doc_id로 찾지 못했거나 doc_id 형태가 아니면 주소명(description)으로 검색
        if not doc_id:
            found_by_address = True
            
            # 주소명으로 문서 찾기
            result = query_any_collection("addressesJson", limit=1000)
            
            if validate_response(result):
                documents = []
                try:
                    if isinstance(result, dict):
                        if result.get("status") == "success":
                            documents = result.get("raw_data", {}).get("data", {}).get("documents", [])
                        elif result.get("success"):
                            documents = result.get("data", {}).get("documents", [])
                except Exception:
                    pass
                
                # 주소명(description)으로 문서 찾기
                for doc in documents:
                    doc_description = doc.get("data", {}).get("description", "").strip()
                    if doc_description == identifier.strip():
                        doc_id = doc.get("id") or doc.get("_id") or doc.get("name", "").split("/")[-1]
                        existing_doc = {"exists": True, "data": doc.get("data", {})}
                        break
        
        if not doc_id or not existing_doc or not existing_doc['exists']:
            return {
                "status": "error",
                "message": f"주소 '{identifier}'를 찾을 수 없습니다. 정확한 주소명이나 문서 ID를 확인해주세요."
            }
        
        # 2. 기존 문서의 dataJson 파싱
        existing_doc_data = existing_doc['data']
        existing_data_json_str = existing_doc_data.get('dataJson', '{}') if 'dataJson' in existing_doc_data else '{}'
        try:
            existing_data_json = json.loads(existing_data_json_str) if existing_data_json_str else {}
        except json.JSONDecodeError:
            existing_data_json = {}
        
        # 3. description 필드 처리 (주소 수정)
        document_updates = {}
        
        # update_data에서 description 업데이트 확인
        if 'description' in update_data:
            new_description = update_data['description'].strip()
            if not new_description:
                return {
                    "status": "error",
                    "message": "주소(description)는 빈 값일 수 없습니다."
                }
            document_updates['description'] = new_description
        
        # 4. dataJson 업데이트 준비
        updated_data_json = {**existing_data_json}  # 기존 데이터 복사
        
        # Firebase 필드 매핑 (하위 호환성 고려)
        field_mapping = {
            'totalAmount': 'contractAmount',
            'startDate': 'contractDate'
        }
        
        # 업데이트 데이터를 dataJson에 병합 (description 제외)
        for key, value in update_data.items():
            if key != 'description':  # description은 문서 최상위 필드
                # 매핑된 필드 이름 사용
                mapped_key = field_mapping.get(key, key)
                updated_data_json[mapped_key] = value
        
        # lastModified 필드 업데이트
        updated_data_json['lastModified'] = datetime.now().isoformat()
        
        # 5. Firebase 업데이트를 위한 문서 데이터 준비
        document_updates["dataJson"] = json.dumps(updated_data_json, ensure_ascii=False)
        
        # Firebase 문서 업데이트
        result = firebase_client.update_document(f"addressesJson/{doc_id}", document_updates)
        
        # 호출 결과 확인 및 검증
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("Firebase 업데이트 실패"), "address_update")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 성공적인 응답 처리
        if result and result.get("success"):
            old_description = existing_doc_data.get('description', identifier)
            new_description = document_updates.get('description', old_description)
            
            log_operation("address_update", "addressesJson", {
                "doc_id": doc_id, 
                "identifier": identifier,
                "found_by": "address" if found_by_address else "doc_id",
                "fields_updated": list(update_data.keys())
            }, True)
            
            success_msg = f"주소 정보가 성공적으로 업데이트되었습니다."
            if 'description' in update_data:
                success_msg += f"\n기존 주소: {old_description}\n새로운 주소: {new_description}"
            
            return {
                "status": "success", 
                "message": success_msg,
                "updated_doc_id": doc_id,
                "old_description": old_description,
                "new_description": new_description,
                "updated_fields": list(update_data.keys())
            }
        else:
            error_msg = handle_mcp_error(Exception("Firebase 업데이트 실패"), "address_update")
            return {
                "status": "error",
                "message": error_msg
            }
            
    except Exception as e:
        log_operation("address_update", "addressesJson", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": handle_mcp_error(e, "address_update")
        }


def delete_address_record(identifier: str, force: bool = False) -> dict:
    """
    주소 레코드를 삭제합니다.
    
    Args:
        identifier: 삭제할 주소 식별자 (doc_id 또는 주소명/description)
        force: 강제 삭제 여부 (완전 문서 삭제인 경우)
        
    Returns:
        dict: 삭제 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("address_delete", "addressesJson"):
            log_operation("address_delete", "addressesJson", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 1. identifier가 doc_id인지 주소명(description)인지 판단하고 문서 찾기
        doc_id = None
        existing_doc = None
        found_by_address = False
        
        # 숫자로만 구성되고 길이가 10자리 이상이면 타임스탬프 doc_id로 먼저 시도
        if identifier.isdigit() and len(identifier) >= 10:
            existing_doc = _get_document_by_id(identifier)
            if existing_doc['exists']:
                doc_id = identifier
        
        # doc_id로 찾지 못했거나 doc_id 형태가 아니면 주소명(description)으로 검색
        if not doc_id:
            found_by_address = True
            # 주소명으로 문서 찾기
            result = query_any_collection("addressesJson", limit=1000)
            if validate_response(result):
                documents = []
                try:
                    if isinstance(result, dict):
                        if result.get("status") == "success":
                            documents = result.get("raw_data", {}).get("data", {}).get("documents", [])
                        elif result.get("success"):
                            documents = result.get("data", {}).get("documents", [])
                except Exception:
                    pass
                
                # 주소명(description)으로 문서 찾기
                for doc in documents:
                    doc_description = doc.get("data", {}).get("description", "").strip()
                    if doc_description == identifier.strip():
                        doc_id = doc.get("id") or doc.get("_id") or doc.get("name", "").split("/")[-1]
                        existing_doc = {"exists": True, "data": doc.get("data", {})}
                        break
        
        if not doc_id or not existing_doc or not existing_doc['exists']:
            log_operation("address_delete", "addressesJson", {"error": "문서 없음", "identifier": identifier}, False)
            return {
                "status": "error",
                "message": f"주소 '{identifier}'를 찾을 수 없습니다. 정확한 주소명이나 문서 ID를 확인해주세요."
            }
        
        # 문서 완전 삭제
        
        # Firebase에서 문서 완전 삭제
        document_path = f"addressesJson/{doc_id}"
        result = firebase_client.delete_document(document_path)
        
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("Firebase 삭제 실패"), "address_delete")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 성공적인 응답 처리
        if result and result.get("success"):
            log_operation("address_delete", "addressesJson", {"doc_id": doc_id, "action": "complete_deletion"}, True)
            return {
                "status": "success",
                "message": f"주소 '{identifier}'가 완전히 삭제되었습니다.",
                "deleted_doc_id": doc_id,
                "deleted_address": existing_doc['data'].get('description', 'Unknown')
            }
        else:
            error_msg = handle_mcp_error(Exception("Firebase 삭제 실패"), "address_delete")
            return {
                "status": "error",
                "message": error_msg
            }
            
    except Exception as e:
        log_operation("address_delete", "addressesJson", {"error": str(e)}, False)
        return {
            "status": "error", 
            "message": handle_mcp_error(e, "address_delete")
        }


def list_all_addresses(limit: int = 100, include_details: bool = False) -> dict:
    """
    모든 주소를 조회합니다.
    
    Args:
        limit: 조회할 주소 개수 제한
        include_details: 상세 정보 포함 여부
        
    Returns:
        dict: 주소 목록과 조회 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "addressesJson"):
            log_operation("list_addresses", "addressesJson", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # Firebase 데이터 조회
        result = query_any_collection("addressesJson", limit)
        
        # 호출 결과 확인 및 검증
        if not validate_response(result):
            error_msg = handle_mcp_error(Exception("주소 목록 조회 실패"), "list_addresses")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 성공적인 응답 처리
        if result and result.get("status") == "success":
            documents = result.get("data", {}).get("documents", [])
        else:
            error_msg = handle_mcp_error(Exception("응답 데이터 오류"), "list_addresses")
            return {
                "status": "error",
                "message": error_msg
            }
        
        addresses = []
        for doc in documents:
            # 문서 ID 추출 - Firebase 응답에서는 "id" 필드 사용
            doc_id = doc.get("id", "")
            doc_data = doc.get("data", {})
            
            # dataJson 파싱
            data_json_str = doc_data.get("dataJson", "{}")
            try:
                data_json = json.loads(data_json_str) if data_json_str else {}
            except json.JSONDecodeError:
                data_json = {}
                
            if include_details:
                # 상세 정보 포함
                addresses.append({
                    "doc_id": doc_id,
                    "address": doc_data.get("description", ""),  # 주소는 description에서
                    "date": data_json.get("date", ""),
                    "firstFloorPassword": data_json.get("firstFloorPassword", ""),
                    "unitPassword": data_json.get("unitPassword", ""),
                    "supervisorName": data_json.get("supervisorName", ""),
                    "contractAmount": data_json.get("contractAmount", ""),
                    "contractDate": data_json.get("contractDate", ""),
                    "phoneLastFourDigits": data_json.get("phoneLastFourDigits", ""),
                    "email": data_json.get("email", ""),
                    "isCompleted": data_json.get("isCompleted", False),
                    "createdAt": data_json.get("createdAt", "")
                })
            else:
                # 기본 정보만 - 주소명만 포함
                addresses.append({
                    "doc_id": doc_id,
                    "address": doc_data.get("description", "")  # 주소는 description에서
                })
        
        log_operation("list_addresses", "addressesJson", {"count": len(addresses)}, True)
        
        # 사용자가 읽기 쉬운 형태로 포맷팅
        if addresses:
            # 유효한 주소만 필터링 (잘못 등록된 데이터 제외)
            valid_addresses = []
            for addr in addresses:
                address_text = addr.get('address', '').strip()
                # 명령어나 요청 형태의 잘못된 데이터 제외
                if (address_text and 
                    not any(keyword in address_text.lower() for keyword in 
                           ['보여주세요', '등록해줘', '일정', '확인하고', '를 등록', '설정해주세요', '변경해주세요']) and
                    len(address_text) > 3 and  # 너무 짧은 주소 제외
                    not address_text in ['새 주소', '11114']):  # 테스트용 데이터 제외
                    valid_addresses.append(addr)
            
            if valid_addresses:
                if include_details:
                    # 상세 모드: 모든 정보 표시
                    formatted_list = "📋 등록된 주소 상세 목록\n\n"
                    for i, addr in enumerate(valid_addresses, 1):
                        formatted_list += f"{i}. {addr.get('address', '주소 없음')}\n"
                        formatted_list += f"   - 담당자: {addr.get('supervisorName', '없음')}\n"
                        formatted_list += f"   - 계약금액: {addr.get('contractAmount', '없음')}\n"
                        formatted_list += f"   - 계약일: {addr.get('contractDate', '없음')}\n"
                        formatted_list += f"   - 상태: {'완료' if addr.get('isCompleted') else '진행중'}\n"
                        formatted_list += f"   - 문서ID: {addr.get('doc_id', '없음')}\n\n"
                else:
                    # 기본 모드: 주소명만 간단히 표시
                    formatted_list = "📋 등록된 주소 목록\n\n"
                    for i, addr in enumerate(valid_addresses, 1):
                        formatted_list += f"{i}. {addr.get('address', '주소 없음')}\n"
                
                formatted_list += f"\n총 {len(valid_addresses)}개의 주소가 등록되어 있습니다."
                if not include_details:
                    formatted_list += "\n\n💡 상세 정보가 필요하면 '주소 상세 목록 보여줘'라고 요청해주세요."
            else:
                formatted_list = "📋 유효한 주소가 없습니다.\n\n새로운 주소를 등록하려면 '주소명 등록해줘' 형태로 요청해주세요."
        else:
            formatted_list = "📋 등록된 주소가 없습니다.\n\n새로운 주소를 등록하려면 '주소명 등록해줘' 형태로 요청해주세요."
        
        return {
            "status": "success",
            "addresses": addresses,
            "total_count": len(addresses),
            "formatted_list": formatted_list,
            "message": formatted_list  # 사용자에게 직접 표시될 메시지
        }
        
    except Exception as e:
        log_operation("list_addresses", "addressesJson", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": handle_mcp_error(e, "list_addresses")
        }


def search_addresses_by_keyword(keyword: str, threshold: float = 0.6) -> dict:
    """
    키워드로 주소를 검색합니다.
    
    Args:
        keyword: 검색할 키워드
        threshold: 유사도 임계값 (0.0-1.0)
        
    Returns:
        dict: 검색 결과
    """
    try:
        # Firebase MCP 호출 의무화 검증
        if not validate_mcp_call("data_query", "addressesJson", {"keyword": keyword}):
            log_operation("search_addresses", "addressesJson", {"error": "MCP 호출 의무화 검증 실패"}, False)
            return {
                "status": "error",
                "message": "데이터 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

        # 유효성 검증
        if not keyword or keyword.strip() == "":
            log_operation("search_addresses", "addressesJson", {"error": "빈 키워드"}, False)
            return {
                "status": "error",
                "message": "검색 키워드를 입력해주세요."
            }
        
        # Firebase 데이터 조회
        all_addresses_result = list_all_addresses(limit=200, include_details=True)
        
        # 호출 결과 확인 및 검증
        if not validate_response(all_addresses_result):
            error_msg = handle_mcp_error(Exception("주소 목록 조회 실패"), "search_addresses")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 성공적인 응답 처리
        if all_addresses_result and all_addresses_result.get("status") == "success":
            addresses = all_addresses_result.get("addresses", [])
        else:
            error_msg = handle_mcp_error(Exception("주소 검색용 데이터 오류"), "search_addresses")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 키워드 매칭 검색
        matched_addresses = []
        keyword_lower = keyword.lower().strip()
        
        for addr in addresses:
            address_text = addr.get("address", "").lower()
            supervisor_name = addr.get("supervisorName", "").lower()
            
            # 정확한 일치 또는 포함 검색
            if (keyword_lower in address_text or 
                keyword_lower in supervisor_name or
                address_text.find(keyword_lower) != -1):
                
                # 유사도 점수 계산 (간단한 방식)
                similarity = 1.0 if keyword_lower == address_text else 0.8
                if keyword_lower in address_text:
                    similarity = max(similarity, 0.7)
                
                if similarity >= threshold:
                    addr["similarity"] = similarity
                    matched_addresses.append(addr)
        
        # 유사도 순으로 정렬
        matched_addresses.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        
        log_operation("search_addresses", "addressesJson", {"keyword": keyword, "matches": len(matched_addresses)}, True)
        return {
            "status": "success",
            "addresses": matched_addresses,
            "total_matches": len(matched_addresses),
            "search_keyword": keyword,
            "message": f"'{keyword}' 검색 결과: {len(matched_addresses)}개의 주소를 찾았습니다."
        }
        
    except Exception as e:
        log_operation("search_addresses", "addressesJson", {"error": str(e)}, False)
        return {
            "status": "error",
            "message": handle_mcp_error(e, "search_addresses")
        }


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

 