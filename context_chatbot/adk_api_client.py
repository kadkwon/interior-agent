"""
ADK API 서버와 통신하는 클라이언트
"""

import requests
import json
import logging
from typing import Dict, Any, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdkApiClient:
    """ADK API 서버와 통신하는 클라이언트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:8505"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """서버 상태 확인"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check 실패: {e}")
            return {"status": "error", "error": str(e)}
    
    def chat(self, message: str) -> Dict[str, Any]:
        """챗봇과 대화"""
        try:
            logger.info(f"🔄 API 요청: {message}")
            
            payload = {"message": message}
            response = self.session.post(
                f"{self.base_url}/agent/chat",
                json=payload,
                timeout=60
            )
            
            logger.info(f"📥 API 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"✅ 성공: {len(result.get('response', ''))} 문자")
                    return result
                else:
                    logger.error(f"❌ API 오류: {result.get('error')}")
                    return result
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ HTTP 오류: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "요청 시간 초과 (60초)"
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = "서버 연결 실패. ADK API 서버가 실행 중인지 확인하세요."
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"예상치 못한 오류: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

class AdkInteriorAgent:
    """ADK API를 통한 인테리어 에이전트"""
    
    def __init__(self):
        self.client = AdkApiClient()
        self.name = "interior_assistant"
        self.description = "ADK API를 통한 인테리어 프로젝트 전문 AI 어시스턴트"
        
        # 서버 상태 확인
        health = self.client.health_check()
        if health.get("status") == "healthy" and health.get("agent_available"):
            logger.info("✅ ADK API 서버 연결 성공")
            self.available = True
        else:
            logger.warning(f"⚠️ ADK API 서버 상태: {health}")
            self.available = False
    
    def check_connection(self) -> bool:
        """연결 상태 재확인"""
        health = self.client.health_check()
        if health.get("status") == "healthy" and health.get("agent_available"):
            self.available = True
            logger.info("✅ ADK API 서버 연결 재확인 성공")
            return True
        else:
            self.available = False
            logger.warning(f"⚠️ ADK API 서버 연결 재확인 실패: {health}")
            return False

    def generate(self, user_input: str) -> str:
        """사용자 입력에 대한 응답 생성"""
        # 연결 상태가 불안정하면 재확인
        if not self.available:
            logger.info("🔄 연결 상태 재확인 중...")
            self.check_connection()
        
        if not self.available:
            return "죄송합니다. 현재 ADK API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
        
        try:
            result = self.client.chat(user_input)
            
            if result.get("success"):
                return result.get("response", "응답을 받지 못했습니다.")
            else:
                error = result.get("error", "알 수 없는 오류")
                logger.error(f"ADK API 오류: {error}")
                return f"죄송합니다. 처리 중 오류가 발생했습니다: {error}"
                
        except Exception as e:
            logger.error(f"응답 생성 중 오류: {e}")
            return f"죄송합니다. 시스템 오류가 발생했습니다: {str(e)}"
    
    def is_interior_related(self, user_input: str) -> bool:
        """인테리어 관련 질문인지 판단 (ADK API에서 처리하므로 항상 True)"""
        return True

# 전역 인스턴스
adk_interior_agent = AdkInteriorAgent()

if __name__ == "__main__":
    # 테스트
    print("=== ADK API 클라이언트 테스트 ===")
    
    # 서버 상태 확인
    health = adk_interior_agent.client.health_check()
    print(f"서버 상태: {health}")
    
    if adk_interior_agent.available:
        # 테스트 메시지
        test_messages = [
            "안녕하세요!",
            "주소 리스트 보여줘",
            "새로운 인테리어 프로젝트를 시작하고 싶어요"
        ]
        
        for msg in test_messages:
            print(f"\n--- 테스트: {msg} ---")
            response = adk_interior_agent.generate(msg)
            print(f"응답: {response[:100]}...")
    else:
        print("❌ ADK API 서버를 사용할 수 없습니다.")
    
    print("\n=== 테스트 완료 ===") 