"""
🚀 초간단 FastAPI 브릿지 서버 - ADK 표준 구조 연결 버전
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

# ========================================
# 🎯 ADK 표준 에이전트 연결 (새로운 구조)
# ========================================
ADK_AVAILABLE = False
import_errors = []

print("🔍 ADK 표준 구조 로드 진단 시작...")

# ADK 표준 구조 import
try:
    print("1️⃣ 새로운 ADK 표준 인테리어 에이전트 로드 중...")
    from interior_agent import root_agent, runner, session_service, print_adk_info
    print("✅ ADK 표준 인테리어 에이전트 로드 성공")
    print(f"📦 메인 에이전트: {root_agent.name}")
    print(f"🔀 하위 에이전트: {len(root_agent.sub_agents)}개")
    for i, sub_agent in enumerate(root_agent.sub_agents):
        print(f"   {i+1}. {sub_agent.name}")
    
    # ADK 정보 출력
    print_adk_info()
    
    # 최종 성공 시에만 ADK_AVAILABLE = True
    ADK_AVAILABLE = True
    print("🎉 ADK 표준 구조 로드 완료!")
    
except ImportError as e:
    error_msg = f"❌ ADK 표준 구조 로드 실패: {e}"
    print(error_msg)
    import_errors.append(error_msg)
    
    # 폴백: 기존 구조 시도
    print("\n🔄 폴백: 기존 구조로 시도 중...")
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        from interior_multi_agent.interior_agents.agent_main import interior_agent
        
        print("✅ 기존 구조 로드 성공 (폴백 모드)")
        
        # 기존 구조로 Runner 설정
        session_service = InMemorySessionService()
        runner = Runner(
            agent=interior_agent, 
            app_name="interior_app", 
            session_service=session_service
        )
        root_agent = interior_agent  # 호환성을 위해
        
        ADK_AVAILABLE = True
        print("🔄 폴백 모드로 활성화됨")
        
    except ImportError as e2:
        error_msg2 = f"❌ 폴백 모드도 실패: {e2}"
        print(error_msg2)
        import_errors.append(error_msg2)

except Exception as e:
    error_msg = f"❌ ADK 표준 구조 초기화 실패: {e}"
    print(error_msg)
    import_errors.append(error_msg)

# 오류 요약 출력
if import_errors and not ADK_AVAILABLE:
    print(f"\n📋 총 {len(import_errors)}개 오류 발생:")
    for i, error in enumerate(import_errors, 1):
        print(f"   {i}. {error}")
    print(f"\n⚠️ ADK 비활성화됨")
else:
    print(f"\n🚀 ADK 활성화됨! (표준 구조: {len(import_errors) == 0})")

# FastAPI 앱
app = FastAPI(title="인테리어 에이전트 API - ADK 표준", version="4.0.0")

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
        "active_sessions": len(conversation_storage),
        "agent_structure": "ADK_Standard" if ADK_AVAILABLE else "Unavailable"
    }

@app.get("/status")
async def status():
    """서버 상태 확인 (리액트 호환)"""
    return {
        "mode": "ADK_Standard" if ADK_AVAILABLE else "Error",
        "status": "healthy",
        "adk_available": ADK_AVAILABLE,
        "active_sessions": len(conversation_storage),
        "session_management": "enabled",
        "agent_info": {
            "main_agent": root_agent.name if ADK_AVAILABLE else None,
            "sub_agents": len(root_agent.sub_agents) if ADK_AVAILABLE else 0
        }
    }

@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """채팅 API - ADK 표준 구조 사용"""
    
    if not ADK_AVAILABLE:
        return ChatResponse(
            response="❌ ADK 표준 구조를 사용할 수 없습니다. 서버 로그를 확인해주세요."
        )
    
    try:
        print(f"🔄 사용자 요청: {request.message}")
        
        # 🎯 ADK 표준 세션 관리
        session_id = request.session_id
        print(f"🔄 세션 ID 사용: {session_id}")
        
        # 애플리케이션 레벨 세션 초기화 (필요시)
        if session_id not in conversation_storage:
            conversation_storage[session_id] = []
            print(f"🆕 새 앱 세션 생성: {session_id}")
        else:
            print(f"🔄 기존 앱 세션 재사용: {session_id} (기록 {len(conversation_storage[session_id])}개)")
        
        # 오래된 세션 정리
        cleanup_old_sessions()
        
        # 컨텍스트 포함 메시지 생성
        context_message = create_context_message(session_id, request.message)
        print(f"📝 컨텍스트 메시지 길이: {len(context_message)} 문자")
        
        # ========================================
        # 🎯 ADK 표준 Runner 사용 (올바른 세션 관리)
        # ========================================
        print(f"🚀 ADK 표준 Runner로 요청 처리 중...")
        
        # ADK 표준 세션 생성 또는 재사용
        adk_session = None
        try:
            # 기존 세션 확인 또는 새로 생성
            try:
                adk_session = await session_service.get_session(
                    app_name="interior_agent",
                    user_id=session_id,
                    session_id=session_id
                )
                print(f"✅ 기존 ADK 세션 재사용: {adk_session.id}")
            except:
                # 세션이 없으면 새로 생성
                adk_session = await session_service.create_session(
                    app_name="interior_agent",
                    user_id=session_id,
                    session_id=session_id
                )
                print(f"✅ 새 ADK 세션 생성: {adk_session.id}")
                
        except Exception as e:
            print(f"❌ ADK 세션 생성/조회 실패: {e}")
            return ChatResponse(response="세션 생성에 실패했습니다. 다시 시도해주세요.")
        
        # Runner를 통한 실행
        response_text = ""
        try:
            print(f"🔄 ADK 세션 사용: user_id={session_id}, session_id={adk_session.id}")
            
            # 메시지 생성
            from google.genai import types
            content = types.Content(
                role='user', 
                parts=[types.Part(text=context_message)]
            )
            
            # Runner 실행 (생성된 세션 사용)
            final_response = None
            async for event in runner.run_async(
                user_id=session_id,
                session_id=adk_session.id,  # 생성된 세션 ID 사용
                new_message=content
            ):
                print(f"📨 이벤트 수신: {type(event).__name__}")
                
                # 최종 응답 추출
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                final_response = part.text
                                print(f"💬 응답 내용: {part.text[:100]}...")
        
            response_text = final_response if final_response else "에이전트가 응답을 생성하지 못했습니다."
            print(f"💬 ADK 응답 생성 완료: {len(response_text)} 문자")
            
        except Exception as e:
            print(f"❌ ADK Runner 실행 오류: {e}")
            import traceback
            traceback.print_exc()
            response_text = f"죄송합니다. 요청 처리 중 오류가 발생했습니다: {str(e)}"
        
        # 응답이 비어있으면 기본 메시지
        if not response_text or response_text.strip() == "":
            response_text = "죄송합니다. 응답을 생성하지 못했습니다. 다시 시도해주세요."
        
        # 대화 히스토리 관리
        add_to_history(session_id, "user", request.message)
        add_to_history(session_id, "assistant", response_text)
        
        return ChatResponse(response=response_text)
        
    except Exception as e:
        print(f"❌ 전체 처리 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"ADK 표준 구조 처리 오류: {str(e)}"
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
    print("="*60)
    print("🏠 인테리어 에이전트 API 서버 - ADK 표준 구조")
    print("🎯 ADK 표준 85점 준수 구조 연결")
    print("🔀 라우팅 패턴: Firebase + Email 전문 에이전트")
    print("📝 맥락 유지: 같은 세션 ID로 대화 시 이전 내용 기억")
    print("🗂️ 세션 관리: /sessions API로 세션 조회/삭제 가능")
    print("🧹 자동 정리: 1시간 비활성 세션 자동 삭제")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8506) 