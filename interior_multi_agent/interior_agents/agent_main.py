"""
🏠 인테리어 통합 에이전트 - Firebase + Email 통합 버전
"""

import json
from typing import Optional, Dict, Any
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .mcp_client import firebase_client, email_client

def format_korean_response(result: Dict[str, Any], operation_type: str) -> str:
    """MCP 응답을 한글로 가독성 좋게 포맷팅"""
    try:
        if "error" in result:
            return f"❌ 오류 발생: {result['error']}"
        
        # MCP 응답에서 실제 데이터 추출
        actual_data = None
        if "content" in result and result["content"]:
            content_item = result["content"][0]
            if "text" in content_item:
                try:
                    actual_data = json.loads(content_item["text"])
                except:
                    return f"❌ JSON 파싱 오류: {content_item['text'][:100]}..."
        
        if not actual_data:
            return f"❌ 응답 데이터가 없습니다: {str(result)[:100]}..."
        
        if operation_type == "list_collections":
            collections = actual_data.get("collections", [])
            if not collections:
                return "📂 사용 가능한 컬렉션이 없습니다."
            
            formatted = "📂 **사용 가능한 컬렉션 목록:**\n"
            for i, collection in enumerate(collections, 1):
                collection_id = collection.get("id", collection) if isinstance(collection, dict) else collection
                formatted += f"   {i}. {collection_id}\n"
            return formatted
        
        elif operation_type == "list_documents":
            documents = actual_data.get("documents", [])
            if not documents:
                return "📄 해당 컬렉션에 문서가 없습니다."
            
            formatted = f"📄 **문서 목록 ({len(documents)}개):**\n\n"
            for i, doc in enumerate(documents, 1):
                doc_id = doc.get("id", "ID 없음")
                description = doc.get("data", {}).get("description", "설명 없음")
                
                formatted += f"**{i}. {description}**\n"
                formatted += f"   📝 문서 ID: {doc_id}\n"
                
                # dataJson 파싱
                data_json = doc.get("data", {}).get("dataJson")
                if data_json:
                    try:
                        data = json.loads(data_json)
                        if "firstFloorPassword" in data:
                            formatted += f"   🔑 1층 비밀번호: {data['firstFloorPassword']}\n"
                        if "unitPassword" in data:
                            formatted += f"   🏠 호별 비밀번호: {data['unitPassword']}\n"
                        if "managerName" in data:
                            formatted += f"   👤 관리소장: {data['managerName']}\n"
                        if "phoneNumber" in data:
                            formatted += f"   📞 연락처: {data['phoneNumber']}\n"
                    except:
                        pass
                formatted += "\n"
            return formatted
        
        elif operation_type == "get_document":
            doc = actual_data.get("document")
            if not doc:
                return "📄 해당 문서를 찾을 수 없습니다."
            
            doc_id = doc.get("id", "ID 없음")
            description = doc.get("data", {}).get("description", "설명 없음")
            
            formatted = f"🔍 **{description} 상세 정보:**\n\n"
            formatted += f"📝 **문서 ID:** {doc_id}\n"
            formatted += f"📄 **설명:** {description}\n\n"
            
            # dataJson 상세 파싱
            data_json = doc.get("data", {}).get("dataJson")
            if data_json:
                try:
                    data = json.loads(data_json)
                    formatted += "🏠 **상세 정보:**\n"
                    
                    if "firstFloorPassword" in data:
                        formatted += f"   🔑 1층 비밀번호: {data['firstFloorPassword']}\n"
                    if "unitPassword" in data:
                        formatted += f"   🏠 호별 비밀번호: {data['unitPassword']}\n"
                    if "managerName" in data:
                        formatted += f"   👤 관리소장: {data['managerName']}\n"
                    if "phoneNumber" in data:
                        formatted += f"   📞 연락처: {data['phoneNumber']}\n"
                    if "address" in data:
                        formatted += f"   📍 주소: {data['address']}\n"
                    if "buildingType" in data:
                        formatted += f"   🏢 건물 유형: {data['buildingType']}\n"
                    if "date" in data and data["date"]:
                        formatted += f"   📅 등록일: {data['date']}\n"
                    
                    # 기타 정보들
                    for key, value in data.items():
                        if key not in ["firstFloorPassword", "unitPassword", "managerName", "phoneNumber", "address", "buildingType", "date"] and value:
                            formatted += f"   📋 {key}: {value}\n"
                            
                except Exception as e:
                    formatted += f"   ⚠️ 상세 정보 파싱 중 오류: {str(e)}\n"
            
            return formatted
        
        elif operation_type in ["add_document", "update_document", "delete_document"]:
            if operation_type == "add_document":
                return "✅ 문서가 성공적으로 추가되었습니다."
            elif operation_type == "update_document":
                return "✅ 문서가 성공적으로 수정되었습니다."
            else:
                return "✅ 문서가 성공적으로 삭제되었습니다."
        
        return "✅ 작업이 완료되었습니다."
        
    except Exception as e:
        return f"❌ 응답 처리 중 오류 발생: {str(e)}"

