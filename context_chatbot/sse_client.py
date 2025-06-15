"""
Server-Sent Events (SSE) 전용 클라이언트
- 실시간 스트리밍 특화
- 이벤트 핸들러 시스템
- 자동 재연결
- 상태 관리
"""

import json
import logging
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import requests
import sseclient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    """연결 상태"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

@dataclass
class SSEEvent:
    """SSE 이벤트 데이터"""
    event: str
    data: Dict[str, Any]
    timestamp: str
    session_id: str
    raw_data: str

class SSEEventHandler:
    """SSE 이벤트 핸들러"""
    
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
    
    def on(self, event_type: str, handler: Callable[[SSEEvent], None]):
        """이벤트 핸들러 등록"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def emit(self, event: SSEEvent):
        """이벤트 발생"""
        # 특정 이벤트 핸들러 실행
        if event.event in self.handlers:
            for handler in self.handlers[event.event]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"이벤트 핸들러 오류 ({event.event}): {e}")
        
        # 전체 이벤트 핸들러 실행
        if "*" in self.handlers:
            for handler in self.handlers["*"]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"전체 이벤트 핸들러 오류: {e}")

class SSEClient:
    """Server-Sent Events 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8505"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session_id: Optional[str] = None
        self.state = ConnectionState.DISCONNECTED
        
        # 이벤트 핸들러
        self.event_handler = SSEEventHandler()
        
        # 연결 설정
        self.auto_reconnect = True
        self.reconnect_delay = 5  # 초
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
        
        # 스레드 관리
        self.connection_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 통계
        self.stats = {
            "events_received": 0,
            "connection_time": None,
            "last_event_time": None,
            "errors": 0
        }
        
        logger.info(f"SSE 클라이언트 초기화: {self.base_url}")
    
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
    
    def connect_stream(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        blocking: bool = False
    ):
        """스트림 연결 시작"""
        if self.state in [ConnectionState.CONNECTED, ConnectionState.CONNECTING]:
            logger.warning("이미 연결되어 있거나 연결 중입니다")
            return
        
        self.state = ConnectionState.CONNECTING
        self.stop_event.clear()
        
        # 세션 ID 설정
        if session_id:
            self.session_id = session_id
        elif not self.session_id:
            self.create_session()
        
        # 연결 스레드 시작
        self.connection_thread = threading.Thread(
            target=self._stream_worker,
            args=(message,),
            daemon=True
        )
        self.connection_thread.start()
        
        if blocking:
            self.connection_thread.join()
    
    def _stream_worker(self, message: str):
        """스트림 워커 (별도 스레드에서 실행)"""
        while not self.stop_event.is_set():
            try:
                self._establish_stream(message)
                
                # 자동 재연결이 비활성화되어 있으면 종료
                if not self.auto_reconnect:
                    break
                
                # 재연결 대기
                if not self.stop_event.wait(self.reconnect_delay):
                    self.reconnect_attempts += 1
                    if self.reconnect_attempts >= self.max_reconnect_attempts:
                        logger.error("최대 재연결 시도 횟수 초과")
                        break
                    
                    logger.info(f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts}")
                    self.state = ConnectionState.RECONNECTING
                
            except Exception as e:
                logger.error(f"스트림 워커 오류: {e}")
                self.stats["errors"] += 1
                self.state = ConnectionState.ERROR
                
                if not self.auto_reconnect:
                    break
        
        self.state = ConnectionState.DISCONNECTED
    
    def _establish_stream(self, message: str):
        """실제 스트림 연결 수행"""
        payload = {
            "message": message,
            "session_id": self.session_id,
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
        
        self.state = ConnectionState.CONNECTED
        self.stats["connection_time"] = time.time()
        self.reconnect_attempts = 0
        
        logger.info("SSE 스트림 연결됨")
        
        # SSE 클라이언트로 이벤트 스트림 처리
        client = sseclient.SSEClient(response)
        
        for event in client.events():
            if self.stop_event.is_set():
                break
            
            try:
                if event.data:
                    event_data = json.loads(event.data)
                    
                    # SSE 이벤트 객체 생성
                    sse_event = SSEEvent(
                        event=event.event or "message",
                        data=event_data,
                        timestamp=event_data.get("timestamp", time.time()),
                        session_id=event_data.get("session_id", self.session_id),
                        raw_data=event.data
                    )
                    
                    # 통계 업데이트
                    self.stats["events_received"] += 1
                    self.stats["last_event_time"] = time.time()
                    
                    # 이벤트 핸들러 실행
                    self.event_handler.emit(sse_event)
                    
                    # 연결 종료 이벤트 처리
                    if event.event == "connection_close":
                        logger.info("서버에서 연결 종료 요청")
                        break
                        
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 파싱 오류: {e}, 데이터: {event.data}")
                continue
            except Exception as e:
                logger.error(f"이벤트 처리 오류: {e}")
                self.stats["errors"] += 1
    
    def disconnect(self):
        """연결 종료"""
        logger.info("SSE 연결 종료 중...")
        self.stop_event.set()
        
        if self.connection_thread and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=5)
        
        self.state = ConnectionState.DISCONNECTED
        logger.info("SSE 연결 종료됨")
    
    def on_event(self, event_type: str, handler: Callable[[SSEEvent], None]):
        """이벤트 핸들러 등록"""
        self.event_handler.on(event_type, handler)
    
    def on_agent_start(self, handler: Callable[[SSEEvent], None]):
        """에이전트 시작 이벤트 핸들러"""
        self.on_event("agent_start", handler)
    
    def on_tool_start(self, handler: Callable[[SSEEvent], None]):
        """도구 시작 이벤트 핸들러"""
        self.on_event("tool_start", handler)
    
    def on_response_chunk(self, handler: Callable[[SSEEvent], None]):
        """응답 청크 이벤트 핸들러"""
        self.on_event("response_chunk", handler)
    
    def on_agent_complete(self, handler: Callable[[SSEEvent], None]):
        """에이전트 완료 이벤트 핸들러"""
        self.on_event("agent_complete", handler)
    
    def on_error(self, handler: Callable[[SSEEvent], None]):
        """오류 이벤트 핸들러"""
        self.on_event("error", handler)
    
    def on_any_event(self, handler: Callable[[SSEEvent], None]):
        """모든 이벤트 핸들러"""
        self.on_event("*", handler)
    
    def get_state(self) -> ConnectionState:
        """현재 연결 상태"""
        return self.state
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보"""
        return {
            **self.stats,
            "state": self.state.value,
            "session_id": self.session_id,
            "auto_reconnect": self.auto_reconnect,
            "reconnect_attempts": self.reconnect_attempts
        }
    
    def close(self):
        """클라이언트 종료"""
        self.disconnect()
        if self.session:
            self.session.close()
        logger.info("SSE 클라이언트 종료")

