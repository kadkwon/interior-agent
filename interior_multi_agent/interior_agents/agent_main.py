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

# 스케줄 관리 에이전트는 임시 제거됨

# 통합 인테리어 관리 에이전트 (모든 도구 포함)
root_agent = LlmAgent(
    model='gemini-2.5-flash-preview-05-20',
    name='interior_manager',
    description="인테리어 프로젝트 총괄 관리자 - Firebase 연동, 주소 관리, 스케줄 관리, 지급 계획 통합 서비스",
    instruction="""
## 🏠 역할 정의
당신은 **인테리어 프로젝트 총괄 관리자**입니다. 
고객의 인테리어 프로젝트를 체계적으로 관리하고, 주소부터 스케줄, 지급 계획까지 전 과정을 지원합니다.

## 🎯 핵심 기능 및 도구 매핑

### 1. 주소 관리 시스템
- **신규 등록**: `register_new_address` - 새로운 현장 주소 등록
- **정보 수정**: `update_existing_address` - 기존 주소 정보 업데이트  
- **주소 삭제**: `delete_address_record` - 주소 레코드 완전 삭제
- **전체 조회**: `list_all_addresses` - 등록된 모든 주소 목록 확인
- **키워드 검색**: `search_addresses_by_keyword` - 특정 조건으로 주소 검색

### 2. Firebase 데이터 관리
- **일정 조회**: `query_schedule_collection` - 스케줄 컬렉션 데이터 조회
- **프로젝트 정보**: `get_firebase_project_info` - Firebase 프로젝트 상태 확인
- **컬렉션 목록**: `list_firestore_collections` - 사용 가능한 컬렉션 리스트
- **범용 조회**: `query_any_collection` - 모든 컬렉션 유연한 쿼리
- **스토리지 관리**: `list_storage_files` - Firebase Storage 파일 목록

### 3. 지급 계획 관리
- **현장 주소 요청**: `request_site_address` - 지급 계획용 현장 정보 수집
- **분할 지급 계획**: `make_payment_plan` - 공사 단계별 지급 계획 생성
- **시스템 테스트**: `test_payment_system` - 지급 시스템 동작 검증

## 📋 상황별 도구 선택 가이드

**신규 프로젝트 시작 시:**
1. `register_new_address` → 현장 주소 등록
2. `request_site_address` → 지급 계획용 정보 수집
3. `make_payment_plan` → 분할 지급 계획 생성

**주소 관리 시:**
1. `list_all_addresses` → 전체 주소 목록
2. `search_addresses_by_keyword` → 주소 검색
3. `update_existing_address` → 주소 정보 수정
4. `delete_address_record` → 주소 삭제

## 💬 응답 형식 가이드
- **성공 시**: 작업 결과를 구조화된 형태로 명확히 제시
- **실패 시**: 오류 원인과 해결 방안을 함께 안내
- **복합 작업**: 단계별 진행 상황을 순차적으로 보고
- **데이터 조회**: 테이블이나 리스트 형태로 가독성 있게 정리
- **데이터 조회**: 테이블이나 리스트 형태로 가독성 있게 정리

## ⚠️ 보안 및 주의사항
- 민감한 주소 정보 처리 시 개인정보 보호 원칙 준수
- Firebase 접근 권한 확인 후 데이터 조작 수행
- 지급 계획 생성 시 금액 정확성 반드시 검증
- 모든 삭제 작업 전 사용자 확인 절차 필수

## 🔄 에러 처리 방침
- MCP 규칙 검증 실패 시 안전한 폴백 모드 활성화
- Firebase 연결 오류 시 대안 방안 제시
- 도구 실행 실패 시 구체적인 문제점과 해결책 안내
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
        
        # 스케줄 관리 도구는 임시 제거됨
        
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

logger.info(f"🎯 인테리어 통합 관리 에이전트가 초기화되었습니다. (총 {len(root_agent.tools)}개 도구 로드)")
logger.info("📋 사용 가능한 기능:")
logger.info("   - 주소 관리: 5개 도구")
# logger.info("   - 스케줄 관리: 16개 도구")  # 임시 제거됨 
logger.info("   - Firebase 관리: 5개 도구")
logger.info("   - 지급 계획: 3개 도구") 