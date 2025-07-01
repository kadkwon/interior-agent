"""
🏠 인테리어 통합 에이전트 - Firebase + Email 통합 버전 (라우팅 전담)
"""

import json
from typing import Optional, Dict, Any, List
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .mcp_client import firebase_client, email_client
from .formatter_agent import format_korean_response

# 🔄 현재 세션 추적 (글로벌)
current_session_id = None

def set_current_session(session_id: str):
    """현재 ADK 세션 ID 설정"""
    global current_session_id
    current_session_id = session_id
    print(f"🔄 현재 세션 설정: {session_id}")

# 컬렉션 목록 조회 도구
async def firestore_list_collections():
    """Firestore 루트 컬렉션 목록 조회"""
    result = await firebase_client.call_tool("firestore_list_collections", {}, current_session_id)
    return format_korean_response(result, "list_collections")

# Firestore 도구들 (6개)
async def firestore_list(collection: str, limit: Optional[int] = None):
    """컬렉션 문서 목록 조회 - 한글 가독성 버전"""
    params = {"collection": collection}
    if limit is not None:
        params["limit"] = limit
    else:
        params["limit"] = 20
    
    result = await firebase_client.call_tool("firestore_list_documents", params, current_session_id)
    return format_korean_response(result, "list_documents")

async def firestore_get(collection: str, document_id: str):
    """특정 문서 조회 - 한글 상세정보 버전"""
    print(f"🔍 [DEBUG] firestore_get 호출: collection={collection}, document_id='{document_id}'")
    
    result = await firebase_client.call_tool("firestore_get_document", {
        "collection": collection,
        "id": document_id
    }, current_session_id)
    
    print(f"🔍 [DEBUG] MCP 서버 응답: {str(result)[:200]}...")
    return format_korean_response(result, "get_document")

async def firestore_add(collection: str, data: dict):
    """문서 추가 - 한글 응답 버전"""
    result = await firebase_client.call_tool("firestore_add_document", {
        "collection": collection,
        "data": data
    }, current_session_id)
    return format_korean_response(result, "add_document")

async def firestore_update(collection: str, document_id: str, data: dict):
    """문서 수정 - 한글 응답 버전"""
    result = await firebase_client.call_tool("firestore_update_document", {
        "collection": collection,
        "id": document_id,
        "data": data
    }, current_session_id)
    return format_korean_response(result, "update_document")

async def firestore_delete(collection: str, document_id: str):
    """문서 삭제 - 한글 응답 버전"""
    result = await firebase_client.call_tool("firestore_delete_document", {
        "collection": collection,
        "id": document_id
    }, current_session_id)
    return format_korean_response(result, "delete_document")

# Email 하위 에이전트 함수들 - Google AI 완전 호환 버전
async def send_estimate_email(email: str, address: str, process_data: Optional[str] = None):
    """견적서 이메일 전송 - Google AI 호환성을 위해 기본값 None 사용"""
    # None이거나 빈 문자열이면 빈 배열 문자열로 설정
    if process_data is None or not process_data or process_data.strip() == "":
        process_data = "[]"
    
    # estimate-email-mcp 서버는 process_data를 배열로 받아야 함
    try:
        import json
        
        # 문자열을 배열로 변환하는 로직
        if isinstance(process_data, str):
            process_data = process_data.strip()
            if process_data == "" or process_data == "[]":
                # 빈 문자열이거나 빈 배열 문자열이면 빈 배열
                data_to_send = []
            else:
                try:
                    # JSON 문자열 파싱 시도
                    parsed_data = json.loads(process_data)
                    # 이미 배열이면 그대로, 아니면 배열로 감싸기
                    data_to_send = parsed_data if isinstance(parsed_data, list) else [parsed_data]
                except json.JSONDecodeError:
                    # JSON 파싱 실패시 빈 배열 (주소 정보만 전송)
                    data_to_send = []
        else:
            # 문자열이 아니면 배열로 변환
            data_to_send = [process_data] if not isinstance(process_data, list) else process_data
            
    except Exception as e:
        # 모든 오류 시 빈 배열
        print(f"⚠️ process_data 변환 오류: {e}")
        data_to_send = []
    
    print(f"📧 이메일 전송 데이터: email={email}, address={address}, process_data={data_to_send}")
    
    result = await email_client.call_tool("send_estimate_email", {
        "email": email,
        "address": address,
        "process_data": data_to_send
    }, current_session_id)
    
    if "error" in result:
        return f"❌ 이메일 전송 실패: {result['error']}"
    return "✅ 견적서 이메일이 성공적으로 전송되었습니다."

async def test_email_connection():
    """이메일 서버 연결 테스트"""
    result = await email_client.call_tool("test_connection", {
        "random_string": "test"
    }, current_session_id)
    if "error" in result:
        return f"❌ 이메일 서버 연결 실패: {result['error']}"
    return "✅ 이메일 서버 연결 성공"

async def get_email_server_info():
    """이메일 서버 정보 조회"""
    result = await email_client.call_tool("get_server_info", {
        "random_string": "info"
    }, current_session_id)
    if "error" in result:
        return f"❌ 서버 정보 조회 실패: {result['error']}"
    return f"📧 이메일 서버 정보: {result}"

