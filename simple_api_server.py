"""
FastAPI Firebase MCP 프록시 서버 - ADK 루트 에이전트 연결
"""

import logging
import uuid
import json
import aiohttp
import asyncio
import sys
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv()

# 환경변수 확인 및 설정
google_api_key = os.getenv('GOOGLE_API_KEY')
use_vertex_ai = os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'FALSE').upper() == 'TRUE'

if google_api_key:
    print(f"✅ Google API Key 로드 성공: {google_api_key[:10]}...")
    # 환경변수로 설정하여 ADK가 인식할 수 있도록 함
    os.environ['GOOGLE_API_KEY'] = google_api_key
else:
    print("⚠️ Google API Key가 .env 파일에 없습니다.")

print(f"🔧 Vertex AI 사용: {use_vertex_ai}")

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(__file__))

# ADK 루트 에이전트 임포트
try:
    from interior_multi_agent.interior_agents import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    ADK_AGENT_AVAILABLE = True
    print("✅ ADK 루트 에이전트 임포트 성공")
except ImportError as e:
    print(f"⚠️ ADK 루트 에이전트 임포트 실패: {e}")
    print("기본 Firebase MCP 클라이언트를 사용합니다.")
    ADK_AGENT_AVAILABLE = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 세션별 대화 히스토리 저장소 (메모리 기반)
session_histories = {}

def add_to_session_history(session_id: str, message_type: str, content: str, metadata: dict = None):
    """세션 히스토리에 메시지 추가"""
    if session_id not in session_histories:
        session_histories[session_id] = []
    
    session_histories[session_id].append({
        "type": message_type,  # "user" 또는 "assistant"
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    })
    
    # 히스토리가 너무 길어지면 오래된 것부터 제거 (최대 50개)
    if len(session_histories[session_id]) > 50:
        session_histories[session_id] = session_histories[session_id][-50:]
    
    print(f"📝 세션 {session_id} 히스토리 추가: {message_type} - {content[:50]}...")
    print(f"📊 현재 히스토리 개수: {len(session_histories[session_id])}")

def get_session_context(session_id: str, last_n: int = 5) -> str:
    """세션의 최근 대화 컨텍스트를 문자열로 반환"""
    if session_id not in session_histories:
        return ""
    
    recent_history = session_histories[session_id][-last_n:]
    context_lines = []
    
    for entry in recent_history:
        role = "사용자" if entry["type"] == "user" else "어시스턴트"
        context_lines.append(f"{role}: {entry['content']}")
    
    return "\n".join(context_lines)

