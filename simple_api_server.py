"""
FastAPI 서버
"""

import logging
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from interior_multi_agent.interior_agents import root_agent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """채팅 응답"""
    response: str
    tools_used: List[Dict[str, Any]] = []

@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    채팅 엔드포인트
    
    Args:
        request: 채팅 요청
        
    Returns:
        ChatResponse: 채팅 응답
    """
    try:
        # 세션 ID가 없으면 생성
        if not request.session_id:
            request.session_id = str(uuid.uuid4())
            
        # 사용자 ID가 없으면 기본값 사용
        if not request.user_id:
            request.user_id = "default-user"
            
        # 메시지 처리
        result = await root_agent.process_message(request.message)
        
        return ChatResponse(
            response=result["response"],
            tools_used=result.get("toolsUsed", [])
        )
        
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리 작업"""
    await root_agent.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 