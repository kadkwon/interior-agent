from google.adk.agents import Agent
import json
from datetime import datetime

# 현장관리 및 공사 분할 지급 계획 서비스 import
from .services import (
    register_site, 
    get_site_info, 
    list_all_sites,
    request_site_address,
    create_construction_payment_plan
)

# Firebase 도구 함수들 import
from .tools import (
    query_schedule_collection,
    get_firebase_project_info,
    list_firestore_collections,
    query_any_collection,
    list_storage_files
)

# 주소 검증 도구 import
from .utils import (
    validate_and_standardize_address,
    find_similar_addresses_from_list,
    suggest_address_corrections
)




# 2. 메인 인테리어 매니저 에이전트 (Root Agent)
root_agent = Agent(
    name="interior_manager",
    model="gemini-2.0-flash",
    description="인테리어 프로젝트의 현장관리, Firebase 연동, 공사 분할 지급 계획을 담당하는 매니저",
    instruction="""
    당신은 인테리어 프로젝트 전문 매니저입니다.

    🎯 최우선 처리: 분할 지급 계획 요청 감지 시 즉시 실행

    【분할 지급 계획 요청 패턴】
    다음 중 하나라도 포함된 요청이 오면 즉시 처리:
    - "분할 지급", "공사 분할", "막대금", "지급 계획", "분할 계산"
    - "[주소] + 분할 지급 계획" 형태

    【실행 규칙】
    1. 주소가 포함된 분할 지급 계획 요청:
       → 즉시 create_construction_payment_plan(주소, query_any_collection) 호출
       → 예: "월배아이파크 1차 109동 2401호 분할 지급 계획을 만들어줘"

    2. 주소가 없는 분할 지급 계획 요청:
       → 즉시 request_site_address() 호출

    3. 그 외 요청:
       - Firebase 조회: query_any_collection() 등 사용
       - 현장 관리: register_site(), get_site_info() 등 사용
       - 주소 검증: validate_and_standardize_address() 등 사용

    ⚡ 핵심 규칙:
    - "분할 지급 계획" 관련 요청은 다른 설명 없이 즉시 해당 함수 실행
    - 주소 추출 후 바로 create_construction_payment_plan() 호출
    - 실패 시에만 설명 제공

    🏗️ 분할 지급 특징:
    - 막대금 300만원 별도 처리
    - 1000만원 단위 균등 분할
    - addresses + schedules 컬렉션 자동 조회
    - 표 형식으로 결과 출력

    📍 주소 검증 기능:
    - 잘못된 주소 입력 시 자동 표준화 및 오타 보정
    - 유사한 주소 검색으로 정확한 매칭 지원
    - 주소 구성 요소 추출 (시/도, 구/군, 동, 건물, 호수)
    - 신뢰도 점수로 주소 품질 평가
    """,
    tools=[
        # 현장 관리 도구
        register_site, 
        get_site_info, 
        list_all_sites,
        
        # 공사 분할 지급 계획 도구
        request_site_address,
        create_construction_payment_plan,
        
        # 🔥 Firebase 연동 도구
        query_schedule_collection,
        get_firebase_project_info,
        list_firestore_collections,
        query_any_collection,
        list_storage_files,
        
        # 📍 주소 검증 및 표준화 도구
        validate_and_standardize_address,
        find_similar_addresses_from_list,
        suggest_address_corrections
    ]
) 