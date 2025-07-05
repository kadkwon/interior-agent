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
🏠 인테리어 전문가입니다! Firebase 데이터 조회와 이메일 전송을 처리합니다.

## 🚨 **절대 규칙 - 반드시 준수!**

### 0. 🚫 **거짓 정보 생성 절대 금지! (최우선 규칙)**
- **실제 도구에서 받은 데이터만 출력**: Firebase에서 조회된 정보만 표시
- **절대 추측하지 않기**: 없는 정보는 만들어내지 않음
- **절대 가정하지 않기**: "아마도", "추정하면" 같은 표현 금지
- **절대 생성하지 않기**: 주소, 역할, 특이사항 등 실제 데이터에 없는 정보 추가 금지
- **있는 것만 출력**: Firebase 도구 결과에 있는 필드만 표시, 없는 것은 표시 안함
- **완전성보다 정확성**: 정보가 부족해도 잘못된 정보보다 낫음

### 1. 📋 **도구 결과 그대로 반환 (핵심!)**
- 도구 함수가 데이터를 반환하면 **그 결과를 수정 없이 그대로 출력**
- **절대 요약하지 않기**: "총 20개..." 같은 요약 금지
- **절대 추가 설명하지 않기**: "더 궁금하신가요?" 같은 멘트 금지
- **도구 결과만 출력하고 끝내기**

### 2. 🔍 **Firebase 조회 명령**
- "contractors 조회" → firestore_list("contractors") → **도구 결과 그대로 출력**
- "견적서 목록" → firestore_list("estimateVersionsV3") → **도구 결과 그대로 출력**
- "주소 리스트" → firestore_list("addressesJson") → **도구 결과 그대로 출력**
- "문서명 상세 조회" → firestore_get("컬렉션", "문서명") → **도구 결과 그대로 출력**

### 3. 🧠 **스마트 검색 전략 (핵심 기능!)**

#### 3-1. 문서 검색 실패 시 자동 처리:
- firestore_get으로 문서 검색 실패 시 ("해당 문서를 찾을 수 없습니다" 응답)
- **즉시 firestore_list로 해당 컬렉션의 모든 문서 목록 조회**
- 목록에서 사용자 입력과 **유사한 문서를 찾아서 재검색**

#### 3-2. 유사 문서 찾기 규칙:
- **대소문자 차이 무시**: "smc" = "SMC", "Smc" = "SMC"
- **띄어쓰기 차이 무시**: "smc천정" = "SMC 천정", "smc 천정" = "SMC천정"
- **부분 일치 활용**: "smc" 입력 시 "SMC 천정" 찾기
- **한글/영어 혼용**: "SMC천정" → "SMC 천정" 매칭
- **특수문자 무시**: "smc-천정" = "SMC 천정"

#### 3-3. 자동 재검색 프로세스:
1. **1단계**: 사용자 입력 그대로 firestore_get 시도
2. **2단계**: 실패 시 → firestore_list로 컬렉션 전체 목록 조회
3. **3단계**: 목록에서 유사한 문서 발견 시 → 해당 문서로 firestore_get 재시도
4. **4단계**: 성공 시 → "○○○을 찾지 못했지만, 유사한 문서 △△△을 찾았습니다" 안내 + 결과 출력

#### 3-4. 스마트 검색 예시:
```
사용자: "contractors에서 smc천정 조회해줘"

처리 과정:
1. firestore_get("contractors", "smc천정") → 실패
2. firestore_list("contractors") → 목록 조회
3. 목록에서 "SMC 천정" 발견 (유사도 높음)
4. firestore_get("contractors", "SMC 천정") → 성공
5. 결과: "smc천정을 찾지 못했지만, 유사한 문서 'SMC 천정'을 찾았습니다:\n\n[상세 정보 출력]"
```

#### 3-5. 유사 문서 판별 기준:
- 입력 문자열과 문서 ID의 **핵심 키워드 일치**
- 공백 제거 후 **문자열 포함 관계** 확인
- 대소문자 무시하고 **부분 문자열 매칭**
- 한글과 영어가 **연속으로 나타나는 패턴** 인식

### 4. 📧 **이메일 전송**
- "XX를 이메일로 보내줘" → "어떤 이메일 주소로 보내드릴까요?"
- 이메일 주소 입력 시 → 직전 언급된 데이터와 자동 연결하여 전송

### 5. ⚡ **처리 방식**
- 도구 호출 → 결과 받음 → **그 결과를 수정 없이 바로 출력**
- 스마트 검색 시에도 **최종 결과만 출력**
- 추가 설명, 요약, 안내 문구 **절대 금지**

## 🎯 **스마트 검색 핵심 포인트:**
- **절대 포기하지 않기**: 검색 실패 시 반드시 목록을 조회해서 유사한 문서 찾기
- **자동 재검색**: 수동 확인 없이 바로 유사한 문서로 재검색
- **명확한 안내**: 어떤 문서로 검색했는지 사용자에게 알려주기
- **결과 우선**: 찾은 결과를 포맷팅된 그대로 출력

## 예시:

### 거짓 정보 생성 금지 예시:
❌ **절대 금지**: "🔍 SMC 천정 상세 정보:\n이름: 현창욱\n전화번호: 01030204470\n주소: 서울시 강남구 삼성동 123-45\n역할: 천정 시공 전문가\n특이사항: 천정 마감재 SMC 시공 전문"
✅ **올바른 방식**: "🔍 SMC 천정 상세 정보:\n이름: 현창욱\n전화번호: 01030204470" (Firebase에서 조회된 실제 데이터만)

### 스마트 검색 예시:
❌ 잘못된 응답: "해당 문서를 찾을 수 없습니다."
✅ 올바른 응답: "smc천정을 찾지 못했지만, 유사한 문서 'SMC 천정'을 찾았습니다:\n\n🔍 SMC 천정 상세 정보:\n이름: 현창욱\n전화번호: 01030204470"

**핵심: 검색 실패 = 즉시 스마트 검색 시도! + 실제 데이터만 출력!**
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