# 편의 함수들
def create_sse_client(base_url: str = "http://localhost:8505") -> SSEClient:
    """SSE 클라이언트 생성"""
    return SSEClient(base_url)

def simple_stream_chat(
    message: str, 
    base_url: str = "http://localhost:8505",
    on_chunk: Optional[Callable[[str], None]] = None,
    on_complete: Optional[Callable[[str], None]] = None
) -> str:
    """간단한 스트림 채팅"""
    client = SSEClient(base_url)
    full_response = ""
    
    def handle_chunk(event: SSEEvent):
        nonlocal full_response
        if event.event == "response_chunk":
            chunk = event.data.get("chunk", "")
            full_response += chunk
            if on_chunk:
                on_chunk(chunk)
    
    def handle_complete(event: SSEEvent):
        if on_complete:
            on_complete(full_response)
    
    try:
        client.on_response_chunk(handle_chunk)
        client.on_agent_complete(handle_complete)
        
        client.connect_stream(message, blocking=True)
        return full_response
        
    finally:
        client.close()

# 메인 테스트
if __name__ == "__main__":
    print("🧪 SSE 클라이언트 테스트")
    print("=" * 50)
    
    # 클라이언트 생성
    client = create_sse_client()
    
    # 이벤트 핸들러 등록
    def on_any_event(event: SSEEvent):
        print(f"📡 {event.event}: {event.data.get('message', '')[:50]}...")
    
    def on_response_chunk(event: SSEEvent):
        chunk = event.data.get("chunk", "")
        print(f"📝 청크: {chunk}", end="", flush=True)
    
    def on_complete(event: SSEEvent):
        print(f"\n✅ 완료: {len(event.data.get('full_response', ''))}자")
    
    client.on_any_event(on_any_event)
    client.on_response_chunk(on_response_chunk)
    client.on_agent_complete(on_complete)
    
    try:
        # 스트림 연결
        print("스트림 연결 중...")
        client.connect_stream("주소 리스트 보여줘", blocking=True)
        
        # 통계 출력
        stats = client.get_stats()
        print(f"\n📊 통계:")
        print(f"  - 받은 이벤트: {stats['events_received']}")
        print(f"  - 오류 수: {stats['errors']}")
        print(f"  - 상태: {stats['state']}")
        
    finally:
        client.close()
        print("\n✅ 테스트 완료") 