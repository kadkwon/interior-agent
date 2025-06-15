"""
FastAPI 서버 클라이언트
- 일반 HTTP 요청
- Server-Sent Events (SSE) 스트리밍
- 세션 관리
- 에이전트 전환
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Generator, Callable
import requests
import sseclient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastAPIClient:
    """FastAPI 서버 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8505"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session_id: Optional[str] = None
        
        # 기본 헤더 설정
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"FastAPI 클라이언트 초기화: {self.base_url}")
    
    def health_check(self) -> Dict[str, Any]:
        """서버 상태 확인"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"헬스 체크 실패: {e}")
            return {"status": "error", "error": str(e)}
    
    def create_session(self, user_id: str = "user", app_name: str = "interior-agent") -> str:
        """새 세션 생성"""
        try:
            response = self.session.post(
                f"{self.base_url}/apps/{app_name}/users/{user_id}/sessions"
            )
            response.raise_for_status()
            data = response.json()
            self.session_id = data["session_id"]
            logger.info(f"새 세션 생성됨: {self.session_id}")
            return self.session_id
        except Exception as e:
            logger.error(f"세션 생성 실패: {e}")
            raise
    
    def send_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """일반 메시지 전송 (레거시 호환)"""
        try:
            payload = {
                "message": message,
                "session_id": session_id or self.session_id,
                "user_id": "user",
                "agent_id": "interior_manager"
            }
            
            response = self.session.post(
                f"{self.base_url}/agent/chat",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"오류가 발생했습니다: {str(e)}"
            }
    
    def send_message_sse(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        event_callback: Optional[Callable[[str, Dict], None]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """SSE 스트리밍으로 메시지 전송"""
        try:
            payload = {
                "message": message,
                "session_id": session_id or self.session_id,
                "user_id": "user",
                "agent_id": "interior_manager"
            }
            
            # SSE 요청
            response = self.session.post(
                f"{self.base_url}/run_sse",
                json=payload,
                stream=True,
                headers={
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache'
                }
            )
            response.raise_for_status()
            
            # SSE 클라이언트로 이벤트 스트림 처리
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                try:
                    if event.data:
                        event_data = json.loads(event.data)
                        
                        # 콜백 함수 호출
                        if event_callback:
                            event_callback(event.event, event_data)
                        
                        yield {
                            "event": event.event,
                            "data": event_data,
                            "timestamp": event_data.get("timestamp"),
                            "session_id": event_data.get("session_id")
                        }
                        
                        # 연결 종료 이벤트 처리
                        if event.event == "connection_close":
                            break
                            
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 파싱 오류: {e}, 데이터: {event.data}")
                    continue
                    
        except Exception as e:
            logger.error(f"SSE 스트리밍 실패: {e}")
            yield {
                "event": "error",
                "data": {
                    "message": f"스트리밍 오류: {str(e)}",
                    "error_type": "client_error"
                },
                "timestamp": time.time(),
                "session_id": session_id or self.session_id
            }
    
    def transfer_to_agent(
        self, 
        agent_name: str, 
        message: str, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """에이전트 전환"""
        try:
            payload = {
                "agent_name": agent_name,
                "message": message,
                "session_id": session_id or self.session_id
            }
            
            response = self.session.post(
                f"{self.base_url}/transfer_to_agent",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"에이전트 전환 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_session_info(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """세션 정보 조회"""
        try:
            sid = session_id or self.session_id
            if not sid:
                raise ValueError("세션 ID가 필요합니다")
            
            response = self.session.get(f"{self.base_url}/sessions/{sid}")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"세션 정보 조회 실패: {e}")
            return {"error": str(e)}
    
    def delete_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """세션 삭제"""
        try:
            sid = session_id or self.session_id
            if not sid:
                raise ValueError("세션 ID가 필요합니다")
            
            response = self.session.delete(f"{self.base_url}/sessions/{sid}")
            response.raise_for_status()
            
            # 현재 세션이 삭제된 경우 초기화
            if sid == self.session_id:
                self.session_id = None
            
            return response.json()
            
        except Exception as e:
            logger.error(f"세션 삭제 실패: {e}")
            return {"error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """서버 통계 조회"""
        try:
            response = self.session.get(f"{self.base_url}/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {"error": str(e)}
    
    def close(self):
        """클라이언트 종료"""
        if self.session:
            self.session.close()
        logger.info("FastAPI 클라이언트 종료")

# 편의 함수들
def create_client(base_url: str = "http://localhost:8505") -> FastAPIClient:
    """FastAPI 클라이언트 생성"""
    return FastAPIClient(base_url)

def quick_chat(message: str, base_url: str = "http://localhost:8505") -> str:
    """빠른 채팅 (일회성)"""
    client = FastAPIClient(base_url)
    try:
        result = client.send_message(message)
        return result.get("response", "응답을 받을 수 없습니다.")
    finally:
        client.close()

def test_connection(base_url: str = "http://localhost:8505") -> bool:
    """연결 테스트"""
    client = FastAPIClient(base_url)
    try:
        health = client.health_check()
        return health.get("status") == "healthy"
    except:
        return False
    finally:
        client.close()

# 메인 테스트
if __name__ == "__main__":
    print("🧪 FastAPI 클라이언트 테스트")
    print("=" * 50)
    
    # 연결 테스트
    print("1. 연결 테스트...")
    if test_connection():
        print("✅ 서버 연결 성공")
    else:
        print("❌ 서버 연결 실패")
        exit(1)
    
    # 클라이언트 생성
    client = create_client()
    
    try:
        # 헬스 체크
        print("\n2. 헬스 체크...")
        health = client.health_check()
        print(f"상태: {health.get('status')}")
        print(f"에이전트: {health.get('agent_available')}")
        
        # 세션 생성
        print("\n3. 세션 생성...")
        session_id = client.create_session()
        print(f"세션 ID: {session_id}")
        
        # 일반 메시지 테스트
        print("\n4. 일반 메시지 테스트...")
        result = client.send_message("안녕하세요")
        print(f"응답: {result.get('response', '')[:100]}...")
        
        # SSE 스트리밍 테스트
        print("\n5. SSE 스트리밍 테스트...")
        print("이벤트 스트림:")
        
        for event in client.send_message_sse("주소 리스트 보여줘"):
            print(f"  - {event['event']}: {event['data'].get('message', '')[:50]}...")
            if event['event'] == 'agent_complete':
                break
        
        # 통계 조회
        print("\n6. 서버 통계...")
        stats = client.get_stats()
        print(f"총 세션: {stats.get('total_sessions')}")
        print(f"에이전트 상태: {stats.get('agent_status')}")
        
    finally:
        client.close()
        print("\n✅ 테스트 완료") 