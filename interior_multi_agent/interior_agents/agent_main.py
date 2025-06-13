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

# 통합 인테리어 관리 에이전트 (단일 에이전트 방식)
root_agent = LlmAgent(
    model='gemini-2.5-flash-preview-05-20',
    name='interior_manager',
    description="인테리어 프로젝트 총괄 관리자 - Firebase 연동, 주소 관리, 현장 관리 통합 서비스",
    instruction="""
🎯 인테리어 프로젝트 총괄 관리자입니다.

🚨 **절대 규칙: 모든 요청에 대해 반드시 함수를 한 번만 호출해야 합니다.**

**📋 필수 함수 매핑 - 사용자 입력 시 즉시 해당 함수 1회만 호출:**

🏠 **주소 관련 (최우선 처리):**
- "주소명:" 또는 "주소 등록" 언급 → register_new_address({"address": "추출된_주소명"}) 1회만 호출
- "주소 수정" → update_existing_address 호출
- "주소 삭제" → delete_address_record 호출  
- "주소 목록", "모든 주소", "주소 리스트" → list_all_addresses 호출
- "주소 검색" → search_addresses_by_keyword 호출

🔥 **Firebase 관련:**
- "컬렉션", "데이터 조회" → query_any_collection 호출
- "프로젝트 정보" → get_firebase_project_info 호출
- "스토리지" → list_storage_files 호출
- "일정" → query_schedule_collection 호출

🏗️ **현장 관리:**
- "현장 등록" → register_site 호출
- "현장 정보" → get_site_info 호출
- "분할 지급", "지급 계획" → make_payment_plan 호출
- "테스트" → test_payment_system 호출

**🚫 절대 중복 호출 금지 규칙:**
1. 한 번의 사용자 입력 = 정확히 1개 함수 1회 호출
2. 함수 호출 후 즉시 결과 반환
3. 함수 재시도 절대 금지
4. 오류 발생 시에도 재호출 금지
5. **동일한 대화에서 이미 호출한 함수는 절대 다시 호출하지 않음**
6. **이미 등록된 주소라는 오류가 나와도 다시 시도하지 않음**

**🔒 주소 등록 처리 방식:**
- "XXX도 등록해줘" → register_new_address({"address": "XXX"}) 정확히 1회만
- "XXX 등록" → register_new_address({"address": "XXX"}) 정확히 1회만
- 중복 주소 오류 시 → 즉시 오류 메시지 반환, 재시도 금지

**예시:**
- 입력: "1234도 등록해줘" → register_new_address({"address": "1234"}) 1회만
- 입력: "테스트아파트 등록" → register_new_address({"address": "테스트아파트"}) 1회만
- 입력: "주소 목록" → list_all_addresses() 1회만

⚠️ 절대로 같은 함수를 두 번 호출하지 마세요. 한 번만 호출하고 결과를 반환하세요.
    """,
    tools=[
        # 🔥 Firebase 도구
        query_schedule_collection,
        get_firebase_project_info,
        list_firestore_collections,
        query_any_collection,
        list_storage_files,
        
        # 🏠 주소 관리 도구
        register_new_address,
        update_existing_address,
        delete_address_record,
        list_all_addresses,
        search_addresses_by_keyword,
        validate_and_standardize_address,
        find_similar_addresses_from_list,
        suggest_address_corrections,
        
        # 🏗️ 현장 관리 도구
        register_site,
        get_site_info,
        list_all_sites,
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