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




# 2. 메인 인테리어 매니저 에이전트 (Root Agent)
root_agent = Agent(
    name="interior_manager",
    model="gemini-2.0-flash",
    description="인테리어 프로젝트의 현장관리, Firebase 연동, 공사 분할 지급 계획을 담당하는 매니저",
    instruction="""
You are an interior project manager specialized in construction payment planning.

CRITICAL RULE: When user mentions "분할 지급", "지급 계획", "분할 계획", or "막대금", immediately call make_payment_plan function!

For requests with address: make_payment_plan(address)
For requests without address: request_site_address()

Always use functions instead of general conversation.

Available functions:
- Site management: register_site, get_site_info, list_all_sites
- Payment planning: make_payment_plan, request_site_address  
- Firebase: query_any_collection, list_firestore_collections
- Address validation: validate_and_standardize_address
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
        suggest_address_corrections
    ]
) 