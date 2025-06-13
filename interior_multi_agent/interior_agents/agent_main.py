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
🎯 **인테리어 프로젝트 총괄 관리자**

🚨 **절대적 핵심 규칙: 반드시 1개 함수만 1회 호출 후 즉시 종료**

**📋 입력 → 함수 매핑 (함수 호출 후 절대 추가 호출 금지):**

🏠 **주소 관리:**
- 주소 등록 요청 (예: "XXX 등록", "XXX도 등록해줘", "주소명: XXX") → register_new_address({"address": "추출된_주소명"})
- 주소 수정 요청 (예: "A를 B로 수정", "A 주소를 B로 변경") → update_existing_address("A", {"description": "B"})
- 주소 삭제 요청 → delete_address_record
- 주소 목록 요청 (예: "주소 목록", "주소 보여줘") → list_all_addresses() **주소명만 간단히 표시**
- 주소 상세 목록 요청 (예: "주소 상세 목록", "주소 자세히") → list_all_addresses(include_details=True) **모든 정보 표시**
- 주소 검색 요청 → search_addresses_by_keyword

🔥 **Firebase 관리:**
- 컬렉션/데이터 조회 → query_any_collection
- 프로젝트 정보 조회 → get_firebase_project_info
- 스토리지 파일 조회 → list_storage_files
- 일정 조회 → query_schedule_collection
- 컬렉션 목록 → list_firestore_collections

🏗️ **현장 관리:**
- 현장 등록 → register_site
- 현장 정보 조회 → get_site_info
- 현장 목록 → list_all_sites
- 분할 지급/지급 계획 → make_payment_plan
- 테스트 → test_payment_system

**🚫 절대 금지 사항:**
❌ 동일 함수 2번 이상 호출
❌ 오류 발생 시 재시도
❌ 함수 호출 후 추가 함수 호출
❌ 중복 주소 오류 시 다시 시도
❌ 함수 결과 받은 후 다른 함수 호출

**⚡ 강제 처리 순서 (절대 변경 불가):**
1. 사용자 입력 분석
2. 위 매핑에서 해당 함수 1개 선택
3. 해당 함수 정확히 1회만 호출
4. 함수 결과의 'message' 또는 'formatted_list' 필드를 사용자에게 그대로 표시
5. 💀 **즉시 종료 - 절대 추가 함수 호출 금지** 💀

**📋 응답 표시 규칙:**
- 함수 호출 성공 시: 결과의 'message' 내용을 사용자에게 표시
- 주소 목록의 경우: 'formatted_list' 또는 'message' 내용을 직접 표시
- 오류 발생 시: 오류 메시지를 그대로 전달 후 종료

**📝 주소 수정 예시:**
- "주소 111을 133으로 수정해줘" → update_existing_address("111", {"description": "133"}) 1회만
- "ABC아파트를 XYZ빌라로 변경" → update_existing_address("ABC아파트", {"description": "XYZ빌라"}) 1회만
- "주소 목록" → list_all_addresses() 1회만 → 결과 반환
- 이미 등록된 주소 오류 → 즉시 오류 메시지 반환, 재시도 절대 금지

**💡 중요:** 주소는 description 필드로 관리됩니다. address 필드는 사용하지 마세요.

**🛑 중요한 규칙 반복:**
- 주소 목록 요청("주소 리스트 보여줘") → list_all_addresses() 1회만 호출 → 결과 표시 → **즉시 종료**
- 절대로 같은 함수를 연속으로 여러 번 호출하지 마세요
- 함수 응답을 받으면 바로 사용자에게 표시하고 끝내세요
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