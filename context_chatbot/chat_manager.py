import json
import datetime
import sys
import os
import requests
from typing import List, Dict, Any

# 1순위: ADK API 클라이언트 시도
try:
    from adk_api_client import adk_interior_agent
    ADK_API_AVAILABLE = True
    print("✅ ADK API 클라이언트 연동 성공")
except ImportError as e:
    print(f"⚠️ ADK API 클라이언트 연동 실패: {e}")
    ADK_API_AVAILABLE = False
    adk_interior_agent = None

# 2순위: 실제 에이전트 연동 시도 (기존 real_agent_integration)
try:
    from real_agent_integration import real_interior_agent
    REAL_AGENT_AVAILABLE = True
    print("✅ 실제 Agent 연동 성공")
except ImportError as e:
    print(f"⚠️ 실제 Agent 연동 실패: {e}")
    REAL_AGENT_AVAILABLE = False
    real_interior_agent = None

# 3순위: 안정적인 fallback 에이전트 임포트
try:
    from fallback_agent import interior_agent
    FALLBACK_AGENT_AVAILABLE = True
    print("✅ Fallback Agent 로드 성공")
except ImportError as e:
    print(f"❌ Fallback Agent 임포트 실패: {e}")
    FALLBACK_AGENT_AVAILABLE = False
    interior_agent = None

