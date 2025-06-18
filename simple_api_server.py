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
                    
                    logger.info(f"도구 '{tool_name}' 호출 성공")
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
        if ADK_AGENT_AVAILABLE:
            # ADK 루트 에이전트 사용 (v1.0.0 완전 비동기 방식)
            try:
                print(f"📤 ADK v1.0.0 완전 비동기 방식으로 메시지 전송: {request.message}")
                
                # ADK v1.0.0 세션 서비스 및 Runner 설정
                session_service = InMemorySessionService()
                runner = Runner(
                    agent=root_agent,
                    app_name="interior_chatbot",
                    session_service=session_service
                )
                
                # 세션 생성 (완전 비동기)
                app_name = "interior_chatbot"
                user_id = request.session_id or f"user_{uuid.uuid4()}"
                session_id = f"session_{uuid.uuid4()}"
                
                # 비동기 세션 생성 - await 사용
                session = await session_service.create_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id
                )
                print(f"✅ 세션 생성 완료: {session_id}")
                
                # 메시지 생성
                content = types.Content(
                    role='user', 
                    parts=[types.Part(text=request.message)]
                )
                
                # ADK Runner 비동기 실행
                print(f"🔄 ADK Runner 비동기 실행 시작...")
                events = []
                
                try:
                    async for event in runner.run_async(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=content
                    ):
                        events.append(event)
                        print(f"📨 이벤트 수신: {type(event).__name__}")
                        
                        # 텍스트 응답이 있는 이벤트를 즉시 확인
                        if hasattr(event, 'content') and hasattr(event.content, 'parts'):
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    print(f"💬 즉시 텍스트 발견: {part.text[:100]}...")
                
                except Exception as mcp_error:
                    print(f"⚠️ MCP 연결 에러 발생, 하지만 이미 받은 이벤트들을 처리합니다: {mcp_error}")
                    # 에러가 발생해도 이미 받은 이벤트들은 처리 계속
                
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
                
                # 응답이 없거나 MCP 에러인 경우 기본 대안 응답 제공
                if not response_text or "응답을 생성했지만 텍스트를 추출할 수 없습니다" in response_text:
                    if len(events) > 0:
                        response_text = "죄송합니다. 현재 일부 고급 기능에 연결 문제가 있어 기본 응답을 제공합니다. Firebase 데이터베이스 연결을 확인 중입니다."
                    else:
                        response_text = "ADK 에이전트가 실행 중이지만 응답을 받지 못했습니다. 다시 시도해 주세요."
                
                print(f"📥 ADK v1.0.0 최종 응답: {response_text[:200]}...")
                
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
        user_message = request.message.lower()
        
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
        if any(keyword in user_message for keyword in ["안녕", "hello", "hi"]):
            response = "안녕하세요! 인테리어 전문 에이전트입니다. ADK 시스템과 연결하여 더 전문적인 서비스를 제공합니다!"
        elif any(keyword in user_message for keyword in ["예산", "비용", "가격"]):
            response = "인테리어 예산은 공간 크기, 원하는 스타일, 자재 등에 따라 달라집니다. 구체적인 정보를 알려주시면 더 정확한 견적을 도와드릴 수 있어요!"
        elif any(keyword in user_message for keyword in ["디자인", "스타일", "컨셉"]):
            response = "어떤 스타일을 선호하시나요? 모던, 클래식, 미니멀, 북유럽 등 다양한 스타일이 있습니다. 공간의 용도와 개인 취향을 고려해서 추천해드릴게요!"
        elif any(keyword in user_message for keyword in ["색상", "컬러", "색깔"]):
            response = "색상 선택은 공간의 분위기를 결정하는 중요한 요소입니다. 밝은 색상은 공간을 넓어 보이게 하고, 어두운 색상은 아늑한 느낌을 줍니다."
        elif any(keyword in user_message for keyword in ["시공", "공사", "리모델링"]):
            response = "시공 과정에서는 전기, 배관, 타일, 도배 등 순서가 중요합니다. 전문 업체와 상담하여 체계적으로 진행하시는 것을 추천드려요."
        elif any(keyword in user_message for keyword in ["주소", "위치", "address", "location"]):
            response = "주소 관리 기능이 필요하시군요! ADK 에이전트가 활성화되면 Firebase를 통한 주소 저장 및 관리가 가능합니다."
        else:
            response = f"'{request.message}'에 대해 더 구체적으로 알려주시면 더 정확한 답변을 드릴 수 있어요. 인테리어 관련 궁금한 점이 있으시면 언제든 물어보세요!"
        
        agent_status = "fallback_mode" if not ADK_AGENT_AVAILABLE else "basic_mode"
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat(),
            agent_status=agent_status,
            firebase_tools_used=firebase_tools_used
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}")

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