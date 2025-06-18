"""
FastAPI 인테리어 에이전트 서버 - Firebase MCP 연동
"""

import logging
import uuid
import json
import asyncio
import aiohttp
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="인테리어 에이전트 API", version="1.0.0")

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

class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """채팅 응답"""
    response: str
    agent_status: str = "active"
    tools_used: List[Dict[str, Any]] = []
    timestamp: str = ""

class FirebaseMCPClient:
    """Firebase MCP 서버와 통신하는 클라이언트 - SSE 지원 및 올바른 MCP 프로토콜 구현"""
    
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
        """MCP 프로토콜 초기화 - Firebase MCP 서버 요구사항 준수"""
        if self.initialized:
            return True
            
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "interior-agent-client",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        }
        
        # Firebase MCP 서버 요구사항: Accept 헤더에 text/event-stream 포함
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
                    # Firebase MCP 서버의 세션 ID는 헤더에서 추출
                    self.session_id = response.headers.get('mcp-session-id')
                    if not self.session_id:
                        self.session_id = str(uuid.uuid4())
                    
                    # SSE 응답 처리
                    if response.headers.get('Content-Type') == 'text/event-stream':
                        result = await self._parse_sse_response(response)
                    else:
                        result = await response.json()
                    
                    self.initialized = True
                    logger.info(f"MCP 초기화 성공. 세션 ID: {self.session_id}")
                    logger.info(f"서버 응답: {result}")
                    return True
                else:
                    logger.error(f"MCP 초기화 실패: {response.status}")
                    response_text = await response.text()
                    logger.error(f"응답 내용: {response_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"MCP 초기화 오류: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Firebase MCP 도구 호출 - 올바른 프로토콜 준수"""
        
        # 초기화 확인
        if not self.initialized:
            logger.warning("MCP가 초기화되지 않았습니다. 재시도합니다.")
            if not await self._initialize_mcp():
                return {"error": "MCP 초기화 실패"}
        
        # 도구 호출 페이로드
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Firebase MCP 서버 요구사항에 맞는 헤더 설정
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
                    # SSE 응답 처리
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

class InteriorAgent:
    """인테리어 전문 에이전트"""
    
    def __init__(self):
        self.name = "인테리어 전문 에이전트"
        self.description = "Firebase를 통한 주소 관리와 인테리어 상담을 제공하는 AI 어시스턴트"
        
    async def process_message(self, message: str, user_id: str = "default", session_id: str = None) -> Dict[str, Any]:
        """메시지 처리 및 응답 생성"""
        
        try:
            # 주소 관련 키워드 감지
            address_keywords = ["주소", "위치", "address", "location", "집", "집주소", "시공지", "현장"]
            firebase_action = None
            firebase_result = None
            
            # Firebase 작업이 필요한지 판단
            message_lower = message.lower()
            
            if any(keyword in message for keyword in address_keywords):
                try:
                    if ("조회" in message or "목록" in message or "찾기" in message) and not ("저장" in message or "추가" in message):
                        firebase_action = "주소 목록 조회"
                        firebase_result = await self._handle_address_list()
                    elif "삭제" in message or "제거" in message:
                        firebase_action = "주소 삭제 요청"
                        firebase_result = await self._handle_address_delete(message)
                    elif "저장" in message or "추가" in message or "등록" in message:
                        firebase_action = "주소 정보 저장 요청"
                        firebase_result = await self._handle_address_save(message, user_id)
                except Exception as e:
                    logger.error(f"Firebase 작업 중 오류: {e}", exc_info=True)
                    firebase_result = {"error": f"Firebase 작업 오류: {str(e)}"}
            
            # 응답 생성
            try:
                if firebase_result:
                    response = await self._generate_firebase_response(message, firebase_action, firebase_result)
                else:
                    response = await self._generate_general_response(message)
            except Exception as e:
                logger.error(f"응답 생성 중 오류: {e}", exc_info=True)
                response = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
            
            return {
                "response": response,
                "agent_status": "active",
                "tools_used": [{"tool": firebase_action, "result": str(firebase_result)}] if firebase_action else [],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"메시지 처리 전체 오류: {e}", exc_info=True)
            return {
                "response": f"메시지 처리 중 예상치 못한 오류가 발생했습니다: {str(e)}",
                "agent_status": "error",
                "tools_used": [],
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_address_save(self, message: str, user_id: str) -> Dict[str, Any]:
        """주소 저장 처리"""
        try:
            # 메시지에서 주소 정보 추출 (간단한 예시)
            address_data = {
                "user_id": user_id,
                "raw_message": message,
                "timestamp": datetime.now().isoformat(),
                "status": "pending_verification"
            }
            
            async with FirebaseMCPClient(FIREBASE_MCP_URL) as client:
                result = await client.call_tool(
                    "firestore_add_document",
                    {
                                            "collection": "addressesJson",
                    "data": address_data
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"주소 저장 중 오류: {e}")
            return {"error": str(e)}
    
    async def _handle_address_list(self) -> Dict[str, Any]:
        """주소 목록 조회"""
        try:
            logger.info("Firebase에서 실제 주소 목록을 조회합니다...")
            async with FirebaseMCPClient(FIREBASE_MCP_URL) as client:
                result = await client.call_tool(
                    "firestore_list_documents",
                    {
                        "collection": "addressesJson",
                        "limit": 20
                    }
                )
            
            logger.info(f"주소 목록 조회 결과: {result}")
            return result
            
        except Exception as e:
            logger.error(f"주소 조회 중 오류: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def _handle_address_delete(self, message: str) -> Dict[str, Any]:
        """주소 삭제 처리"""
        # 실제 구현에서는 메시지에서 삭제할 주소 ID를 추출해야 함
        return {"message": "주소 삭제 기능은 추후 구현 예정입니다."}
    
    async def _generate_firebase_response(self, message: str, action: str, firebase_result: Dict[str, Any]) -> str:
        """Firebase 작업 결과를 바탕으로 응답 생성"""
        
        if "error" in firebase_result:
            return f"죄송합니다. {action} 중 오류가 발생했습니다: {firebase_result['error']}"
        
        if action == "주소 정보 저장 요청":
            return f"""
✅ 주소 정보가 성공적으로 저장되었습니다!

📍 **저장된 정보:**
- 사용자 메시지: {message}
- 저장 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

이제 인테리어 시공 계획을 세워보겠습니다. 어떤 공간을 리모델링하고 싶으신가요?
"""
        
        elif action == "주소 목록 조회":
            try:
                logger.info(f"주소 목록 응답 생성 중... firebase_result: {firebase_result}")
                
                # Firebase MCP 응답 구조: result.content[0].text에 JSON 문자열
                if firebase_result.get("result") and firebase_result["result"].get("content"):
                    content = firebase_result["result"]["content"][0]
                    if content.get("type") == "text":
                        # text 필드의 JSON 문자열을 파싱
                        data_str = content.get("text", "{}")
                        logger.info(f"파싱할 데이터: {data_str}")
                        
                        try:
                            firestore_data = json.loads(data_str)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON 파싱 실패: {e}, 데이터: {data_str}")
                            return "데이터 파싱 중 오류가 발생했습니다."
                        
                        documents = firestore_data.get("documents", [])
                        logger.info(f"찾은 문서 수: {len(documents) if isinstance(documents, list) else 'N/A'}")
                        
                        if documents and isinstance(documents, list):
                            address_list = []
                            # 안전한 슬라이싱
                            doc_count = min(len(documents), 10)
                            for i in range(doc_count):
                                doc = documents[i]
                                if isinstance(doc, dict):
                                    doc_id = doc.get("id", "")
                                    doc_data = doc.get("data", {})
                                    if isinstance(doc_data, dict):
                                        address = doc_data.get("address", "")
                                        description = doc_data.get("description", "")
                                        raw_message = doc_data.get("raw_message", "")
                                        name = doc_data.get("name", "")
                                        user_id = doc_data.get("user_id", "")
                                        timestamp = doc_data.get("timestamp", "")
                                        
                                        # 표시할 주소 정보 결정 (우선순위: name > address > description > raw_message)
                                        display_text = name or address or description or raw_message or f"주소 ID: {doc_id}"
                                        
                                        # 타임스탬프가 있으면 날짜 추가
                                        date_info = ""
                                        if timestamp:
                                            try:
                                                from datetime import datetime
                                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                                date_info = f" ({dt.strftime('%Y-%m-%d')})"
                                            except:
                                                pass
                                        
                                        address_list.append(f"- {display_text}{date_info}")
                            
                            if address_list:
                                return f"""
📋 **등록된 주소 목록 ({len(address_list)}개):**

{chr(10).join(address_list)}

어떤 주소의 인테리어 계획을 진행하시겠습니까?
"""
                            else:
                                return "아직 등록된 주소가 없습니다. 먼저 시공할 주소를 알려주세요!"
                        else:
                            return "아직 등록된 주소가 없습니다. 먼저 시공할 주소를 알려주세요!"
                    else:
                        logger.error(f"잘못된 응답 타입: {content.get('type')}")
                        return "데이터 형식 오류가 발생했습니다."
                else:
                    logger.error("Firebase 응답에 필요한 데이터가 없습니다.")
                    return "주소 목록을 불러오는 중 문제가 발생했습니다."
            except Exception as e:
                logger.error(f"주소 목록 파싱 오류: {e}", exc_info=True)
                return f"주소 목록 처리 중 오류가 발생했습니다: {str(e)}"
        
        return f"{action}이 완료되었습니다."
    
    async def _generate_general_response(self, message: str) -> str:
        """일반적인 인테리어 상담 응답 생성"""
        
        # 인테리어 관련 키워드 감지
        if any(keyword in message for keyword in ["리모델링", "인테리어", "시공", "디자인"]):
            return """
🏠 **인테리어 전문 상담사입니다!**

인테리어 프로젝트를 도와드리겠습니다. 다음 정보를 알려주시면 더 정확한 상담이 가능합니다:

📍 **시공 주소** - 어디서 작업하실 건가요?
📐 **공간 정보** - 아파트, 주택, 상가 등
💰 **예산 규모** - 대략적인 예산 범위
🎨 **원하는 스타일** - 모던, 클래식, 미니멀 등

시공 주소부터 알려주시면 맞춤형 계획을 세워드리겠습니다!
"""
        
        elif any(keyword in message for keyword in ["예산", "비용", "가격"]):
            return """
💰 **인테리어 예산 가이드**

일반적인 인테리어 비용 (평당):
- **전체 리모델링**: 300-500만원
- **부분 리모델링**: 150-300만원  
- **페인트/도배**: 50-100만원

정확한 견적을 위해서는:
1. 시공 주소와 평수
2. 원하는 작업 범위
3. 선호하는 자재 등급

이 정보들을 알려주시면 맞춤 견적을 드리겠습니다!
"""
        
        elif any(keyword in message for keyword in ["일정", "기간", "시간"]):
            return """
📅 **인테리어 시공 일정**

일반적인 작업 기간:
- **전체 리모델링**: 2-3개월
- **부분 리모델링**: 2-4주
- **도배/페인트**: 3-7일

정확한 일정 계획을 위해 시공 주소와 작업 범위를 알려주세요!
"""
        
        else:
            return """
안녕하세요! 🏠 인테리어 전문 에이전트입니다.

무엇을 도와드릴까요?
- 🏡 **인테리어 상담** (리모델링, 디자인)
- 📍 **시공 주소 관리** (저장, 조회)
- 💰 **예산 계획** 및 견적
- 📅 **일정 관리** 및 시공 계획

궁금한 것이 있으시면 언제든 말씀해 주세요!
"""

# 에이전트 인스턴스 생성
interior_agent = InteriorAgent()

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    try:
        # Firebase MCP 서버 연결 테스트
        async with FirebaseMCPClient(FIREBASE_MCP_URL) as client:
            test_result = await client.call_tool("firestore_list_collections", {})
            firebase_available = "error" not in test_result
        
        return {
            "status": "healthy",
            "agent_available": True,
            "firebase_connected": firebase_available,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check 실패: {e}")
        return {
            "status": "degraded",
            "agent_available": True,
            "firebase_connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

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
            
        message_preview = request.message[:50] if len(request.message) > 50 else request.message
        logger.info(f"메시지 처리 시작: {message_preview}...")
        
        # 메시지 처리
        result = await interior_agent.process_message(
            request.message, 
            request.user_id, 
            request.session_id
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {e}", exc_info=True)
        return ChatResponse(
            response=f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
            agent_status="error",
            timestamp=datetime.now().isoformat()
        )

@app.post("/address/save")
async def save_address(address_data: Dict[str, Any]):
    """주소 정보 직접 저장 API"""
    try:
        async with FirebaseMCPClient(FIREBASE_MCP_URL) as client:
            result = await client.call_tool(
                "firestore_add_document",
                {
                                    "collection": "addressesJson",
                "data": {
                    **address_data,
                    "timestamp": datetime.now().isoformat()
                }
                }
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/addresses")
async def get_addresses():
    """주소 목록 조회 API"""
    try:
        async with FirebaseMCPClient(FIREBASE_MCP_URL) as client:
            result = await client.call_tool(
                "firestore_list_documents",
                {"collection": "addressesJson", "limit": 20}
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8505) 