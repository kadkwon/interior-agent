"""
Google ADK 공식 방식 FastAPI 서버
- Server-Sent Events (SSE) 스트리밍
- 에이전트 전환 (transfer_to_agent)
- 세션 관리
- 실시간 이벤트 생성
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 메인 에이전트 임포트
try:
    from context_chatbot.main import interior_manager
    logger.info("✅ interior_manager 에이전트 로드 성공")
except ImportError as e:
    logger.error(f"❌ interior_manager 에이전트 로드 실패: {e}")
    interior_manager = None

# 전역 변수
sessions: Dict[str, Dict] = {}
active_connections: Dict[str, Any] = {}

# Pydantic 모델들
class ChatMessage(BaseModel):
    message: str = Field(..., description="사용자 메시지")
    session_id: Optional[str] = Field(None, description="세션 ID")
    user_id: Optional[str] = Field("user", description="사용자 ID")
    agent_id: Optional[str] = Field("interior_manager", description="에이전트 ID")

class SessionCreate(BaseModel):
    user_id: str = Field("user", description="사용자 ID")
    agent_id: str = Field("interior_manager", description="에이전트 ID")

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    agent_id: str
    created_at: str
    status: str = "active"

class SSEEvent(BaseModel):
    event: str
    data: Dict[str, Any]
    timestamp: str
    session_id: str

# 세션 관리 함수들
def create_session(user_id: str = "user", agent_id: str = "interior_manager") -> str:
    """새 세션 생성"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "session_id": session_id,
        "user_id": user_id,
        "agent_id": agent_id,
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "messages": [],
        "context": {}
    }
    logger.info(f"새 세션 생성: {session_id}")
    return session_id

def get_session(session_id: str) -> Optional[Dict]:
    """세션 조회"""
    return sessions.get(session_id)

def update_session(session_id: str, data: Dict):
    """세션 업데이트"""
    if session_id in sessions:
        sessions[session_id].update(data)

# SSE 이벤트 생성 함수들
async def create_sse_event(event_type: str, data: Dict, session_id: str) -> str:
    """SSE 이벤트 생성"""
    event = SSEEvent(
        event=event_type,
        data=data,
        timestamp=datetime.now().isoformat(),
        session_id=session_id
    )
    return f"event: {event.event}\ndata: {json.dumps(event.dict(), ensure_ascii=False)}\n\n"

async def stream_agent_response(message: str, session_id: str) -> AsyncGenerator[str, None]:
    """에이전트 응답을 스트리밍으로 전송"""
    try:
        # 시작 이벤트
        yield await create_sse_event("agent_start", {
            "message": "에이전트가 응답을 생성하고 있습니다...",
            "agent_id": "interior_manager"
        }, session_id)

        # 에이전트 실행
        if interior_manager:
            # 도구 실행 시작 이벤트
            yield await create_sse_event("tool_start", {
                "message": "도구를 실행하고 있습니다...",
                "tools_available": 29
            }, session_id)

            # 실제 에이전트 실행
            response = interior_manager.run(message)
            
            # 응답 처리
            if hasattr(response, 'response'):
                agent_response = response.response
            elif isinstance(response, str):
                agent_response = response
            else:
                agent_response = str(response)

            # 도구 완료 이벤트
            yield await create_sse_event("tool_complete", {
                "message": "도구 실행이 완료되었습니다.",
                "response_length": len(agent_response)
            }, session_id)

            # 응답 스트리밍 (청크 단위로)
            chunk_size = 100
            for i in range(0, len(agent_response), chunk_size):
                chunk = agent_response[i:i+chunk_size]
                yield await create_sse_event("response_chunk", {
                    "chunk": chunk,
                    "chunk_index": i // chunk_size,
                    "is_final": i + chunk_size >= len(agent_response)
                }, session_id)
                await asyncio.sleep(0.01)  # 스트리밍 효과

            # 완료 이벤트
            yield await create_sse_event("agent_complete", {
                "message": "응답 생성이 완료되었습니다.",
                "full_response": agent_response,
                "success": True
            }, session_id)

        else:
            # 에이전트 없음 오류
            yield await create_sse_event("error", {
                "message": "에이전트를 사용할 수 없습니다.",
                "error_type": "agent_unavailable"
            }, session_id)

    except Exception as e:
        logger.error(f"스트리밍 중 오류: {e}")
        yield await create_sse_event("error", {
            "message": f"오류가 발생했습니다: {str(e)}",
            "error_type": "execution_error"
        }, session_id)

# FastAPI 앱 생성
@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    logger.info("🚀 FastAPI 서버 시작")
    logger.info(f"📊 에이전트 상태: {'✅ 사용 가능' if interior_manager else '❌ 사용 불가'}")
    yield
    logger.info("🛑 FastAPI 서버 종료")

