from google.adk.agents.llm_agent import LlmAgent
import json
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firebase MCP 호출 규칙 import 추가
try:
    from .firebase_mcp_rules import (
        validate_mcp_call,
        execute_mcp_sequence,
        handle_mcp_error,
        safe_remove_data,
        validate_schedule_memo,
        validate_response,
        log_operation
    )
    MCP_RULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Firebase MCP 규칙 모듈 로드 실패: {e}")
    MCP_RULES_AVAILABLE = False
    
    # 폴백 함수들 정의
    def validate_mcp_call(*args, **kwargs): return True
    def execute_mcp_sequence(func, *args, **kwargs): 
        try:
            return True, func(*args, **kwargs)
        except Exception as e:
            return False, str(e)
    def handle_mcp_error(error, context=""): return str(error)
    def safe_remove_data(*args, **kwargs): return {"status": "removed"}
    def validate_schedule_memo(*args, **kwargs): return True
    def validate_response(response): return response is not None
    def log_operation(*args, **kwargs): pass

# 공사 분할 지급 계획 서비스 import
from .services import (
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

# 주소 관리 에이전트 import  
from .agent.address_management_agent import (
    register_new_address,
    update_existing_address,
    delete_address_record,
    list_all_addresses,
    search_addresses_by_keyword
)

# 통합 인테리어 관리 에이전트 (단일 에이전트 방식)
root_agent = LlmAgent(
    model='gemini-2.5-flash-preview-05-20',
    name='interior_manager',
    description="인테리어 프로젝트 총괄 관리자 - Firebase 연동, 주소 관리, 지급 계획 통합 서비스",
    instruction="""
인테리어 프로젝트 관리 시스템입니다.

주요 기능:
1. 주소 관리: 등록, 수정, 삭제, 조회, 검색
2. Firebase 데이터 관리: 컬렉션 조회, 프로젝트 정보, 스토리지 관리
3. 지급 계획 관리: 공사 분할 지급 계획 생성 및 관리

사용자 요청에 따라 적절한 함수를 호출하여 응답합니다.
    """,
    tools=[
        # Firebase 도구
        query_schedule_collection,
        get_firebase_project_info,
        list_firestore_collections,
        query_any_collection,
        list_storage_files,
        
        # 주소 관리 도구
        register_new_address,
        update_existing_address,
        delete_address_record,
        list_all_addresses,
        search_addresses_by_keyword,
        
        # 지급 계획 도구
        request_site_address,
        make_payment_plan,
        test_payment_system
    ]
)

# 모듈 로드 상태 로깅
if MCP_RULES_AVAILABLE:
    logger.info("✅ Firebase MCP 규칙 모듈이 성공적으로 로드되었습니다.")
else:
    logger.warning("⚠️ Firebase MCP 규칙 모듈을 사용할 수 없어 폴백 함수를 사용합니다.")

logger.info("🎯 인테리어 통합 관리 에이전트가 초기화되었습니다.") 