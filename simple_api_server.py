"""
🚀 초간단 FastAPI 브릿지 서버 - 세션 유지 버전
"""

import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict

# 환경변수 설정
from dotenv import load_dotenv
load_dotenv()

# ADK 에이전트 임포트 - 루트에이전트 연결
try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    # 🎯 루트에이전트와 직접 연결
    from interior_multi_agent.interior_agents.agent_main import interior_agent
    ADK_AVAILABLE = True
    print("✅ ADK 루트에이전트 로드 성공")
    print(f"📦 에이전트 이름: {interior_agent.name}")
    print(f"🔧 등록된 도구: {len(interior_agent.tools)}개")
except ImportError as e:
    print(f"❌ ADK 루트에이전트 로드 실패: {e}")
    ADK_AVAILABLE = False

# FastAPI 앱
app = FastAPI(title="인테리어 에이전트 API", version="3.1.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션 관리 - 전역 딕셔너리로 관리
active_sessions: Dict[str, any] = {}

# ADK 설정 (한 번만)
if ADK_AVAILABLE:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=interior_agent, 
        app_name="interior_app", 
        session_service=session_service
    )

# 요청/응답 모델
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str

@app.get("/health")
async def health():
    """서버 상태 확인"""
    return {
        "status": "healthy", 
        "adk_available": ADK_AVAILABLE,
        "active_sessions": len(active_sessions)
    }

@app.get("/status")
async def status():
    """서버 상태 확인 (리액트 호환)"""
    return {
        "mode": "ADK_Minimal" if ADK_AVAILABLE else "Error",
        "status": "healthy",
        "adk_available": ADK_AVAILABLE,
        "active_sessions": len(active_sessions),
        "session_management": "enabled"
    }

@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """채팅 API - 세션 유지 기능"""
    
    if not ADK_AVAILABLE:
        return ChatResponse(
            response="ADK 루트에이전트를 사용할 수 없습니다. 기본 응답: 안녕하세요! 인테리어 상담이 필요하시면 말씀해주세요."
        )
    
    try:
        print(f"🔄 사용자 요청: {request.message}")
        
        # 🎯 세션 재사용 로직
        session_id = request.session_id
        
        if session_id not in active_sessions:
            # 새 세션 생성
            session = await session_service.create_session(
                app_name="interior_app",
                user_id=session_id,
                session_id=session_id
            )
            active_sessions[session_id] = session
            print(f"🆕 새 세션 생성: {session_id}")
        else:
            # 기존 세션 재사용
            session = active_sessions[session_id]
            print(f"🔄 기존 세션 재사용: {session_id}")
        
        # 메시지 생성
        content = types.Content(
            role='user', 
            parts=[types.Part(text=request.message)]
        )
        
        # 🎯 루트에이전트 실행
        response_text = ""
        final_response = None
        
        async for event in runner.run_async(
            user_id=session_id,
            session_id=session_id,
            new_message=content
        ):
            print(f"📨 이벤트 수신: {event.author if hasattr(event, 'author') else 'Unknown'}")
            
            # 최종 응답 추출
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response = part.text
                            print(f"💬 응답 내용: {part.text[:100]}...")
        
        # 최종 응답 반환
        response_text = final_response if final_response else "루트에이전트가 응답을 생성하지 못했습니다."
        
        return ChatResponse(response=response_text)
        
    except Exception as e:
        print(f"❌ 에이전트 처리 오류: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"루트에이전트 처리 오류: {str(e)}"
        )

# 세션 관리 API
@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """특정 세션 삭제"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return {"message": f"세션 {session_id} 삭제됨"}
    return {"message": "세션을 찾을 수 없음"}

@app.delete("/sessions")
async def delete_all_sessions():
    """모든 세션 삭제"""
    count = len(active_sessions)
    active_sessions.clear()
    return {"message": f"총 {count}개 세션 삭제됨"}

if __name__ == "__main__":
    import uvicorn
    print("🧠 세션 유지 기능 활성화")
    print("📝 맥락 유지: 같은 세션 ID로 대화 시 이전 내용 기억")
    uvicorn.run(app, host="0.0.0.0", port=8506) 