# 컬렉션 목록 조회 도구
async def firestore_list_collections():
    """Firestore 루트 컬렉션 목록 조회"""
    result = await firebase_client.call_tool("firestore_list_collections", {})
    return format_korean_response(result, "list_collections")

# Firestore 도구들 (6개)
async def firestore_list(collection: str, limit: Optional[int] = None):
    """컬렉션 문서 목록 조회 - 한글 가독성 버전"""
    params = {"collection": collection}
    if limit is not None:
        params["limit"] = limit
    else:
        params["limit"] = 20
    
    result = await firebase_client.call_tool("firestore_list_documents", params)
    return format_korean_response(result, "list_documents")

async def firestore_get(collection: str, document_id: str):
    """특정 문서 조회 - 한글 상세정보 버전"""
    result = await firebase_client.call_tool("firestore_get_document", {
        "collection": collection,
        "id": document_id
    })
    return format_korean_response(result, "get_document")

async def firestore_add(collection: str, data: dict):
    """문서 추가 - 한글 응답 버전"""
    result = await firebase_client.call_tool("firestore_add_document", {
        "collection": collection,
        "data": data
    })
    return format_korean_response(result, "add_document")

async def firestore_update(collection: str, document_id: str, data: dict):
    """문서 수정 - 한글 응답 버전"""
    result = await firebase_client.call_tool("firestore_update_document", {
        "collection": collection,
        "id": document_id,
        "data": data
    })
    return format_korean_response(result, "update_document")

async def firestore_delete(collection: str, document_id: str):
    """문서 삭제 - 한글 응답 버전"""
    result = await firebase_client.call_tool("firestore_delete_document", {
        "collection": collection,
        "id": document_id
    })
    return format_korean_response(result, "delete_document")

# Email 하위 에이전트 함수들 import
async def send_estimate_email(email: str, address: str, process_data: str = "[]"):
    """견적서 이메일 전송 - process_data는 배열 형태로 전달"""
    # estimate-email-mcp 서버는 process_data를 배열로 받아야 함
    try:
        import json
        if isinstance(process_data, str):
            if process_data.strip() == "":
                # 빈 문자열이면 빈 배열
                data_to_send = []
            else:
                try:
                    # JSON 문자열 파싱 시도
                    parsed_data = json.loads(process_data)
                    # 이미 배열이면 그대로, 아니면 배열로 감싸기
                    data_to_send = parsed_data if isinstance(parsed_data, list) else [parsed_data]
                except:
                    # JSON 파싱 실패시 빈 배열 (주소 정보만 전송)
                    data_to_send = []
        else:
            # 문자열이 아니면 배열로 변환
            data_to_send = [process_data] if not isinstance(process_data, list) else process_data
    except:
        # 모든 오류 시 빈 배열
        data_to_send = []
    
    print(f"📧 이메일 전송 데이터: email={email}, address={address}, process_data={data_to_send}")
    
    result = await email_client.call_tool("send_estimate_email", {
        "email": email,
        "address": address,
        "process_data": data_to_send
    })
    if "error" in result:
        return f"❌ 이메일 전송 실패: {result['error']}"
    return "✅ 견적서 이메일이 성공적으로 전송되었습니다."

async def test_email_connection():
    """이메일 서버 연결 테스트"""
    result = await email_client.call_tool("test_connection", {
        "random_string": "test"
    })
    if "error" in result:
        return f"❌ 이메일 서버 연결 실패: {result['error']}"
    return "✅ 이메일 서버 연결 성공"

