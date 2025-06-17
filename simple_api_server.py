"""
인테리어 프로젝트 API 서버
- Firebase MCP 서버와 통합된 API 서버
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from interior_multi_agent.interior_agents.agent_main import root_agent

# 환경 변수 설정
PORT = 8000

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="인테리어 프로젝트 API",
    description="Firebase MCP 서버와 통합된 인테리어 프로젝트 관리 API",
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

class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str
    session_id: str = "default"

@app.post("/chat")
async def chat(request: ChatRequest):
    """채팅 처리"""
    try:
        # Interior Agent로 메시지 전송
        response = await root_agent.process_message(
            message=request.message,
            session_id=request.session_id
        )
        
        # 에러 체크
        if "error" in response:
            raise HTTPException(
                status_code=500,
                detail=response["error"]
            )
            
        return response
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"채팅 처리 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    """상태 확인"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

# 서버 종료 시 세션 정리
@app.on_event("shutdown")
async def shutdown_event():
    await root_agent.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT) 