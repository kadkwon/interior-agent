"""
주소 검증 및 표준화 도구

root_agent가 사용할 수 있는 주소 검증 함수들을 제공합니다.
"""

from .address_validator import AddressValidator, validate_address, standardize_address
from typing import Dict, List

def validate_and_standardize_address(address: str) -> Dict[str, any]:
    """
    주소를 검증하고 표준화합니다.
    
    Args:
        address: 검증할 주소
        
    Returns:
        Dict: 검증 결과와 표준화된 주소
    """
    validator = AddressValidator()
    validation_result = validator.validate_address_format(address)
    address_info = validator.extract_address_components(address)
    
    result = {
        "original_address": address,
        "standardized_address": address_info.standardized,
        "is_valid": validation_result["is_valid"],
        "confidence_score": validation_result["confidence_score"],
        "extracted_components": {
            "city": address_info.city,
            "district": address_info.district,
            "dong": address_info.dong,
            "building_number": address_info.building_number,
            "unit_number": address_info.unit_number
        },
        "issues": validation_result["issues"],
        "suggestions": validation_result["suggestions"]
    }
    
    return result

def find_similar_addresses_from_list(input_address: str, address_list: List[str], threshold: float = 0.6) -> Dict[str, any]:
    """
    주소 목록에서 유사한 주소를 찾습니다.
    
    Args:
        input_address: 입력 주소
        address_list: 후보 주소 목록
        threshold: 유사도 임계값
        
    Returns:
        Dict: 유사 주소 검색 결과
    """
    validator = AddressValidator()
    similar_addresses = validator.find_similar_addresses(input_address, address_list, threshold)
    
    return {
        "input_address": input_address,
        "similar_addresses": [
            {"address": addr, "similarity_score": score} 
            for addr, score in similar_addresses
        ],
        "best_match": similar_addresses[0] if similar_addresses else None,
        "total_found": len(similar_addresses)
    }

def suggest_address_corrections(address: str) -> Dict[str, any]:
    """
    주소 입력에 대한 수정 제안을 생성합니다.
    
    Args:
        address: 원본 주소
        
    Returns:
        Dict: 수정 제안 결과
    """
    validator = AddressValidator()
    suggestions = validator.suggest_corrections(address)
    validation_result = validator.validate_address_format(address)
    
    return {
        "original_address": address,
        "suggestions": suggestions,
        "issues": validation_result["issues"],
        "confidence_score": validation_result["confidence_score"]
    } 