app = FastAPI(
    title="Interior Manager ADK API",
    description="Google ADK 공식 방식 FastAPI 서버 - SSE 스트리밍 지원",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 엔드포인트들

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Interior Manager ADK API",
        "version": "2.0.0",
        "status": "running",
        "agent_available": interior_manager is not None,
        "features": [
            "Server-Sent Events (SSE)",
            "Agent Transfer",
            "Session Management",
            "Real-time Streaming"
        ]
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_available": interior_manager is not None,
        "agent_model": "gemini-2.5-flash-preview-05-20" if interior_manager else None,
        "tools_count": 29 if interior_manager else 0,
        "active_sessions": len(sessions)
    }

@app.post("/apps/{app_name}/users/{user_id}/sessions", response_model=SessionResponse)
async def create_user_session(app_name: str, user_id: str):
    """사용자 세션 생성 (Google ADK 방식)"""
    session_id = create_session(user_id, "interior_manager")
    session = sessions[session_id]
    
    return SessionResponse(
        session_id=session_id,
        user_id=user_id,
        agent_id=session["agent_id"],
        created_at=session["created_at"]
    )

@app.get("/apps/{app_name}/users/{user_id}/sessions")
async def list_user_sessions(app_name: str, user_id: str):
    """사용자 세션 목록 조회"""
    user_sessions = [
        session for session in sessions.values() 
        if session["user_id"] == user_id
    ]
    return {"sessions": user_sessions}

@app.post("/run_sse")
async def run_sse_endpoint(request: Request, message_data: ChatMessage):
    """SSE 스트리밍 엔드포인트 (Google ADK 공식 방식)"""
    
    # 세션 처리
    session_id = message_data.session_id
    if not session_id:
        session_id = create_session(message_data.user_id, message_data.agent_id)
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    # 메시지 기록
    session["messages"].append({
        "role": "user",
        "content": message_data.message,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"SSE 요청: {message_data.message[:50]}... (세션: {session_id})")
    
    # SSE 응답 생성
    async def event_stream():
        async for event in stream_agent_response(message_data.message, session_id):
            yield event
        
        # 연결 종료 이벤트
        yield await create_sse_event("connection_close", {
            "message": "연결이 종료됩니다.",
            "session_id": session_id
        }, session_id)
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/agent/chat")
async def legacy_chat_endpoint(message_data: ChatMessage):
    """레거시 호환성을 위한 일반 채팅 엔드포인트"""
    try:
        if not interior_manager:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "에이전트를 사용할 수 없습니다",
                    "response": "시스템 오류: 에이전트가 초기화되지 않았습니다."
                }
            )
        
        # 에이전트 실행
        response = interior_manager.run(message_data.message)
        
        # 응답 처리
        if hasattr(response, 'response'):
            agent_response = response.response
        elif isinstance(response, str):
            agent_response = response
        else:
            agent_response = str(response)
        
        return {
            "success": True,
            "response": agent_response,
            "timestamp": datetime.now().isoformat(),
            "agent_id": "interior_manager"
        }
        
    except Exception as e:
        logger.error(f"채팅 처리 중 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "response": f"오류가 발생했습니다: {str(e)}"
            }
        )

@app.post("/transfer_to_agent")
async def transfer_to_agent(request: Request):
    """에이전트 전환 엔드포인트"""
    try:
        data = await request.json()
        target_agent = data.get("agent_name", "interior_manager")
        message = data.get("message", "")
        session_id = data.get("session_id")
        
        logger.info(f"에이전트 전환 요청: {target_agent}")
        
        # 현재는 interior_manager만 지원
        if target_agent != "interior_manager":
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"지원하지 않는 에이전트: {target_agent}",
                    "available_agents": ["interior_manager"]
                }
            )
        
        # 일반 채팅과 동일하게 처리
        return await legacy_chat_endpoint(ChatMessage(
            message=message,
            session_id=session_id
        ))
        
    except Exception as e:
        logger.error(f"에이전트 전환 중 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """세션 정보 조회"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    return session

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "세션이 삭제되었습니다", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

@app.get("/stats")
async def get_stats():
    """서버 통계"""
    return {
        "total_sessions": len(sessions),
        "active_connections": len(active_connections),
        "agent_status": "available" if interior_manager else "unavailable",
        "uptime": time.time(),
        "features": {
            "sse_streaming": True,
            "agent_transfer": True,
            "session_management": True,
            "real_time_events": True
        }
    }

# 메인 실행
if __name__ == "__main__":
    print("🚀 Google ADK 공식 방식 FastAPI 서버 시작")
    print("📡 Server-Sent Events (SSE) 스트리밍 지원")
    print("🔄 에이전트 전환 기능 지원")
    print("📊 실시간 세션 관리")
    print("=" * 60)
    
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8505,
        reload=True,
        log_level="info"
    ) 