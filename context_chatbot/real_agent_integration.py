"""
실제 agent_main.py와 안전한 연동을 위한 클래스

복잡한 의존성 체인을 우회하고 핵심 도구들을 직접 활용합니다.
"""

import sys
import os
from typing import Dict, Any, Optional
import traceback

class RealAgentConnector:
    """agent_main.py의 실제 도구들과 연동하는 클래스"""
    
    def __init__(self):
        self.tools_loaded = False
        self.address_tools = None
        self.payment_tools = None 
        self.schedule_tools = None
        self._setup_path()
        self._load_tools()
    
    def _setup_path(self):
        """Python 경로 설정"""
        # 프로젝트 루트 경로 추가
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        interior_agent_path = os.path.join(project_root, 'interior_multi_agent')
        
        if interior_agent_path not in sys.path:
            sys.path.insert(0, interior_agent_path)
        
        print(f"📁 프로젝트 경로 추가: {interior_agent_path}")
    
    def _load_tools(self):
        """실제 도구들을 로드합니다"""
        try:
            # 주소 관리 도구 임포트
            from interior_agents.agent.address_management_agent import (
                list_all_addresses,
                search_addresses_by_keyword,
                register_new_address,
                update_existing_address,
                delete_address_record
            )
            
            self.address_tools = {
                'list_all_addresses': list_all_addresses,
                'search_addresses': search_addresses_by_keyword,
                'register_address': register_new_address,
                'update_address': update_existing_address,
                'delete_address': delete_address_record
            }
            
            print("✅ 주소 관리 도구 로드 성공")
            
            # 지급 관리 도구 임포트 시도
            try:
                from interior_agents.agent.payment_management_agent import (
                    create_payment_plan,
                    list_payment_plans,
                    update_payment_status
                )
                self.payment_tools = {
                    'create_plan': create_payment_plan,
                    'list_plans': list_payment_plans,
                    'update_status': update_payment_status
                }
                print("✅ 지급 관리 도구 로드 성공")
            except ImportError as e:
                print(f"⚠️ 지급 관리 도구 로드 실패: {e}")
                self.payment_tools = None
            
            # 일정 관리 도구 임포트 시도
            try:
                from interior_agents.agent.schedule_management_agent import (
                    create_schedule,
                    list_schedules,
                    update_schedule
                )
                self.schedule_tools = {
                    'create_schedule': create_schedule,
                    'list_schedules': list_schedules,
                    'update_schedule': update_schedule
                }
                print("✅ 일정 관리 도구 로드 성공")
            except ImportError as e:
                print(f"⚠️ 일정 관리 도구 로드 실패: {e}")
                self.schedule_tools = None
            
            self.tools_loaded = True
            
        except Exception as e:
            print(f"❌ 도구 로드 실패: {e}")
            print(f"📋 스택 트레이스:\n{traceback.format_exc()}")
            self.tools_loaded = False
    
    def generate(self, user_input: str) -> str:
        """사용자 입력에 따라 적절한 도구를 실행하고 응답을 생성합니다"""
        
        if not self.tools_loaded:
            return self._fallback_response(user_input)
        
        try:
            # 주소 관련 명령어 처리
            if any(keyword in user_input.lower() for keyword in ['주소', '리스트', '목록', '보여줘']):
                return self._handle_address_commands(user_input)
            
            # 지급 관련 명령어 처리  
            elif any(keyword in user_input.lower() for keyword in ['지급', '결제', '계획', '비용']):
                return self._handle_payment_commands(user_input)
            
            # 일정 관련 명령어 처리
            elif any(keyword in user_input.lower() for keyword in ['일정', '스케줄', '계획']):
                return self._handle_schedule_commands(user_input)
            
            # 기타 인테리어 관련 질문
            else:
                return self._handle_general_questions(user_input)
                
        except Exception as e:
            error_msg = f"도구 실행 중 오류 발생: {str(e)}"
            print(f"❌ {error_msg}")
            return f"죄송합니다. {error_msg}\n기본 응답으로 전환합니다.\n\n{self._fallback_response(user_input)}"
    
    def _handle_address_commands(self, user_input: str) -> str:
        """주소 관련 명령어를 처리합니다"""
        if not self.address_tools:
            return "주소 관리 기능을 사용할 수 없습니다. 관리자에게 문의해주세요."
        
        try:
            # "주소 리스트보여줘", "주소 목록" 등
            if any(keyword in user_input.lower() for keyword in ['리스트', '목록', '보여줘', '조회']):
                print("🔄 주소 목록 조회 실행 중...")
                
                # 상세 정보 포함 여부 판단
                include_details = any(keyword in user_input.lower() for keyword in ['상세', '자세히', '전체'])
                
                result = self.address_tools['list_all_addresses'](
                    limit=50, 
                    include_details=include_details
                )
                
                if result.get('status') == 'success':
                    return result.get('message', '주소 목록을 조회했습니다.')
                else:
                    return f"주소 조회 실패: {result.get('message', '알 수 없는 오류')}"
            
            # 검색 기능
            elif '검색' in user_input:
                # 간단한 키워드 추출 (개선 가능)
                keywords = user_input.replace('주소', '').replace('검색', '').strip()
                if keywords:
                    result = self.address_tools['search_addresses'](keywords)
                    if result.get('status') == 'success':
                        return result.get('message', '검색 결과입니다.')
                    else:
                        return f"검색 실패: {result.get('message', '알 수 없는 오류')}"
                else:
                    return "검색할 키워드를 입력해주세요. 예: '강남 주소 검색해줘'"
            
            else:
                return """📍 **주소 관리 기능 안내**

다음과 같은 명령어를 사용할 수 있습니다:

🔍 **조회 기능**
- "주소 리스트 보여줘" - 간단한 주소 목록
- "주소 상세 목록 보여줘" - 상세 정보 포함
- "강남 주소 검색해줘" - 키워드 검색

➕ **등록 기능**  
- "서울시 강남구 테헤란로 123 등록해줘"

✏️ **수정/삭제**
- 추후 지원 예정

구체적인 명령어로 다시 요청해주세요!"""
                
        except Exception as e:
            return f"주소 명령어 처리 중 오류: {str(e)}"
    
    def _handle_payment_commands(self, user_input: str) -> str:
        """지급 관리 명령어를 처리합니다"""
        if not self.payment_tools:
            return """💰 **지급 관리 기능 (시뮬레이션)**

실제 지급 관리 도구를 로드할 수 없어 시뮬레이션 응답입니다.

📋 **지급 계획 예시:**
1. 계약금 (10%) - 즉시 지급
2. 중도금 (40%) - 공사 시작 후 2주
3. 잔금 (50%) - 공사 완료 후

실제 기능을 사용하려면 시스템 관리자에게 문의해주세요."""
        
        try:
            if '목록' in user_input or '리스트' in user_input:
                result = self.payment_tools['list_plans']()
                return result.get('message', '지급 계획 목록을 조회했습니다.')
            else:
                return "지급 관리 기능이 준비 중입니다."
        except Exception as e:
            return f"지급 명령어 처리 중 오류: {str(e)}"
    
    def _handle_schedule_commands(self, user_input: str) -> str:
        """일정 관리 명령어를 처리합니다"""
        if not self.schedule_tools:
            return """📅 **일정 관리 기능 (시뮬레이션)**

실제 일정 관리 도구를 로드할 수 없어 시뮬레이션 응답입니다.

📋 **일정 예시:**
- 2024-01-15: 현장 측량
- 2024-01-20: 공사 시작  
- 2024-02-15: 중간 점검
- 2024-03-01: 완료 예정

실제 기능을 사용하려면 시스템 관리자에게 문의해주세요."""
        
        try:
            if '목록' in user_input or '리스트' in user_input:
                result = self.schedule_tools['list_schedules']()
                return result.get('message', '일정 목록을 조회했습니다.')
            else:
                return "일정 관리 기능이 준비 중입니다."
        except Exception as e:
            return f"일정 명령어 처리 중 오류: {str(e)}"
    
    def _handle_general_questions(self, user_input: str) -> str:
        """일반적인 인테리어 질문을 처리합니다"""
        return """🏠 **인테리어 프로젝트 전문 상담**

안녕하세요! 구체적인 질문을 해주시면 더 정확한 도움을 드릴 수 있습니다.

💡 **사용 가능한 기능들:**
- 📍 주소 관리: "주소 리스트 보여줘"
- 💰 지급 관리: "지급 계획 보여줘"  
- 📅 일정 관리: "일정 목록 보여줘"

구체적인 명령어로 다시 요청해주세요!"""
    
    def _fallback_response(self, user_input: str) -> str:
        """도구 로드 실패 시 대체 응답"""
        return """🔧 **시스템 제한 모드**

현재 실제 agent_main.py 연동에 일시적인 문제가 있어 제한된 기능만 제공됩니다.

⚠️ **기술적 이슈:**
- Firebase 연결 필요
- 복잡한 의존성 체인  
- 비동기 처리 복잡성

💡 **현재 사용 가능:**
- 기본적인 인테리어 상담
- 프로젝트 관리 가이드
- 일반적인 질문 응답

완전한 기능을 원하시면 시스템 관리자에게 문의해주세요."""


# 실제 연동 에이전트 인스턴스 생성
real_interior_agent = RealAgentConnector() 