# FastAPI 앱 생성
app = FastAPI(title="Firebase MCP 프록시 서버", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase MCP 서버 설정
FIREBASE_MCP_URL = "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"

class ToolCallRequest(BaseModel):
    """Firebase MCP 도구 호출 요청"""
    tool_name: str
    arguments: Dict[str, Any]

class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """채팅 응답"""
    response: str
    timestamp: str
    agent_status: str
    firebase_tools_used: List[str] = []

class FirebaseMCPClient:
    """Firebase MCP 서버와 통신하는 클라이언트"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session = None
        self.session_id = None
        self.initialized = False
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self._initialize_mcp()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _parse_sse_response(self, response) -> Dict[str, Any]:
        """SSE 응답을 파싱하여 JSON 데이터 추출"""
        try:
            content = await response.text()
            
            # SSE 형식에서 JSON 추출
            lines = content.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    try:
                        json_data = json.loads(line[6:])  # 'data: ' 제거
                        return json_data
                    except json.JSONDecodeError:
                        continue
            
            logger.warning(f"SSE 응답에서 JSON 데이터를 찾을 수 없습니다: {content}")
            return {"error": "No valid JSON data in SSE response"}
            
        except Exception as e:
            logger.error(f"SSE 응답 파싱 오류: {e}")
            return {"error": f"SSE parsing error: {str(e)}"}
    
    async def _initialize_mcp(self) -> bool:
        """MCP 프로토콜 초기화"""
        if self.initialized:
            return True
            
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "firebase-mcp-proxy",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        try:
            async with self.session.post(
                self.server_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    self.session_id = response.headers.get('mcp-session-id')
                    if not self.session_id:
                        self.session_id = str(uuid.uuid4())
                    
                    if response.headers.get('Content-Type') == 'text/event-stream':
                        result = await self._parse_sse_response(response)
                    else:
                        result = await response.json()
                    
                    self.initialized = True
                    logger.info(f"MCP 초기화 성공. 세션 ID: {self.session_id}")
                    return True
                else:
                    logger.error(f"MCP 초기화 실패: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"MCP 초기화 오류: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Firebase MCP 도구 호출"""
        
        if not self.initialized:
            logger.warning("MCP가 초기화되지 않았습니다. 재시도합니다.")
            if not await self._initialize_mcp():
                return {"error": "MCP 초기화 실패"}
        
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    if response.headers.get('Content-Type') == 'text/event-stream':
                        result = await self._parse_sse_response(response)
                    else:
                        result = await response.json()
                    
                    # JSON-RPC 2.0 응답에서 실제 성공/실패 판단
                    if "error" in result:
                        logger.error(f"Firebase MCP 도구 '{tool_name}' 호출 실패: {result.get('error', {}).get('message', 'Unknown error')}")
                        logger.error(f"에러 상세: {result}")
                    else:
                        logger.info(f"✅ 도구 '{tool_name}' 호출 성공")
                        logger.debug(f"응답 내용: {result}")
                    
                    return result
                else:
                    logger.error(f"Firebase MCP 도구 호출 실패: {response.status}")
                    response_text = await response.text()
                    logger.error(f"응답 내용: {response_text}")
                    return {"error": f"HTTP {response.status}: {response_text}"}
                    
        except Exception as e:
            logger.error(f"Firebase MCP 통신 오류: {e}")
            return {"error": str(e)}

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    try:
        async with FirebaseMCPClient(FIREBASE_MCP_URL) as client:
            test_result = await client.call_tool("firestore_list_collections", {"random_string": "test"})
            firebase_available = "error" not in test_result
        
        return {
            "status": "healthy",
            "firebase_connected": firebase_available,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check 실패: {e}")
        return {
            "status": "degraded",
            "firebase_connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """채팅 엔드포인트 - ADK 루트 에이전트 또는 기본 응답"""
    try:
        # 세션 ID 처리
        session_id = request.session_id or f"default-session-{uuid.uuid4()}"
        user_message = request.message
        
        print(f"💬 채팅 요청 - 세션: {session_id}, 메시지: {user_message[:50]}...")
        
        # 사용자 메시지를 히스토리에 추가
        add_to_session_history(session_id, "user", user_message)
        
        # 현재 세션의 컨텍스트 가져오기
        session_context = get_session_context(session_id, last_n=10)
        if session_context:
            print(f"📚 세션 컨텍스트 (최근 10개):\n{session_context}")
        else:
            print(f"📚 세션 컨텍스트: 없음 (새 세션)")
            
        # 컨텍스트를 포함한 메시지 구성 (ADK에 전달할 때 사용)
        message_with_context = user_message
        if session_context:
            message_with_context = f"[이전 대화 컨텍스트]\n{session_context}\n\n[현재 질문]\n{user_message}"
        if ADK_AGENT_AVAILABLE:
            # ADK 루트 에이전트 사용 (v1.0.0 완전 비동기 방식)
            try:
                print(f"📤 ADK v1.0.0 완전 비동기 방식으로 메시지 전송: {message_with_context[:100]}...")
                
                # ADK v1.0.0 세션 서비스 및 Runner 설정
                session_service = InMemorySessionService()
                runner = Runner(
                    agent=root_agent,
                    app_name="interior_chatbot",
                    session_service=session_service
                )
                
                # 세션 생성 (완전 비동기) - React 세션 ID를 ADK 세션 ID로 사용
                app_name = "interior_chatbot"
                user_id = session_id  # React에서 온 세션 ID 사용
                adk_session_id = f"adk-{session_id}"  # ADK 전용 세션 ID
                
                # 비동기 세션 생성 - await 사용
                session = await session_service.create_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=adk_session_id
                )
                print(f"✅ ADK 세션 생성 완료: {adk_session_id}")
                
                # 메시지 생성 (컨텍스트 포함)
                content = types.Content(
                    role='user', 
                    parts=[types.Part(text=message_with_context)]
                )
                
                # ADK Runner 비동기 실행
                print(f"🔄 ADK Runner 비동기 실행 시작...")
                events = []
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=adk_session_id,
                    new_message=content
                ):
                    events.append(event)
                    print(f"📨 이벤트 수신: {type(event).__name__}")
                
                print(f"✅ 총 {len(events)}개의 이벤트 수신 완료")
                
                # 최종 응답 추출 (개선된 로직)
                response_text = "ADK 에이전트가 응답을 생성했지만 텍스트를 추출할 수 없습니다."
                
                for event in reversed(events):  # 마지막 이벤트부터 확인
                    try:
                        # Event 속성들을 체크하여 응답 텍스트 추출
                        if hasattr(event, 'content'):
                            if hasattr(event.content, 'parts') and event.content.parts:
                                if hasattr(event.content.parts[0], 'text'):
                                    response_text = event.content.parts[0].text
                                    print(f"✅ 응답 텍스트 추출 성공: {response_text[:100]}...")
                                    break
                            elif hasattr(event.content, 'text'):
                                response_text = event.content.text
                                print(f"✅ 응답 텍스트 추출 성공: {response_text[:100]}...")
                                break
                        
                        # 다른 가능한 응답 필드들 체크
                        if hasattr(event, 'text'):
                            response_text = event.text
                            print(f"✅ 응답 텍스트 추출 성공: {response_text[:100]}...")
                            break
                            
                        # 이벤트 전체를 문자열로 변환하여 의미있는 내용 찾기
                        event_str = str(event)
                        if len(event_str) > 50 and "Event" not in event_str:
                            response_text = event_str
                            print(f"✅ 이벤트 문자열 추출: {response_text[:100]}...")
                            break
                            
                    except Exception as e:
                        print(f"⚠️ 이벤트 처리 중 오류: {e}")
                        continue
                
                print(f"📥 ADK v1.0.0 최종 응답: {response_text[:200]}...")
                
                # 응답을 히스토리에 추가
                add_to_session_history(session_id, "assistant", response_text, {
                    "agent_type": "adk_root_agent",
                    "adk_session_id": adk_session_id
                })
                
                # Firebase 도구 사용 여부 확인
                firebase_tools_used = []
                if "firestore" in response_text.lower() or "firebase" in response_text.lower():
                    firebase_tools_used.append("adk_root_agent_with_firebase")
                else:
                    firebase_tools_used.append("adk_root_agent")
                
                return ChatResponse(
                    response=response_text,
                    timestamp=datetime.now().isoformat(),
                    agent_status="adk_agent_active",
                    firebase_tools_used=firebase_tools_used
                )
                
            except Exception as e:
                logger.error(f"ADK v1.0.0 비동기 실행 오류: {e}")
                print(f"❌ ADK v1.0.0 에러 상세: {type(e).__name__}: {e}")
                import traceback
                print(f"🔍 전체 스택 트레이스:")
                traceback.print_exc()
                # 에러 시 기본 응답으로 폴백
                pass
        
        # 기본 응답 로직 (ADK 에이전트 사용 불가능하거나 에러 시)
        user_message_lower = user_message.lower()
        
        # Firebase에서 데이터 조회 시도
        firebase_tools_used = []
        
        # 컬렉션 목록 조회 시도
        try:
            async with FirebaseMCPClient(FIREBASE_MCP_URL) as client:
                collections_result = await client.call_tool("firestore_list_collections", {"random_string": "test"})
                if "error" not in collections_result:
                    firebase_tools_used.append("firestore_list_collections")
        except Exception as e:
            logger.warning(f"Firebase 연결 실패: {e}")
        
        # 간단한 인테리어 응답 로직
        if any(keyword in user_message_lower for keyword in ["안녕", "hello", "hi"]):
            response = "안녕하세요! 인테리어 전문 에이전트입니다. ADK 시스템과 연결하여 더 전문적인 서비스를 제공합니다!"
        elif any(keyword in user_message_lower for keyword in ["예산", "비용", "가격"]):
            response = "인테리어 예산은 공간 크기, 원하는 스타일, 자재 등에 따라 달라집니다. 구체적인 정보를 알려주시면 더 정확한 견적을 도와드릴 수 있어요!"
        elif any(keyword in user_message_lower for keyword in ["디자인", "스타일", "컨셉"]):
            response = "어떤 스타일을 선호하시나요? 모던, 클래식, 미니멀, 북유럽 등 다양한 스타일이 있습니다. 공간의 용도와 개인 취향을 고려해서 추천해드릴게요!"
        elif any(keyword in user_message_lower for keyword in ["색상", "컬러", "색깔"]):
            response = "색상 선택은 공간의 분위기를 결정하는 중요한 요소입니다. 밝은 색상은 공간을 넓어 보이게 하고, 어두운 색상은 아늑한 느낌을 줍니다."
        elif any(keyword in user_message_lower for keyword in ["시공", "공사", "리모델링"]):
            response = "시공 과정에서는 전기, 배관, 타일, 도배 등 순서가 중요합니다. 전문 업체와 상담하여 체계적으로 진행하시는 것을 추천드려요."
        elif any(keyword in user_message_lower for keyword in ["주소", "위치", "address", "location"]):
            response = "주소 관리 기능이 필요하시군요! ADK 에이전트가 활성화되면 Firebase를 통한 주소 저장 및 관리가 가능합니다."
        else:
            response = f"'{user_message}'에 대해 더 구체적으로 알려주시면 더 정확한 답변을 드릴 수 있어요. 인테리어 관련 궁금한 점이 있으시면 언제든 물어보세요!"
        
        agent_status = "fallback_mode" if not ADK_AGENT_AVAILABLE else "basic_mode"
        
        # 기본 응답을 히스토리에 추가
        add_to_session_history(session_id, "assistant", response, {
            "agent_type": "fallback_agent",
            "agent_status": agent_status
        })
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat(),
            agent_status=agent_status,
            firebase_tools_used=firebase_tools_used
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}")

@app.get("/debug/session/{session_id}")
async def get_session_history(session_id: str):
    """세션 히스토리 조회 (디버깅용)"""
    if session_id not in session_histories:
        return {"error": "세션을 찾을 수 없습니다."}
    
    return {
        "session_id": session_id,
        "message_count": len(session_histories[session_id]),
        "history": session_histories[session_id]
    }

@app.get("/debug/sessions")
async def get_all_sessions():
    """모든 세션 목록 조회 (디버깅용)"""
    return {
        "total_sessions": len(session_histories),
        "sessions": {
            session_id: len(history) 
            for session_id, history in session_histories.items()
        }
    }

@app.post("/firebase/tool")
async def call_firebase_tool(request: ToolCallRequest):
    """Firebase MCP 도구 호출 API - 모든 도구를 통합하여 처리"""
    try:
        async with FirebaseMCPClient(FIREBASE_MCP_URL) as client:
            result = await client.call_tool(request.tool_name, request.arguments)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8505) 