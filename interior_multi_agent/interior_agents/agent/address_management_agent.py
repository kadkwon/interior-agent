"""
주소 관리 에이전트

addressesJson 컬렉션의 CRUD 작업을 담당하는 전용 에이전트입니다.
단순하고 직접적인 주소 관리 행동들을 제공합니다.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import time
import json

# Firebase 클라이언트 및 도구들
try:
    from ..client.firebase_client import firebase_client
    from ..tools.firebase_tools import query_any_collection
    from ..utils.address_validator import AddressValidator
except ImportError:
    # ADK Web 환경에서는 절대 import
    from interior_agents.client.firebase_client import firebase_client
    from interior_agents.tools.firebase_tools import query_any_collection
    from interior_agents.utils.address_validator import AddressValidator


def register_new_address(address_data: dict) -> dict:
    """
    새 주소를 addressesJson 컬렉션에 등록합니다.
    
    Args:
        address_data: 등록할 주소 정보 (address 필드만 필수)
        {
            "address": "월배아이파크 1차 109동 2401호",                      # 필수 (description에 저장)
            "date": "",                                                   # 선택
            "firstFloorPassword": "#2401*3345#",                          # 선택
            "unitPassword": "1234*",                                      # 선택
            "supervisorName": "조대현",                                    # 선택
            "contractAmount": "14245000",                                 # 선택
            "contractDate": "2024-01-15",                                 # 선택 (Timestamp 변환됨)
            "phoneLastFourDigits": "01042640810",                         # 선택
            "email": "",                                                  # 선택
            "isCompleted": True,                                          # 선택
            "siteNumber": 26                                              # 선택
        }
        
    Returns:
        dict: 등록 결과 (문서 ID는 타임스탬프 형식으로 자동 생성)
    """
    try:
        # 1. 필수 필드 검증 (주소만 필수)
        if not address_data.get('address'):
            return {
                "status": "error",
                "message": "주소 정보는 필수입니다."
            }
        
        # 2. 주소 검증 및 표준화
        validator = AddressValidator()
        validation_result = validator.validate_address_format(address_data['address'])
        address_info = validator.extract_address_components(address_data['address'])
        
        if not validation_result['is_valid']:
            return {
                "status": "warning", 
                "message": "주소 형식에 문제가 있지만 등록을 진행합니다.",
                "issues": validation_result['issues'],
                "suggestions": validation_result['suggestions']
            }
        
        # 3. 중복 주소 체크
        duplicate_check = _check_duplicate_address(address_data['address'])
        if duplicate_check['has_duplicate']:
            return {
                "status": "error",
                "message": f"유사한 주소가 이미 존재합니다: {duplicate_check['similar_address']}",
                "existing_doc_id": duplicate_check.get('doc_id'),
                "similarity_score": duplicate_check.get('similarity', 0)
            }
        
        # 4. 타임스탬프 기반 문서 ID 생성
        timestamp_id = str(int(time.time() * 1000))  # 밀리초 단위 타임스탬프
        
        # 5. 문서 데이터 준비 (Firebase 정확한 구조)
        now = datetime.now().isoformat()
        
        # contractDate를 Firebase Timestamp 형식으로 변환
        contract_date = address_data.get('contractDate', address_data.get('startDate', ''))
        if contract_date:
            try:
                from datetime import datetime as dt
                if isinstance(contract_date, str):
                    parsed_date = dt.fromisoformat(contract_date.replace('Z', '+00:00'))
                    contract_date_obj = {
                        "seconds": int(parsed_date.timestamp()),
                        "nanoseconds": 0
                    }
                else:
                    contract_date_obj = contract_date
            except:
                contract_date_obj = ""
        else:
            contract_date_obj = ""
        
        # dataJson 필드 - 정확한 Firebase 형식 (주소 정보 제외)
        data_json_content = {
            "date": address_data.get('date', ''),
            "firstFloorPassword": address_data.get('firstFloorPassword', ''),
            "unitPassword": address_data.get('unitPassword', ''),
            "supervisorName": address_data.get('supervisorName', ''),
            "contractAmount": address_data.get('contractAmount', address_data.get('totalAmount', '')),
            "contractDate": contract_date_obj,
            "phoneLastFourDigits": address_data.get('phoneLastFourDigits', ''),
            "email": address_data.get('email', ''),
            "isCompleted": address_data.get('isCompleted', False),
            "createdAt": now,
            "siteNumber": address_data.get('siteNumber', 0)
        }
        
        # Firebase 문서 구조 - 주소는 description에!
        document_data = {
            "dataJson": json.dumps(data_json_content, ensure_ascii=False),
            "description": address_data['address']  # 주소는 description 필드에 저장
        }
        
        # 6. Firebase에 문서 추가 (커스텀 ID 사용)
        result = firebase_client.add_document("addressesJson", document_data, timestamp_id)
        
        if result.get("success"):
            return {
                "status": "success",
                "message": f"주소가 성공적으로 등록되었습니다.",
                "doc_id": timestamp_id,
                "standardized_address": address_info.standardized,
                "confidence_score": address_info.confidence_score,
                "registered_fields": {
                    "description": address_data['address'],  # 주소는 description에 저장
                    "date": address_data.get('date', '미입력'),
                    "firstFloorPassword": address_data.get('firstFloorPassword', '미입력'),
                    "unitPassword": address_data.get('unitPassword', '미입력'),
                    "supervisorName": address_data.get('supervisorName', '미입력'),
                    "contractAmount": address_data.get('contractAmount', address_data.get('totalAmount', '미입력')),
                    "contractDate": address_data.get('contractDate', address_data.get('startDate', '미입력')),
                    "phoneLastFourDigits": address_data.get('phoneLastFourDigits', '미입력'),
                    "email": address_data.get('email', '미입력'),
                    "isCompleted": address_data.get('isCompleted', '미입력'),
                    "siteNumber": address_data.get('siteNumber', '미입력')
                }
            }
        else:
            return {
                "status": "error",
                "message": f"Firebase 등록 실패: {result.get('message', '알 수 없는 오류')}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"주소 등록 중 오류 발생: {str(e)}"
        }


def update_existing_address(doc_id: str, update_data: dict) -> dict:
    """
    기존 주소 정보를 수정합니다.
    
    Args:
        doc_id: 수정할 문서 ID
        update_data: 수정할 데이터
        
    Returns:
        dict: 수정 결과
    """
    try:
        # 1. 문서 존재 여부 확인
        existing_doc = _get_document_by_id(doc_id)
        if not existing_doc['exists']:
            return {
                "status": "error",
                "message": f"문서 ID '{doc_id}'를 찾을 수 없습니다."
            }
        
        # 2. 기존 문서의 dataJson 파싱
        existing_doc_data = existing_doc['data']
        existing_data_json_str = existing_doc_data.get('dataJson', '{}') if 'dataJson' in existing_doc_data else '{}'
        try:
            existing_data_json = json.loads(existing_data_json_str) if existing_data_json_str else {}
        except json.JSONDecodeError:
            existing_data_json = {}
        
        # 3. 주소가 변경되는 경우 검증
        if 'address' in update_data:
            validator = AddressValidator()
            validation_result = validator.validate_address_format(update_data['address'])
            address_info = validator.extract_address_components(update_data['address'])
            
            # 표준화된 주소도 함께 업데이트
            update_data['standardizedAddress'] = address_info.standardized
            update_data['confidenceScore'] = address_info.confidence_score
            
            if not validation_result['is_valid']:
                return {
                    "status": "warning",
                    "message": "주소 형식에 문제가 있지만 수정을 진행합니다.",
                    "issues": validation_result['issues']
                }
        
        # 4. dataJson 업데이트 준비
        updated_data_json = {**existing_data_json}  # 기존 데이터 복사
        
        # Firebase 필드 매핑 (하위 호환성 고려)
        field_mapping = {
            'totalAmount': 'contractAmount',
            'startDate': 'contractDate'
        }
        
        # 업데이트할 필드들을 dataJson에 병합
        for key, value in update_data.items():
            if key == 'description':
                continue  # description은 별도 필드
            # 필드명 매핑 처리
            actual_key = field_mapping.get(key, key)
            updated_data_json[actual_key] = value
        
        # 5. 최종 문서 데이터 준비
        final_update_data = {
            "dataJson": json.dumps(updated_data_json, ensure_ascii=False)
        }
        
        # 주소 변경 시 description 필드 업데이트
        if 'address' in update_data:
            final_update_data['description'] = update_data['address']
        
        # 6. Firebase 문서 업데이트
        document_path = f"addressesJson/{doc_id}"
        result = firebase_client.update_document(document_path, final_update_data, merge=True)
        
        if result.get("success"):
            return {
                "status": "success",
                "message": f"주소 정보가 성공적으로 수정되었습니다.",
                "doc_id": doc_id,
                "updated_fields": list(update_data.keys())
            }
        else:
            return {
                "status": "error",
                "message": f"Firebase 수정 실패: {result.get('message', '알 수 없는 오류')}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"주소 수정 중 오류 발생: {str(e)}"
        }


def delete_address_record(doc_id: str, force: bool = False) -> dict:
    """
    주소 레코드를 삭제합니다.
    
    Args:
        doc_id: 삭제할 문서 ID
        force: 강제 삭제 여부 (관련 데이터 확인 생략)
        
    Returns:
        dict: 삭제 결과
    """
    try:
        # 1. 문서 존재 여부 확인
        existing_doc = _get_document_by_id(doc_id)
        if not existing_doc['exists']:
            return {
                "status": "error",
                "message": f"문서 ID '{doc_id}'를 찾을 수 없습니다."
            }
        
        # 2. 관련 데이터 확인 (schedules 컬렉션)
        if not force:
            related_data = _check_related_data(existing_doc['data'].get('address', ''))
            if related_data['has_related']:
                return {
                    "status": "warning",
                    "message": "이 주소와 관련된 다른 데이터가 있습니다. 정말 삭제하시겠습니까?",
                    "related_collections": related_data['collections'],
                    "suggestion": "force=True 옵션을 사용하여 강제 삭제할 수 있습니다."
                }
        
        # 3. Firebase에서 문서 삭제
        document_path = f"addressesJson/{doc_id}"
        result = firebase_client.delete_document(document_path)
        
        if result.get("success"):
            return {
                "status": "success",
                "message": f"주소 레코드가 성공적으로 삭제되었습니다.",
                "deleted_doc_id": doc_id,
                "deleted_address": existing_doc['data'].get('address', 'Unknown')
            }
        else:
            return {
                "status": "error",
                "message": f"Firebase 삭제 실패: {result.get('message', '알 수 없는 오류')}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"주소 삭제 중 오류 발생: {str(e)}"
        }


def list_all_addresses(limit: int = 100, include_details: bool = False) -> dict:
    """
    모든 주소 목록을 조회합니다.
    
    Args:
        limit: 조회할 최대 문서 수
        include_details: 상세 정보 포함 여부
        
    Returns:
        dict: 주소 목록
    """
    try:
        # query_any_collection 활용
        result = query_any_collection("addressesJson", limit)
        
        if result.get("status") == "success":
            documents = result.get("raw_data", {}).get("data", {}).get("documents", [])
            
            addresses = []
            for doc in documents:
                doc_data = doc.get("data", {})
                doc_id = doc.get("id", "Unknown")
                
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
                        "siteNumber": data_json.get("siteNumber", 0),
                        "createdAt": data_json.get("createdAt", "")
                    })
                else:
                    # 기본 정보만
                    addresses.append({
                        "doc_id": doc_id,
                        "address": doc_data.get("description", ""),  # 주소는 description에서
                        "contractAmount": data_json.get("contractAmount", ""),
                        "supervisorName": data_json.get("supervisorName", "")
                    })
            
            return {
                "status": "success",
                "addresses": addresses,
                "total_count": len(addresses),
                "message": f"총 {len(addresses)}개의 주소를 조회했습니다."
            }
        else:
            return {
                "status": "error", 
                "message": f"주소 목록 조회 실패: {result.get('message', '알 수 없는 오류')}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"주소 목록 조회 중 오류 발생: {str(e)}"
        }


def search_addresses_by_keyword(keyword: str, threshold: float = 0.6) -> dict:
    """
    키워드로 주소를 검색합니다.
    
    Args:
        keyword: 검색 키워드
        threshold: 유사도 임계값 (0.0 ~ 1.0)
        
    Returns:
        dict: 검색 결과
    """
    try:
        # 1. 모든 주소 조회
        all_addresses_result = list_all_addresses(limit=500)
        if all_addresses_result.get("status") != "success":
            return all_addresses_result
        
        addresses = all_addresses_result.get("addresses", [])
        
        # 2. 주소 유사도 검색 (description 필드에서)
        validator = AddressValidator()
        address_list = [addr["address"] for addr in addresses if addr.get("address")]
        
        similar_addresses = validator.find_similar_addresses(keyword, address_list, threshold)
        
        # 3. 결과 매핑
        matched_results = []
        for similar_addr, similarity in similar_addresses:
            # 원본 주소 데이터 찾기
            for addr in addresses:
                if addr["address"] == similar_addr:
                    matched_results.append({
                        **addr,
                        "similarity_score": similarity
                    })
                    break
        
        return {
            "status": "success",
            "keyword": keyword,
            "matches": matched_results,
            "total_matches": len(matched_results),
            "message": f"'{keyword}'로 {len(matched_results)}개의 유사 주소를 찾았습니다."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"주소 검색 중 오류 발생: {str(e)}"
        }


# =================
# 헬퍼 함수들
# =================

def _check_duplicate_address(address: str, threshold: float = 0.8) -> dict:
    """중복 주소 체크"""
    try:
        all_addresses_result = list_all_addresses(limit=200)
        if all_addresses_result.get("status") != "success":
            return {"has_duplicate": False}
        
        validator = AddressValidator()
        existing_addresses = [addr["address"] for addr in all_addresses_result.get("addresses", []) if addr.get("address")]
        
        similar_addresses = validator.find_similar_addresses(address, existing_addresses, threshold)
        
        if similar_addresses:
            best_match, similarity = similar_addresses[0]
            # 문서 ID 찾기
            for addr in all_addresses_result.get("addresses", []):
                if addr["address"] == best_match:
                    return {
                        "has_duplicate": True,
                        "similar_address": best_match,
                        "similarity": similarity,
                        "doc_id": addr["doc_id"]
                    }
        
        return {"has_duplicate": False}
        
    except Exception:
        return {"has_duplicate": False}


def _get_document_by_id(doc_id: str) -> dict:
    """문서 ID로 특정 문서 조회"""
    try:
        # addressesJson 컬렉션에서 모든 문서 조회 후 ID로 필터링
        result = query_any_collection("addressesJson", limit=500)
        if result.get("status") == "success":
            documents = result.get("raw_data", {}).get("data", {}).get("documents", [])
            
            for doc in documents:
                if doc.get("id") == doc_id:
                    doc_data = doc.get("data", {})
                    # dataJson 파싱
                    data_json_str = doc_data.get("dataJson", "{}")
                    try:
                        data_json = json.loads(data_json_str) if data_json_str else {}
                    except json.JSONDecodeError:
                        data_json = {}
                    
                    return {
                        "exists": True,
                        "data": {
                            **data_json,
                            "address": doc_data.get("description", "")  # 주소는 description에서
                        }
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
            documents = schedules_result.get("raw_data", {}).get("data", {}).get("documents", [])
            
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