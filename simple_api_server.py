from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import json
import logging
from datetime import datetime
import asyncio

# 환경 변수 로드 (API 서버에서만)
try:
    from dotenv import load_dotenv
    # 현재 디렉토리와 interior_multi_agent 디렉토리에서 .env 파일 로드
    load_dotenv()  # 현재 디렉토리의 .env
    load_dotenv("interior_multi_agent/.env")  # interior_multi_agent의 .env
    load_dotenv(".env")  # 명시적으로 .env 파일 로드
    logger = logging.getLogger(__name__)
    logger.info("✅ 환경 변수 로드 완료")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ python-dotenv가 설치되지 않음. 환경 변수를 수동으로 설정하세요.")

# Google ADK imports
from google import adk
from google.adk.sessions import InMemorySessionService
from google.genai import types

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'interior_multi_agent'))

# 루트 에이전트 로드
try:
    from interior_agents import root_agent
    
    # Google ADK Runner 설정
    session_service = InMemorySessionService()
    runner = adk.Runner(
        agent=root_agent,
        app_name="interior_agent",
        session_service=session_service
    )
    
    AGENT_AVAILABLE = True
    logger.info("✅ 루트 에이전트 로드 성공")
except ImportError as e:
    AGENT_AVAILABLE = False
    logger.error(f"❌ 루트 에이전트 로드 실패: {e}")
    runner = None

# FastAPI 앱 생성
app = FastAPI(
    title="인테리어 에이전트 API",
    description="모바일 최적화 챗봇을 위한 단순 API 서버",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    session_id: str
    agent_status: str

class HealthResponse(BaseModel):
    status: str
    agent_available: bool
    timestamp: str

# API 엔드포인트
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 및 에이전트 상태 확인"""
    return HealthResponse(
        status="healthy",
        agent_available=AGENT_AVAILABLE,
        timestamp=datetime.now().isoformat()
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """챗봇 메시지 처리"""
    try:
        if not AGENT_AVAILABLE or not runner:
            raise HTTPException(
                status_code=503, 
                detail="에이전트가 사용 불가능합니다"
            )
        
        # 루트 에이전트 호출 (Google ADK Runner 사용)
        logger.info(f"📥 메시지 수신: {request.message[:50]}...")
        
        # 세션 생성 (비동기 방식)
        try:
            session = await session_service.create_session(
                app_name="interior_agent",
                user_id="user_001",
                session_id=request.session_id
            )
        except Exception as session_error:
            # 세션이 이미 존재하는 경우 기존 세션 사용
            logger.info(f"기존 세션 사용: {request.session_id}")
        
        # 메시지 생성
        content = types.Content(role='user', parts=[types.Part(text=request.message)])
        
        # 에이전트 실행 (비동기 방식)
        response_text = ""
        events = runner.run_async(
            user_id="user_001",
            session_id=request.session_id,
            new_message=content
        )
        
        # 모든 이벤트 처리 (비동기)
        async for event in events:
            logger.info(f"🔍 이벤트 타입: {type(event)}")
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                            logger.info(f"📝 텍스트 추가: {part.text[:50]}...")
            
            if event.is_final_response():
                logger.info("✅ 최종 응답 이벤트 감지")
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                break
        
        logger.info(f"📤 응답 생성 완료: {len(response_text)}자")
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.now().isoformat(),
            session_id=request.session_id,
            agent_status="success"
        )
        
    except Exception as e:
        logger.error(f"❌ 채팅 처리 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "인테리어 에이전트 API 서버",
        "version": "1.0.0",
        "agent_available": AGENT_AVAILABLE,
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8505) 