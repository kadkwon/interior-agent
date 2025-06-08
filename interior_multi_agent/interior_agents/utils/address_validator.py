"""
주소 검증 및 표준화 유틸리티

주소 입력의 유효성 검사, 표준화, 유사 주소 검색, 오타 보정 등의 기능을 제공합니다.
"""

import re
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class AddressInfo:
    """주소 정보를 담는 데이터 클래스"""
    original: str
    standardized: str
    city: Optional[str] = None
    district: Optional[str] = None
    dong: Optional[str] = None
    building_number: Optional[str] = None
    unit_number: Optional[str] = None
    confidence_score: float = 0.0

class AddressValidator:
    """주소 검증 및 표준화를 위한 클래스"""
    
    def __init__(self):
        # 한국 주소 패턴 정의
        self.city_pattern = r'(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)'
        self.district_pattern = r'([가-힣]+구|[가-힣]+시|[가-힣]+군)'
        self.dong_pattern = r'([가-힣]+동|[가-힣]+읍|[가-힣]+면)'
        self.building_pattern = r'([0-9]+동)'
        self.unit_pattern = r'([0-9]+호)'
        
        # 아파트 단지명 패턴
        self.apartment_patterns = [
            r'아이파크',
            r'자이',
            r'래미안',
            r'푸르지오',
            r'더샵',
            r'e편한세상',
            r'힐스테이트',
            r'센트럴파크',
            r'디에이치',
            r'롯데캐슬'
        ]
        
        # 공통 오타 매핑
        self.typo_mapping = {
            '아이팍': '아이파크',
            '아이팍': '아이파크',
            '레미안': '래미안',
            '푸르지우': '푸르지오',
            '더샵': '더샵',
            '힐스테잇': '힐스테이트',
            '센트럴팍': '센트럴파크'
        }
    
    def extract_address_components(self, address: str) -> AddressInfo:
        """
        주소 문자열에서 구성 요소를 추출합니다.
        
        Args:
            address: 입력 주소 문자열
            
        Returns:
            AddressInfo: 추출된 주소 정보
        """
        # 공백 정규화
        normalized = re.sub(r'\s+', ' ', address.strip())
        
        # 오타 수정
        corrected = self._correct_typos(normalized)
        
        # 구성 요소 추출
        city = self._extract_city(corrected)
        district = self._extract_district(corrected)
        dong = self._extract_dong(corrected)
        building_number = self._extract_building_number(corrected)
        unit_number = self._extract_unit_number(corrected)
        
        # 표준화된 주소 생성
        standardized = self._standardize_address(
            city, district, dong, building_number, unit_number, corrected
        )
        
        # 신뢰도 점수 계산
        confidence = self._calculate_confidence_score(
            city, district, dong, building_number, unit_number
        )
        
        return AddressInfo(
            original=address,
            standardized=standardized,
            city=city,
            district=district,
            dong=dong,
            building_number=building_number,
            unit_number=unit_number,
            confidence_score=confidence
        )
    
    def _correct_typos(self, address: str) -> str:
        """오타를 수정합니다."""
        corrected = address
        for typo, correction in self.typo_mapping.items():
            corrected = corrected.replace(typo, correction)
        return corrected
    
    def _extract_city(self, address: str) -> Optional[str]:
        """시/도 정보를 추출합니다."""
        match = re.search(self.city_pattern, address)
        return match.group(1) if match else None
    
    def _extract_district(self, address: str) -> Optional[str]:
        """구/시/군 정보를 추출합니다."""
        match = re.search(self.district_pattern, address)
        return match.group(1) if match else None
    
    def _extract_dong(self, address: str) -> Optional[str]:
        """동/읍/면 정보를 추출합니다."""
        match = re.search(self.dong_pattern, address)
        return match.group(1) if match else None
    
    def _extract_building_number(self, address: str) -> Optional[str]:
        """건물 동 번호를 추출합니다."""
        match = re.search(self.building_pattern, address)
        return match.group(1) if match else None
    
    def _extract_unit_number(self, address: str) -> Optional[str]:
        """호수를 추출합니다."""
        match = re.search(self.unit_pattern, address)
        return match.group(1) if match else None
    
    def _standardize_address(self, city: Optional[str], district: Optional[str], 
                           dong: Optional[str], building_number: Optional[str], 
                           unit_number: Optional[str], original: str) -> str:
        """표준화된 주소 형식을 생성합니다."""
        components = []
        
        if city:
            components.append(city)
        if district:
            components.append(district)
        if dong:
            components.append(dong)
        
        # 아파트 단지명 추출
        apartment_name = self._extract_apartment_name(original)
        if apartment_name:
            components.append(apartment_name)
        
        if building_number:
            components.append(building_number)
        if unit_number:
            components.append(unit_number)
        
        return ' '.join(components) if components else original
    
    def _extract_apartment_name(self, address: str) -> Optional[str]:
        """아파트 단지명을 추출합니다."""
        for pattern in self.apartment_patterns:
            match = re.search(f'[가-힣]*{pattern}[가-힣0-9]*', address)
            if match:
                return match.group(0)
        return None
    
    def _calculate_confidence_score(self, city: Optional[str], district: Optional[str], 
                                  dong: Optional[str], building_number: Optional[str], 
                                  unit_number: Optional[str]) -> float:
        """주소 추출의 신뢰도 점수를 계산합니다."""
        score = 0.0
        total_weight = 5.0
        
        if city:
            score += 1.0
        if district:
            score += 1.5
        if dong:
            score += 1.0
        if building_number:
            score += 0.75
        if unit_number:
            score += 0.75
        
        return score / total_weight
    
    def find_similar_addresses(self, input_address: str, 
                             candidate_addresses: List[str], 
                             threshold: float = 0.6) -> List[Tuple[str, float]]:
        """
        유사한 주소를 찾습니다.
        
        Args:
            input_address: 입력 주소
            candidate_addresses: 후보 주소 목록
            threshold: 유사도 임계값 (0.0 ~ 1.0)
            
        Returns:
            List[Tuple[str, float]]: (주소, 유사도) 튜플의 리스트
        """
        similar_addresses = []
        
        for candidate in candidate_addresses:
            similarity = self._calculate_similarity(input_address, candidate)
            if similarity >= threshold:
                similar_addresses.append((candidate, similarity))
        
        # 유사도 순으로 정렬
        similar_addresses.sort(key=lambda x: x[1], reverse=True)
        return similar_addresses
    
    def _calculate_similarity(self, addr1: str, addr2: str) -> float:
        """두 주소 간의 유사도를 계산합니다."""
        # 각 주소의 구성 요소 추출
        info1 = self.extract_address_components(addr1)
        info2 = self.extract_address_components(addr2)
        
        # 구성 요소별 유사도 계산
        component_similarities = []
        
        # 시/도 비교
        if info1.city and info2.city:
            component_similarities.append(1.0 if info1.city == info2.city else 0.0)
        
        # 구/시/군 비교
        if info1.district and info2.district:
            component_similarities.append(1.0 if info1.district == info2.district else 0.0)
        
        # 동/읍/면 비교
        if info1.dong and info2.dong:
            component_similarities.append(1.0 if info1.dong == info2.dong else 0.0)
        
        # 전체 문자열 유사도도 고려
        string_similarity = SequenceMatcher(None, 
                                          info1.standardized.lower(), 
                                          info2.standardized.lower()).ratio()
        component_similarities.append(string_similarity)
        
        # 가중 평균 계산
        return sum(component_similarities) / len(component_similarities) if component_similarities else 0.0
    
    def validate_address_format(self, address: str) -> Dict[str, any]:
        """
        주소 형식의 유효성을 검사합니다.
        
        Args:
            address: 검사할 주소
            
        Returns:
            Dict: 검증 결과
        """
        info = self.extract_address_components(address)
        
        issues = []
        suggestions = []
        
        # 필수 구성 요소 체크
        if not info.city:
            issues.append("시/도 정보가 누락되었습니다")
            suggestions.append("시/도 정보를 추가해주세요 (예: 경기, 서울 등)")
        
        if not info.district:
            issues.append("구/시/군 정보가 누락되었습니다")
            suggestions.append("구/시/군 정보를 추가해주세요 (예: 수지구, 용인시 등)")
        
        if not info.dong:
            issues.append("동/읍/면 정보가 누락되었습니다")
            suggestions.append("동/읍/면 정보를 추가해주세요 (예: 풍덕천동 등)")
        
        # 신뢰도 평가
        if info.confidence_score < 0.5:
            issues.append("주소 형식의 신뢰도가 낮습니다")
            suggestions.append("주소를 더 구체적으로 입력해주세요")
        
        return {
            'is_valid': len(issues) == 0,
            'confidence_score': info.confidence_score,
            'extracted_info': info,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def suggest_corrections(self, address: str) -> List[str]:
        """
        주소 입력에 대한 수정 제안을 생성합니다.
        
        Args:
            address: 원본 주소
            
        Returns:
            List[str]: 수정 제안 목록
        """
        info = self.extract_address_components(address)
        suggestions = []
        
        # 표준화된 주소 제안
        if info.standardized != address:
            suggestions.append(f"표준화된 형식: {info.standardized}")
        
        # 누락된 정보에 대한 제안
        if info.confidence_score < 0.8:
            if not info.city:
                suggestions.append("시/도 정보를 추가하면 더 정확한 주소가 됩니다")
            if not info.district:
                suggestions.append("구/시/군 정보를 추가하면 더 정확한 주소가 됩니다")
            if not info.dong:
                suggestions.append("동/읍/면 정보를 추가하면 더 정확한 주소가 됩니다")
        
        return suggestions

def validate_address(address: str) -> Dict[str, any]:
    """
    주소 검증을 위한 편의 함수
    
    Args:
        address: 검증할 주소
        
    Returns:
        Dict: 검증 결과
    """
    validator = AddressValidator()
    return validator.validate_address_format(address)

def standardize_address(address: str) -> str:
    """
    주소 표준화를 위한 편의 함수
    
    Args:
        address: 표준화할 주소
        
    Returns:
        str: 표준화된 주소
    """
    validator = AddressValidator()
    info = validator.extract_address_components(address)
    return info.standardized 