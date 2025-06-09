from google.adk.agents import Agent
import json
from datetime import datetime

# 현장관리 및 공사 분할 지급 계획 서비스 import
from .services import (
    register_site, 
    get_site_info, 
    list_all_sites,
    request_site_address,
    make_payment_plan,
    test_payment_system
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

# 주소 관리 에이전트 import  
from .agent.address_management_agent import (
    register_new_address,
    update_existing_address,
    delete_address_record,
    list_all_addresses,
    search_addresses_by_keyword
)




# 2. 메인 인테리어 매니저 에이전트 (Root Agent)
root_agent = Agent(
    name="interior_manager",
    model="gemini-2.5-flash-preview-05-20",
    description="인테리어 프로젝트의 현장관리, Firebase 연동, 공사 분할 지급 계획을 담당하는 매니저",
    instruction="""
You are an interior project manager with access to various tools and databases.

ALWAYS USE FUNCTIONS to handle user requests. Never give general text responses.

Function calling rules:
1. Payment planning: "분할 지급", "지급 계획", "분할 계획", "막대금" → make_payment_plan(address)
2. Firebase queries: "컬렉션", "주소 나열", "데이터 조회" → query_any_collection(collection, limit)
3. Site management: "현장 등록", "현장 정보" → register_site, get_site_info, list_all_sites
4. Address validation: "주소 검증", "주소 표준화" → validate_and_standardize_address
5. Testing: "시스템 테스트", "테스트" → test_payment_system()
6. Address CRUD: 
   - "주소 등록", "새 주소 추가" → register_new_address(address_data)
   - "주소 수정", "주소 업데이트" → update_existing_address(doc_id, update_data)  
   - "주소 삭제", "주소 제거" → delete_address_record(doc_id, force)
   - "주소 목록", "모든 주소", "주소 리스트" → list_all_addresses(limit, include_details)
   - "주소 검색", "주소 찾기" → search_addresses_by_keyword(keyword, threshold)

For addressesJson collection listing: query_any_collection("addressesJson", 50)
For schedules collection listing: query_any_collection("schedules", 50)

Always call appropriate functions immediately based on user request type.
    """,
    tools=[
        # 현장 관리 도구
        register_site, 
        get_site_info, 
        list_all_sites,
        
        # 공사 분할 지급 계획 도구
        request_site_address,
        make_payment_plan,
        test_payment_system,
        
        # 🔥 Firebase 연동 도구
        query_schedule_collection,
        get_firebase_project_info,
        list_firestore_collections,
        query_any_collection,
        list_storage_files,
        
        # 📍 주소 검증 및 표준화 도구
        validate_and_standardize_address,
        find_similar_addresses_from_list,
        suggest_address_corrections,
        
        # 🏠 주소 관리 CRUD 도구
        register_new_address,
        update_existing_address,
        delete_address_record,
        list_all_addresses,
        search_addresses_by_keyword
    ]
) 