"""
🚀 초간단 FastAPI 브릿지 서버 - ADK 표준 구조 연결 버전
🎯 세션 ID 기반 라우팅으로 다중 에이전트 지원
"""

import os
import asyncio
import time
from fastapi import FastAPI, HTTPException, Request
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
    
    # 🔧 AS 전용 루트 에이전트 import 추가
    from interior_agent.as_root_agent import as_root_agent, as_runner, as_session_service
    
    print("✅ ADK 표준 인테리어 에이전트 로드 성공")
    print(f"📦 메인 에이전트: {root_agent.name}")
    print(f"🔀 하위 에이전트: {len(root_agent.sub_agents)}개")
    for i, sub_agent in enumerate(root_agent.sub_agents):
        print(f"   {i+1}. {sub_agent.name}")
    
    # 🎯 AS 전용 루트 에이전트 로드 확인
    print(f"🔧 AS 전용 루트 에이전트 로드: {as_root_agent.name}")
    print(f"🔧 AS 전용 하위 에이전트: {len(as_root_agent.sub_agents)}개")
    for i, sub_agent in enumerate(as_root_agent.sub_agents):
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
        as_root_agent = interior_agent  # 폴백 모드에서는 같은 에이전트 사용
        as_runner = runner  # 폴백 모드에서는 같은 runner 사용
        as_session_service = session_service  # 폴백 모드에서는 같은 세션 서비스 사용
        
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

# ========================================
# 🎯 세션 ID 기반 라우팅 로직
# ========================================
def get_agent_by_session_id(session_id: str):
    """
    세션 ID 패턴에 따라 사용할 에이전트를 결정합니다.
    
    Args:
        session_id (str): 클라이언트에서 전송된 세션 ID
        
    Returns:
        tuple: (에이전트 객체, 에이전트 타입 문자열, runner 객체)
        
    패턴:
        - customer-service-*: AS 전용 루트 에이전트 (소비자 상담)
        - react-session-*: 전체 루트 에이전트 (인테리어 디자인)
        - 기타: 기본값으로 전체 루트 에이전트
    """
    if not session_id:
        return root_agent, "all_agents", runner
    
    if session_id.startswith("customer-service-"):
        print(f"🔧 AS 전용 루트 에이전트 선택: {session_id}")
        return as_root_agent, "as_root_agent", as_runner
    elif session_id.startswith("react-session-"):
        print(f"🏠 전체 루트 에이전트 선택: {session_id}")
        return root_agent, "all_agents", runner
    else:
        # 기본값: 전체 루트 에이전트 사용
        print(f"🔄 기본 루트 에이전트 선택: {session_id}")
        return root_agent, "all_agents", runner

# FastAPI 앱
app = FastAPI(title="인테리어 에이전트 API - 세션 라우팅 지원", version="5.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# 🎯 세션 ID 기반 라우팅 미들웨어
# ========================================
@app.middleware("http")
async def session_routing_middleware(request: Request, call_next):
    """
    모든 HTTP 요청을 가로채서 세션 ID를 확인하고,
    적절한 에이전트 정보를 request.state에 저장합니다.
    
    이 미들웨어가 필요한 이유:
    1. 같은 서버에서 다른 챗봇들이 서로 다른 에이전트를 사용해야 함
    2. 코드 중복 없이 중앙 집중식 라우팅 관리
    3. 성능 최적화 (요청마다 에이전트 선택 로직 실행 방지)
    """
    # 요청 정보 로깅
    print(f"🌐 요청 수신: {request.method} {request.url.path}")
    
    # POST 요청의 경우 body에서 session_id 추출 시도
    if request.method == "POST" and request.url.path == "/chat":
        try:
            # body를 읽어서 session_id 확인 (한 번만 읽을 수 있으므로 주의)
            body = await request.body()
            if body:
                import json
                try:
                    body_data = json.loads(body.decode())
                    session_id = body_data.get("session_id", "")
                    print(f"📝 POST body에서 세션 ID 추출: {session_id}")
                    
                    # 에이전트 선택 및 request.state에 저장
                    selected_agent, agent_type, selected_runner = get_agent_by_session_id(session_id)
                    request.state.selected_agent = selected_agent
                    request.state.agent_type = agent_type
                    request.state.selected_runner = selected_runner
                    request.state.session_id = session_id
                    
                    print(f"✅ 에이전트 선택 완료: {agent_type}")
                    
                except json.JSONDecodeError:
                    print("⚠️ JSON 파싱 실패, 기본 에이전트 사용")
                    request.state.selected_agent = root_agent
                    request.state.agent_type = "all_agents"
                    request.state.selected_runner = runner
                    request.state.session_id = "default"
        except Exception as e:
            print(f"❌ 세션 ID 추출 실패: {e}")
            request.state.selected_agent = root_agent
            request.state.agent_type = "all_agents"
            request.state.selected_runner = runner
            request.state.session_id = "default"
    else:
        # GET 요청이나 다른 경로의 경우 기본 에이전트 사용
        request.state.selected_agent = root_agent
        request.state.agent_type = "all_agents"
        request.state.selected_runner = runner
        request.state.session_id = "default"
    
    # 다음 처리 과정으로 진행
    response = await call_next(request)
    
    # 응답 헤더에 사용된 에이전트 정보 추가 (디버깅용)
    response.headers["X-Agent-Type"] = getattr(request.state, 'agent_type', 'unknown')
    response.headers["X-Session-ID"] = getattr(request.state, 'session_id', 'unknown')
    
    return response

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
        "agent_structure": "ADK_Standard_with_SessionRouting" if ADK_AVAILABLE else "Unavailable",
        "supported_session_patterns": [
            "customer-service-*: AS 전용 에이전트",
            "react-session-*: 전체 에이전트",
            "기타: 기본 전체 에이전트"
        ]
    }