# AI 스마트 통합 에이전트 - Firebase + Email (라우팅 전담)
interior_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='interior_unified_agent',
    instruction='''
🏠 인테리어 통합 전문가입니다! **Firebase 데이터 조회**와 **이메일 전송**을 모두 처리합니다.
모든 응답을 **한글**로 **가독성 좋게** 제공합니다!

## 📋 핵심 기능들:

### 1. 🔍 Firebase 데이터 조회 (무조건 도구 결과 표시):
- "주소 리스트 보여줘" → firestore_list("addressesJson") 실행 후 **반드시 도구의 결과를 그대로 반환**
- "견적서 목록 보여줘" → firestore_list("estimateVersionsV3") 실행 후 **반드시 도구의 결과를 그대로 반환**
- "월배아이파크 1차 109동 2401호_2차 보여줘" → firestore_get("estimateVersionsV3", "월배아이파크 1차 109동 2401호_2차") 실행
- 도구 함수가 성공적으로 데이터를 반환하면 **절대로 추가 설명이나 안내 없이** 그 결과를 직접 출력

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

## 🧠 **대화 맥락 유지 (절대 필수!):**

### 📧 이메일 주소만 입력된 경우 (핵심 규칙):
- **이메일 형식 감지**: "@" 포함된 입력은 이메일 주소로 인식
- **직전 대화 연결**: 바로 직전에 "XX 내용을 메일로 보내줘" 같은 요청이 있었다면 **무조건 연결**
- **자동 실행**: "gncloud86@naver.com" 입력 시, 직전에 언급된 주소로 즉시 전송
- **질문 절대 금지**: "어떤 주소를...", "어떤 작업을..." 같은 추가 질문 절대 하지 않음

### 🔄 두 단계 명령 처리 (완벽 처리):
**1단계**: "수목원 삼성래미안 내용을 메일로 보내줘"
- 응답: "어떤 이메일 주소로 보내드릴까요?"
- **내부적으로 "수목원 삼성래미안" 기억**

**2단계**: "gncloud86@naver.com"
- **즉시 실행**: send_estimate_email("gncloud86@naver.com", "수목원 삼성래미안", "[]")
- **절대 하지 않을 것**: "어떤 주소를..." 같은 되묻기

### 🚨 **맥락 유지 필수 규칙 (절대 준수):**
1. **이메일 형식 감지**: "@" 포함 = 이메일 주소 = 직전 주소와 연결
2. **직전 대화 기억**: 한 번의 대화에서 언급된 주소는 반드시 기억
3. **즉시 연결 실행**: 이메일 주소 입력 시 직전 주소와 자동 연결하여 전송
4. **되묻기 절대 금지**: 이메일 주소 받으면 무조건 전송, 추가 질문 없음

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
4. **맥락 기억**: 직전 대화의 주소 정보 기억하여 이메일 전송

## ⚡ 핵심 규칙 (절대 준수):
1. **도구 결과 필수 반환**: 도구 함수가 데이터를 반환하면 **무조건 그 결과를 그대로 출력**하고 끝내기
2. **추가 설명 금지**: 도구 결과가 있으면 "더 필요하신가요?" 같은 추가 멘트 절대 하지 않음
3. **통합 명령 처리**: "XX를 YY@email.com으로 보내줘" → 데이터 조회 후 즉시 전송
4. **맥락 유지**: 이메일 주소만 입력되면 직전 주소와 자동 연결
5. **정확한 문서 ID 사용**: 문서 상세 조회 시 리스트에서 보여진 정확한 ID 사용
6. **질문 완전 금지**: "혹시..." 또는 "어떤 작업을..." 같은 추가 질문 하지 않음
7. **즉시 처리**: 찾은 데이터로 바로 작업 수행

🎯 실행 예시:
- 사용자: "침산푸르지오를 test@naver.com으로 보내줘"
- AI: ① firestore_list("addressesJson") 실행
- AI: ② 침산푸르지오 데이터 찾기
- AI: ③ send_estimate_email() 즉시 실행
- AI: ④ "✅ 침산푸르지오 정보가 test@naver.com으로 전송되었습니다." 응답

🎯 맥락 유지 예시:
- 사용자: "수목원 삼성래미안 내용을 메일로 보내줘"
- AI: "어떤 이메일 주소로 보내드릴까요?"
- 사용자: "gncloud86@naver.com"
- AI: ① 수목원 삼성래미안 기억
- AI: ② send_estimate_email(gncloud86@naver.com, 수목원 삼성래미안, []) 즉시 실행
- AI: ③ "✅ 수목원 삼성래미안 정보가 gncloud86@naver.com으로 전송되었습니다." 응답
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

print(f"✅ 통합 에이전트 초기화 완료 (Firebase + Email) - 라우팅 전담")
print(f"🔍 Firebase 데이터 조회 기능 (6개 도구)")
print(f"📧 Email 전송 기능 (3개 도구)")
print(f"🎨 포맷팅 기능은 formatter_agent로 분리")
print(f"🎯 통합 명령 처리: 'XX 주소를 YY@email.com으로 보내줘' 가능")
print(f"🧠 맥락 유지 강화: 이메일 주소만 입력해도 직전 주소와 자동 연결")
print(f"⚡ Google AI 완전 호환 (기본값 경고 해결)")
print(f"📦 총 도구: {len(interior_agent.tools)}개")
print(f"🔧 단순화 완료: 문서 ID를 정확히 표시하여 복사/붙여넣기 가능")