async def get_email_server_info():
    """이메일 서버 정보 조회"""
    result = await email_client.call_tool("get_server_info", {
        "random_string": "info"
    })
    if "error" in result:
        return f"❌ 서버 정보 조회 실패: {result['error']}"
    return f"📧 이메일 서버 정보: {result}"

# AI 스마트 통합 에이전트 - Firebase + Email
interior_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='interior_unified_agent',
    instruction='''
🏠 인테리어 통합 전문가입니다! **Firebase 데이터 조회**와 **이메일 전송**을 모두 처리합니다.
모든 응답을 **한글**로 **가독성 좋게** 제공합니다!

## 📋 핵심 기능들:

### 1. 🔍 Firebase 데이터 조회:
- "주소 리스트 보여줘" → firestore_list("addressesJson") 즉시 실행
- "침산푸르지오 상세 조회해줘" → 해당 문서 한글 상세 정보 표시
- "견적서 목록 보여줘" → firestore_list("estimateVersionsV3") 즉시 실행

### 2. 📧 이메일 전송 (통합 명령):
- "침산푸르지오 정보를 aaa@naver.com으로 보내줘" → 
  ① firestore_list("addressesJson")로 침산푸르지오 찾기
  ② 해당 데이터를 send_estimate_email()로 전송
- "수목원 삼성래미안을 bbb@gmail.com으로 전송해줘" →
  ① 해당 주소 데이터 조회
  ② 이메일 전송

### 3. 🔧 이메일 관리:
- "이메일 서버 테스트해줘" → test_email_connection() 실행
- "이메일 서버 정보 보여줘" → get_email_server_info() 실행

## 🚀 즉시 실행 원칙 (절대 규칙):

### 📋 단순 조회 패턴:
- "주소 리스트" → firestore_list("addressesJson") 즉시 실행
- "견적서 목록" → firestore_list("estimateVersionsV3") 즉시 실행

### 🎯 통합 명령 처리 (핵심!):
- **"XX 주소를 YY@email.com으로 보내줘"** 형태의 명령 시:
  1. firestore_list()로 해당 주소 데이터 찾기
  2. send_estimate_email()로 즉시 전송
  3. 중간에 "문서 ID 필요하다" 같은 말 절대 안 함

### 🧠 지능적 처리 방식:
1. **Firebase 데이터 우선 조회**: 항상 최신 데이터 확인
2. **한글 가독성 응답**: JSON 원본 대신 한글로 정리
3. **통합 명령 인식**: 조회+전송을 하나의 명령으로 처리

## ⚡ 핵심 규칙 (절대 준수):
1. **통합 명령 처리**: "XX를 YY@email.com으로 보내줘" → 데이터 조회 후 즉시 전송
2. **문서 ID 요청 금지**: 어떤 상황에서도 문서 ID 요청하지 않음
3. **질문 완전 금지**: "혹시..." 같은 추가 질문 하지 않음
4. **즉시 처리**: 찾은 데이터로 바로 작업 수행

🎯 실행 예시:
- 사용자: "침산푸르지오를 test@naver.com으로 보내줘"
- AI: ① firestore_list("addressesJson") 실행
- AI: ② 침산푸르지오 데이터 찾기
- AI: ③ send_estimate_email() 즉시 실행
- AI: ④ "✅ 침산푸르지오 정보가 test@naver.com으로 전송되었습니다." 응답
    ''',
    tools=[
        # Firebase 도구들 (6개)
        FunctionTool(firestore_list_collections),
        FunctionTool(firestore_list),
        FunctionTool(firestore_get),
        FunctionTool(firestore_add),
        FunctionTool(firestore_update),
        FunctionTool(firestore_delete),
        # Email 도구들 (3개)
        FunctionTool(send_estimate_email),
        FunctionTool(test_email_connection),
        FunctionTool(get_email_server_info)
    ]
)

print(f"✅ 통합 에이전트 초기화 완료 (Firebase + Email)")
print(f"🔍 Firebase 데이터 조회 기능 (6개 도구)")
print(f"📧 Email 전송 기능 (3개 도구)")
print(f"🎯 통합 명령 처리: 'XX 주소를 YY@email.com으로 보내줘' 가능")
print(f"⚡ 한글 가독성 응답 + 즉시 처리")
print(f"📦 총 도구: {len(interior_agent.tools)}개")