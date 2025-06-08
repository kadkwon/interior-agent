from google.adk.agents import Agent
import json
from datetime import datetime

# 현장관리 에이전트 import
from .agent import register_site, get_site_info, list_all_sites

# Firebase 도구 함수들 import
from .tools import (
    query_schedule_collection,
    get_firebase_project_info,
    list_firestore_collections,
    query_any_collection,
    list_storage_files
)





# 2. 메인 인테리어 매니저 에이전트 (Root Agent)
root_agent = Agent(
    name="interior_manager",
    model="gemini-2.0-flash",
    description="인테리어 프로젝트의 현장관리와 Firebase 연동을 담당하는 매니저",
    instruction="""
    당신은 인테리어 프로젝트의 현장 관리와 Firebase 연동을 담당하는 전문 매니저입니다.
    
    주요 기능:
    1. 현장 관리: 현장 등록, 정보 조회, 목록 관리
    2. 🔥 Firebase 연동: 온라인 데이터베이스와 스토리지 관리
    
    Firebase 기능:
    - "schedule 컬렉션을 조회해서" → query_schedule_collection() 사용
    - "컬렉션 목록을 보여줘" → list_firestore_collections() 사용
    - "프로젝트 정보 확인해줘" → get_firebase_project_info() 사용
    - "파일 목록을 보여줘" → list_storage_files() 사용
    - 특정 컬렉션 조회 → query_any_collection(collection_name) 사용
    
    사용자가 Firebase 관련 요청을 하면:
    1. 적절한 Firebase 도구를 사용하여 온라인 데이터를 조회
    2. 결과를 읽기 쉽게 포맷팅하여 제공
    3. 추가적인 분석이나 작업이 필요한지 확인
    
    작업 절차:
    1. 현장 정보 등록 및 관리
    2. Firebase에서 관련 데이터를 조회하거나 저장
    
    각 단계에서 관련 도구를 사용하여 고객에게 진행 상황을 자세히 설명해주세요.
    """,
    tools=[
        # 현장 관리 도구
        register_site, 
        get_site_info, 
        list_all_sites,
        
        # 🔥 Firebase 연동 도구
        query_schedule_collection,
        get_firebase_project_info,
        list_firestore_collections,
        query_any_collection,
        list_storage_files
    ]
) 