class ChatManager:
    def __init__(self):
        self.conversation_history: List[Dict[str, Any]] = []
        self.context_summary = ""
        self.max_history_length = 20
    
        # 에이전트 우선순위에 따른 선택
        if ADK_API_AVAILABLE and adk_interior_agent and adk_interior_agent.available:
            self.agent = adk_interior_agent
            self.agent_type = "ADK_API"
            print("🚀 ADK API 에이전트 선택됨")
        elif REAL_AGENT_AVAILABLE and real_interior_agent:
            self.agent = real_interior_agent
            self.agent_type = "REAL_AGENT"
            print("🔧 실제 에이전트 선택됨")
        elif FALLBACK_AGENT_AVAILABLE and interior_agent:
            self.agent = interior_agent
            self.agent_type = "FALLBACK"
            print("🛡️ Fallback 에이전트 선택됨")
        else:
            self.agent = None
            self.agent_type = "NONE"
            print("❌ 사용 가능한 에이전트가 없습니다")
        
        # 에이전트 정보 출력
        if self.agent:
            print(f"✅ 에이전트 연결 성공: {self.agent_type}")
            print(f"   - 이름: {getattr(self.agent, 'name', 'Unknown')}")
            print(f"   - 설명: {getattr(self.agent, 'description', 'No description')}")
    
    def get_response(self, user_input: str) -> str:
        """사용자 입력에 대한 응답 생성"""
        if not self.agent:
            return "죄송합니다. 현재 시스템을 사용할 수 없습니다. 잠시 후 다시 시도해주세요."
        
        try:
            # 에이전트 타입에 따른 처리
            if self.agent_type == "ADK_API":
                response = self._get_adk_response(user_input)
            elif self.agent_type == "REAL_AGENT":
                response = self._get_real_agent_response(user_input)
            elif self.agent_type == "FALLBACK":
                response = self._get_fallback_response(user_input)
            else:
                response = "에이전트를 사용할 수 없습니다."
            
            # 대화 기록 추가
            self._add_to_history(user_input, response)
            
            return response
            
        except Exception as e:
            error_msg = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
            print(f"❌ ChatManager 오류: {error_msg}")
            
            # 에러 발생 시 fallback 시도
            if self.agent_type != "FALLBACK" and FALLBACK_AGENT_AVAILABLE:
                try:
                    print("🔄 Fallback 에이전트로 재시도...")
                    fallback_response = interior_agent.generate(user_input)
                    self._add_to_history(user_input, fallback_response)
                    return fallback_response
                except Exception as fallback_e:
                    print(f"❌ Fallback도 실패: {fallback_e}")
            
            return error_msg
    
    def _get_adk_response(self, user_input: str) -> str:
        """ADK API를 통한 응답"""
        try:
            response = adk_interior_agent.generate(user_input)
            print(f"✅ ADK API 응답 성공: {len(response)} 문자")
            return response
        except Exception as e:
            print(f"❌ ADK API 오류: {e}")
            raise e
    
    def _get_real_agent_response(self, user_input: str) -> str:
        """실제 에이전트를 통한 응답"""
        try:
            response = real_interior_agent.generate(user_input)
            print(f"✅ 실제 에이전트 응답 성공: {len(response)} 문자")
            return response
        except Exception as e:
            print(f"❌ 실제 에이전트 오류: {e}")
            raise e
    
    def _get_fallback_response(self, user_input: str) -> str:
        """Fallback 에이전트를 통한 응답"""
        try:
            is_interior_question = interior_agent.is_interior_related(user_input)
            response = interior_agent.generate(user_input)
            print(f"✅ Fallback 응답 성공: {len(response)} 문자, 인테리어관련: {is_interior_question}")
            return response
        except Exception as e:
            print(f"❌ Fallback 에이전트 오류: {e}")
            raise e
    
    def _add_to_history(self, user_input: str, response: str):
        """대화 기록에 추가"""
        try:
            self.conversation_history.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "user_input": user_input,
                "response": response,
                "agent_type": self.agent_type
            })
            
            # 최대 길이 초과 시 가장 오래된 기록 제거
            if len(self.conversation_history) > self.max_history_length:
                self.conversation_history.pop(0)
                
        except Exception as e:
            print(f"⚠️ 대화 기록 추가 실패: {e}")
    
    def get_conversation_context(self) -> str:
        """대화 맥락 요약 반환"""
        if not self.conversation_history:
            return "대화 기록이 없습니다."
        
        try:
            recent_conversations = self.conversation_history[-5:]  # 최근 5개 대화
            context_parts = []
            
            for conv in recent_conversations:
                context_parts.append(f"사용자: {conv['user_input'][:50]}...")
                context_parts.append(f"응답: {conv['response'][:50]}...")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            return f"대화 맥락 생성 중 오류: {str(e)}"
    
    def clear_history(self):
        """대화 기록 초기화"""
        self.conversation_history = []
        self.context_summary = ""
        print("✅ 대화 기록이 초기화되었습니다.")
    
    def check_adk_api_connection(self, test_chat=False) -> Dict[str, Any]:
        """ADK API 서버 연결 상태 실시간 확인"""
        try:
            # 1단계: Health Check
            response = requests.get("http://localhost:8505/health", timeout=3)
            if response.status_code != 200:
                return {
                    "connected": False,
                    "status": "error",
                    "agent_available": False,
                    "timestamp": "",
                    "error": f"HTTP {response.status_code}",
                    "chat_test": False
                }
            
            data = response.json()
            health_ok = data.get("agent_available", False)
            
            # 2단계: 실제 채팅 테스트 (옵션)
            chat_test_result = False
            chat_error = None
            
            if test_chat and health_ok:
                try:
                    chat_response = requests.post(
                        "http://localhost:8505/agent/chat",
                        json={"message": "연결 테스트"},
                        timeout=10
                    )
                    
                    if chat_response.status_code == 200:
                        chat_data = chat_response.json()
                        chat_test_result = chat_data.get("success", False)
                        if not chat_test_result:
                            chat_error = chat_data.get("error", "채팅 테스트 실패")
                    else:
                        chat_error = f"채팅 HTTP {chat_response.status_code}"
                        
                except Exception as e:
                    chat_error = f"채팅 테스트 오류: {str(e)}"
            
            # 최종 상태 결정
            if health_ok and (not test_chat or chat_test_result):
                return {
                    "connected": True,
                    "status": "healthy",
                    "agent_available": True,
                    "timestamp": data.get("timestamp", ""),
                    "error": None,
                    "chat_test": chat_test_result if test_chat else None,
                    "chat_error": chat_error
                }
            else:
                return {
                    "connected": True,
                    "status": "partial",  # 연결은 되지만 완전하지 않음
                    "agent_available": health_ok,
                    "timestamp": data.get("timestamp", ""),
                    "error": chat_error if test_chat else "에이전트 사용 불가",
                    "chat_test": chat_test_result if test_chat else None,
                    "chat_error": chat_error
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "connected": False,
                "status": "disconnected",
                "agent_available": False,
                "timestamp": "",
                "error": "서버에 연결할 수 없습니다",
                "chat_test": False
            }
        except requests.exceptions.Timeout:
            return {
                "connected": False,
                "status": "timeout",
                "agent_available": False,
                "timestamp": "",
                "error": "연결 시간 초과",
                "chat_test": False
            }
        except Exception as e:
            return {
                "connected": False,
                "status": "error",
                "agent_available": False,
                "timestamp": "",
                "error": str(e),
                "chat_test": False
            }

    def get_agent_status(self) -> Dict[str, Any]:
        """에이전트 상태 정보 반환 (실시간 ADK API 연결 상태 포함)"""
        # ADK API 서버 연결 상태 실시간 확인
        adk_connection = self.check_adk_api_connection()
        
        return {
            "agent_type": self.agent_type,
            "agent_available": self.agent is not None,
            "agent_name": getattr(self.agent, 'name', 'Unknown') if self.agent else None,
            "conversation_count": len(self.conversation_history),
            "adk_api_available": ADK_API_AVAILABLE,
            "adk_api_connected": adk_connection["connected"],
            "adk_api_status": adk_connection["status"],
            "adk_api_error": adk_connection["error"],
            "real_agent_available": REAL_AGENT_AVAILABLE,
            "fallback_available": FALLBACK_AGENT_AVAILABLE
        } 