@app.get("/status")
async def status():
    """서버 상태 확인 (리액트 호환)"""
    return {
        "mode": "ADK_Standard" if ADK_AVAILABLE else "Error",
        "status": "healthy",
        "adk_available": ADK_AVAILABLE,
        "active_sessions": len(conversation_storage),
        "session_management": "enabled_with_routing",
        "agent_info": {
            "main_agent": root_agent.name if ADK_AVAILABLE else None,
            "sub_agents": len(root_agent.sub_agents) if ADK_AVAILABLE else 0,
            "as_root_agent": as_root_agent.name if ADK_AVAILABLE else None,
            "as_sub_agents": len(as_root_agent.sub_agents) if ADK_AVAILABLE else 0
        }
    }

@app.post("/chat")
async def chat(request: ChatRequest, req: Request) -> ChatResponse:
    """
    채팅 API - 세션 ID 기반 에이전트 라우팅 지원
    
    이 엔드포인트가 하는 일:
    1. 미들웨어에서 설정된 에이전트 정보 사용
    2. 세션별 대화 히스토리 관리  
    3. 선택된 에이전트로 요청 처리
    4. 일관된 응답 형식 제공
    """
    
    if not ADK_AVAILABLE:
        return ChatResponse(
            response="❌ ADK 표준 구조를 사용할 수 없습니다. 서버 로그를 확인해주세요."
        )
    
    try:
        print(f"🔄 사용자 요청: {request.message}")
        
        # 🎯 미들웨어에서 설정된 에이전트 정보 사용
        selected_agent = getattr(req.state, 'selected_agent', root_agent)
        agent_type = getattr(req.state, 'agent_type', 'all_agents')
        selected_runner = getattr(req.state, 'selected_runner', runner)
        session_id = getattr(req.state, 'session_id', request.session_id)
        
        print(f"🤖 선택된 에이전트: {agent_type}")
        print(f"🏃 선택된 Runner: {selected_runner.app_name}")
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
        # 🎯 선택된 에이전트로 요청 처리
        # ========================================
        print(f"🚀 {agent_type} 에이전트로 요청 처리 중...")
        
        # 🎯 선택된 세션 서비스 사용
        selected_session_service = selected_runner.session_service
        app_name = selected_runner.app_name
        
        # ADK 표준 세션 생성 또는 재사용
        adk_session = None
        try:
            # 기존 세션 확인 또는 새로 생성
            try:
                adk_session = await selected_session_service.get_session(
                    app_name=app_name,
                    user_id=session_id,
                    session_id=session_id
                )
                print(f"✅ 기존 ADK 세션 재사용: {adk_session.id} (앱: {app_name})")
            except:
                # 세션이 없으면 새로 생성
                adk_session = await selected_session_service.create_session(
                    app_name=app_name,
                    user_id=session_id,
                    session_id=session_id
                )
                print(f"✅ 새 ADK 세션 생성: {adk_session.id} (앱: {app_name})")
                
        except Exception as e:
            print(f"❌ ADK 세션 생성/조회 실패: {e}")
            return ChatResponse(response="세션 생성에 실패했습니다. 다시 시도해주세요.")
        
        # Runner를 통한 실행 (선택된 에이전트 사용)
        response_text = ""
        try:
            print(f"🔄 ADK 세션 사용: user_id={session_id}, session_id={adk_session.id}")
            
            # 메시지 생성
            from google.genai import types
            content = types.Content(
                role='user', 
                parts=[types.Part(text=context_message)]
            )
            
            # 🎯 선택된 Runner로 직접 실행
            print(f"🏃 선택된 Runner 사용: {selected_runner.app_name}")
            
            # Runner 실행 (생성된 세션 사용)
            final_response = None
            async for event in selected_runner.run_async(
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
            print(f"💬 {agent_type} 응답 생성 완료: {len(response_text)} 문자")
            
        except Exception as e:
            print(f"❌ {agent_type} 에이전트 실행 오류: {e}")
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
            detail=f"세션 라우팅 기반 처리 오류: {str(e)}"
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