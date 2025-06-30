"""
🚀 초간단 FastAPI 브릿지 서버 - 세션 유지 버전
"""

import os
import asyncio
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict

# 환경변수 설정
from dotenv import load_dotenv
load_dotenv()

# ADK 에이전트 임포트 - 루트에이전트 연결 (상세 진단)
ADK_AVAILABLE = False
import_errors = []

print("🔍 ADK 로드 진단 시작...")

# 단계별 import 테스트
try:
    print("1️⃣ Google ADK 패키지 로드 중...")
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    print("✅ Google ADK 패키지 로드 성공")
except ImportError as e:
    error_msg = f"❌ Google ADK 패키지 로드 실패: {e}"
    print(error_msg)
    import_errors.append(error_msg)

try:
    print("2️⃣ MCP 클라이언트 모듈 로드 중...")
    from interior_multi_agent.interior_agents.mcp_client import firebase_client, email_client
    print("✅ MCP 클라이언트 모듈 로드 성공")
except ImportError as e:
    error_msg = f"❌ MCP 클라이언트 모듈 로드 실패: {e}"
    print(error_msg)
    import_errors.append(error_msg)

try:
    print("3️⃣ 포매터 에이전트 모듈 로드 중...")
    from interior_multi_agent.interior_agents.formatter_agent import format_korean_response
    print("✅ 포매터 에이전트 모듈 로드 성공")
except ImportError as e:
    error_msg = f"❌ 포매터 에이전트 모듈 로드 실패: {e}"
    print(error_msg)
    import_errors.append(error_msg)

try:
    print("4️⃣ 루트 에이전트 모듈 로드 중...")
    from interior_multi_agent.interior_agents.agent_main import interior_agent
    print("✅ 루트 에이전트 모듈 로드 성공")
    print(f"📦 에이전트 이름: {interior_agent.name}")
    print(f"🔧 등록된 도구: {len(interior_agent.tools)}개")
    
    # 최종 성공 시에만 ADK_AVAILABLE = True
    ADK_AVAILABLE = True
    print("🎉 모든 ADK 컴포넌트 로드 완료!")
    
except ImportError as e:
    error_msg = f"❌ 루트 에이전트 모듈 로드 실패: {e}"
    print(error_msg)
    import_errors.append(error_msg)
except Exception as e:
    error_msg = f"❌ 루트 에이전트 초기화 실패: {e}"
    print(error_msg)
    import_errors.append(error_msg)

# 오류 요약 출력
if import_errors:
    print(f"\n📋 총 {len(import_errors)}개 오류 발생:")
    for i, error in enumerate(import_errors, 1):
        print(f"   {i}. {error}")
    print(f"\n⚠️ ADK 비활성화됨 (폴백 모드)")
else:
    print("\n🚀 ADK 완전 활성화됨!")

# FastAPI 앱
app = FastAPI(title="인테리어 에이전트 API", version="3.1.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션 관리 - 애플리케이션 레벨 대화 히스토리 저장
conversation_storage: Dict[str, list] = {}
MAX_HISTORY_LENGTH = 10  # 세션당 최대 대화 기록 수

# ADK 설정 (내부 세션 + 애플리케이션 히스토리)
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
        "active_sessions": len(conversation_storage)
    }

