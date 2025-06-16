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
from interior_multi_agent.interior_agents.agent_main import root_runner

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

class Query(BaseModel):
    """쿼리 요청 모델"""
    text: str
    session_id: str = "default"
    user_id: str = "default"

@app.post("/query")
async def process_query(query: Query):
    """쿼리 처리"""
    try:
        # 메시지 생성
        content = types.Content(
            role='user',
            parts=[types.Part(text=query.text)]
        )
        
        # 에이전트 실행
        events = root_runner.run(
            session_id=query.session_id,
            user_id=query.user_id,
            new_message=content
        )
        
        # 응답 수집
        responses = []
        for event in events:
            if hasattr(event, 'message'):
                responses.append(event.message.text)
        
        return {"result": " ".join(responses)}
    except Exception as e:
        logger.error(f"쿼리 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """상태 확인"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 