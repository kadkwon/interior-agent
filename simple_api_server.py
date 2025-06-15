from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import json
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'interior_multi_agent'))

# 루트 에이전트 로드
try:
    from interior_agents import root_agent
    AGENT_AVAILABLE = True
    logger.info("✅ 루트 에이전트 로드 성공")
except ImportError as e:
    AGENT_AVAILABLE = False
    logger.error(f"❌ 루트 에이전트 로드 실패: {e}")

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
        if not AGENT_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="에이전트가 사용 불가능합니다"
            )
        
        # 루트 에이전트 호출
        logger.info(f"📥 메시지 수신: {request.message[:50]}...")
        
        response = root_agent.query(request.message)
        
        logger.info(f"📤 응답 생성 완료: {len(response)}자")
        
        return ChatResponse(
            response=response,
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