@app.get("/status")
async def status():
    """서버 상태 확인 (리액트 호환)"""
    return {
        "mode": "ADK_Minimal" if ADK_AVAILABLE else "Error",
        "status": "healthy",
        "adk_available": ADK_AVAILABLE,
        "active_sessions": len(conversation_storage),
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
        
        # 🎯 세션 기반 컨텍스트 메시지 생성
        session_id = request.session_id
        print(f"🔄 세션 ID 사용: {session_id}")
        
        # 세션 초기화 (필요시)
        if session_id not in conversation_storage:
            conversation_storage[session_id] = []
            print(f"🆕 새 세션 생성: {session_id}")
            
            # ADK 세션도 생성
            try:
                adk_session = await session_service.create_session(
                    app_name="interior_app",
                    user_id=session_id,
                    session_id=session_id
                )
                print(f"✅ ADK 세션 생성 완료: {session_id}")
            except Exception as e:
                print(f"⚠️ ADK 세션 생성 실패 (계속 진행): {e}")
        else:
            print(f"🔄 기존 세션 재사용: {session_id} (기록 {len(conversation_storage[session_id])}개)")
        
        # 오래된 세션 정리
        cleanup_old_sessions()
        
        # 컨텍스트 포함 메시지 생성
        context_message = create_context_message(session_id, request.message)
        print(f"📝 컨텍스트 메시지 길이: {len(context_message)} 문자")
        
        # 메시지 생성
        content = types.Content(
            role='user', 
            parts=[types.Part(text=context_message)]
        )
        
        # 🎯 루트에이전트 실행 (더미 세션 사용)
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
        
        # 대화 히스토리 관리
        add_to_history(session_id, "user", request.message)
        add_to_history(session_id, "assistant", response_text)
        
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
    if session_id in conversation_storage:
        del conversation_storage[session_id]
        return {"message": f"세션 {session_id} 삭제됨"}
    return {"message": "세션을 찾을 수 없음"}

@app.delete("/sessions")
async def delete_all_sessions():
    """모든 세션 삭제"""
    count = len(conversation_storage)
    conversation_storage.clear()
    return {"message": f"총 {count}개 세션 삭제됨"}

@app.get("/sessions")
async def list_sessions():
    """모든 세션 목록 조회"""
    session_info = {}
    for session_id, history in conversation_storage.items():
        session_info[session_id] = {
            "message_count": len(history),
            "last_message_time": history[-1]["timestamp"] if history else None,
            "created_time": history[0]["timestamp"] if history else None
        }
    return {"sessions": session_info, "total_sessions": len(conversation_storage)}

@app.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """특정 세션의 대화 히스토리 조회"""
    if session_id not in conversation_storage:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    history = conversation_storage[session_id]
    return {
        "session_id": session_id,
        "message_count": len(history),
        "history": history
    }

# 대화 히스토리 관리 함수들
def get_conversation_history(session_id: str) -> list:
    """세션의 대화 히스토리 조회"""
    return conversation_storage.get(session_id, [])

def add_to_history(session_id: str, role: str, content: str):
    """대화 히스토리에 메시지 추가"""
    if session_id not in conversation_storage:
        conversation_storage[session_id] = []
    
    conversation_storage[session_id].append({
        "role": role,
        "content": content,
        "timestamp": time.time()
    })
    
    # 최대 길이 초과시 오래된 기록 삭제
    if len(conversation_storage[session_id]) > MAX_HISTORY_LENGTH:
        conversation_storage[session_id] = conversation_storage[session_id][-MAX_HISTORY_LENGTH:]

def create_context_message(session_id: str, new_message: str) -> str:
    """이전 대화 히스토리를 포함한 컨텍스트 메시지 생성"""
    history = get_conversation_history(session_id)
    
    if not history:
        return new_message
    
    # 최근 5개 대화만 컨텍스트로 사용
    recent_history = history[-5:]
    context_lines = []
    
    for msg in recent_history:
        role_kr = "사용자" if msg["role"] == "user" else "어시스턴트"
        context_lines.append(f"{role_kr}: {msg['content']}")
    
    context = "\n".join(context_lines)
    
    return f"""이전 대화:
{context}

현재 질문: {new_message}

위 대화 맥락을 참고하여 자연스럽게 답변해주세요."""

def cleanup_old_sessions():
    """오래된 세션 정리 (메모리 관리)"""
    current_time = time.time()
    sessions_to_remove = []
    
    for session_id, history in conversation_storage.items():
        if history and current_time - history[-1]["timestamp"] > 3600:  # 1시간 후 삭제
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        del conversation_storage[session_id]
        print(f"🗑️ 오래된 세션 삭제: {session_id}")

if __name__ == "__main__":
    import uvicorn
    print("🧠 애플리케이션 레벨 세션 관리 활성화")
    print("📝 맥락 유지: 같은 세션 ID로 대화 시 이전 내용 기억")
    print("🗂️ 세션 관리: /sessions API로 세션 조회/삭제 가능")
    print("🧹 자동 정리: 1시간 비활성 세션 자동 삭제")
    uvicorn.run(app, host="0.0.0.0", port=8506) 