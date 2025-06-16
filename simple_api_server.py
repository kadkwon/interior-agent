"""
인테리어 프로젝트 API 서버
- Firebase MCP 서버와 통합된 API 서버
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.genai import types
from interior_multi_agent.interior_agents.agent_main import root_runner, init_agent

# 환경 변수 설정
PORT = 8505

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
        # 에이전트가 없으면 재초기화 시도
        global root_runner
        if root_runner is None:
            logger.info("에이전트 재초기화 시도...")
            root_runner = init_agent()
            
        if root_runner is None:
            raise HTTPException(status_code=503, detail="에이전트를 사용할 수 없습니다.")
            
        # 메시지 생성
        content = types.Content(
            role='user',
            parts=[types.Part(text=request.message)]
        )
        
        # 에이전트 실행
        events = root_runner.run(
            session_id=request.session_id,
            user_id="default",
            new_message=content
        )
        
        # 응답 수집
        responses = []
        for event in events:
            if hasattr(event, 'message'):
                responses.append(event.message.text)
        
        if not responses:
            return {
                "response": "죄송합니다. 응답을 생성할 수 없습니다.",
                "agent_status": "error"
            }
            
        return {
            "response": " ".join(responses),
            "agent_status": "ready"
        }
    except Exception as e:
        logger.error(f"채팅 처리 중 오류 발생: {e}")
        return {
            "response": f"오류가 발생했습니다: {str(e)}",
            "agent_status": "error"
        }

@app.get("/health")
async def health_check():
    """상태 확인"""
    return {
        "status": "healthy",
        "agent_available": root_runner is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT) 