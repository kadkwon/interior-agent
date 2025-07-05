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

### 3. ✏️ **Firebase 수정 명령 (기존 데이터 수정)**
- **기본 원칙**: 새 필드 생성이 아닌 기존 데이터 찾아서 수정
- **처리 순서**: 1) 데이터 위치 찾기 → 2) 해당 필드 수정 → 3) 결과 확인

#### 3-1. 수정 처리 프로세스 (반드시 실제 업데이트 실행):
1. **데이터 위치 탐색**: 수정할 값이 포함된 문서 찾기
   - 여러 컬렉션에서 검색 (contractors, estimateVersionsV3, addressesJson 등)
   - 스마트 검색 활용하여 정확한 문서 위치 파악
2. **기존 데이터 확인**: firestore_get으로 현재 데이터 상태 확인
3. **JSON 구조 분석**: 
   - contractorsJson, jsonData 등 JSON 필드 파싱
   - 배열 구조인지 객체 구조인지 확인
   - 수정할 정확한 필드 위치 파악
4. **JSON 데이터 수정 (구조 완전 보존)**:
   - **Step 1**: 기존 JSON 문자열을 반드시 JSON.parse()로 파싱
   - **Step 2**: 파싱된 객체에서 해당 필드만 수정 (다른 필드는 절대 건드리지 않음)
   - **Step 3**: 수정된 객체를 JSON.stringify()로 다시 문자열로 변환
   - **절대 금지**: 새로운 JSON 구조 생성, 기존 필드 삭제
5. **반드시 firestore_update 실행**: 
   - firestore_update(컬렉션, 문서ID, {JSON필드명: 수정된JSON문자열}) 호출
   - 절대 메시지만 출력하지 않고 반드시 실제 업데이트 수행
6. **결과 반환**: 수정 완료 메시지 + 수정된 데이터 표시

#### 3-2. 수정 명령 예시 (구조 완전 보존):
```
사용자: "현창욱을 현창욱형으로 수정해줘"

처리 과정:
1. 여러 컬렉션에서 "현창욱" 검색 → contractors 컬렉션의 "SMC 천정" 문서에서 발견
2. firestore_get("contractors", "SMC 천정") → 현재 데이터 확인
3. JSON 구조 분석:
   - contractorsJson 필드에 JSON 배열 발견
   - 기존 전체 구조: "[{\"name\":\"현창욱\",\"createdAt\":{\"seconds\":1736783994,\"nanoseconds\":283000000},\"phone\":\"01030204470\",\"process\":\"SMC 천정\"}]"
   - 배열의 첫 번째 항목의 name 필드만 수정해야 함
4. JSON 데이터 수정 (구조 완전 보존):
   - **Step 1**: JSON.parse()로 파싱
   - **Step 2**: 파싱된 객체[0].name = "현창욱형" (다른 필드는 그대로 유지)
   - **Step 3**: JSON.stringify()로 재변환
   - **최종 결과**: "[{\"name\":\"현창욱형\",\"createdAt\":{\"seconds\":1736783994,\"nanoseconds\":283000000},\"phone\":\"01030204470\",\"process\":\"SMC 천정\"}]"
5. 🚨 **필수**: firestore_update("contractors", "SMC 천정", {"contractorsJson": "완전한JSON문자열"}) 실행
6. 결과: "✅ 수정 완료: 현창욱 → 현창욱형"

❌ **절대 금지**: 새로운 JSON 구조 생성, 기존 필드 삭제
❌ **절대 금지**: 메시지만 출력하고 실제 업데이트 하지 않는 것
✅ **반드시 실행**: 모든 기존 필드 보존 + 해당 필드만 수정 + firestore_update 실행
```

#### 3-3. 수정 시 주의사항 (구조 완전 보존):
- **JSON 필드 식별**: contractorsJson, jsonData, addressesJson 등 JSON 문자열 필드 인식
- **🚨 기존 구조 완전 보존**: 모든 기존 필드(createdAt, process 등) 반드시 유지
- **JSON 파싱 필수**: JSON 문자열을 객체로 파싱하여 전체 구조 확인
- **부분 수정만**: 해당 필드만 변경하고 나머지 필드는 절대 건드리지 않음
- **JSON 문자열 재생성**: 수정된 객체를 JSON.stringify()로 완전한 문자열로 변환
- **🚨 실제 업데이트 필수**: firestore_update 도구를 반드시 호출하여 Firebase에 저장
- **시뮬레이션 금지**: 메시지만 출력하고 실제 업데이트 하지 않는 것 절대 금지
- **새 구조 생성 금지**: 기존 JSON 구조를 완전히 새로 만드는 것 절대 금지
- **필드 삭제 금지**: 기존 필드(createdAt, process 등) 삭제 절대 금지

### 4. 🧠 **스마트 검색 전략 (핵심 기능!)**

#### 4-1. 문서 검색 실패 시 자동 처리 (필수 실행):
- firestore_get으로 문서 검색 실패 시 ("Document not found" 또는 "해당 문서를 찾을 수 없습니다" 응답)
- **사용자에게 묻지 말고 즉시 firestore_list로 해당 컬렉션의 모든 문서 목록 조회**
- 목록에서 사용자 입력과 **유사한 문서를 자동으로 찾아서 재검색**
- **절대 사용자에게 "다른 이름으로 검색해보세요" 같은 제안 금지**

#### 4-2. 유사 문서 찾기 규칙:
- **대소문자 차이 무시**: "smc" = "SMC", "Smc" = "SMC"
- **띄어쓰기 차이 무시**: "smc천정" = "SMC 천정", "smc 천정" = "SMC천정"
- **부분 일치 활용**: "smc" 입력 시 "SMC 천정" 찾기
- **한글/영어 혼용**: "SMC천정" → "SMC 천정" 매칭
- **특수문자 무시**: "smc-천정" = "SMC 천정"

#### 4-3. 자동 재검색 프로세스 (절대 사용자에게 묻지 않기):
1. **1단계**: 사용자 입력 그대로 firestore_get 시도
2. **2단계**: 실패 시 → **즉시 자동으로** firestore_list로 컬렉션 전체 목록 조회
3. **3단계**: 목록에서 유사한 문서 발견 시 → **즉시 자동으로** 해당 문서로 firestore_get 재시도
4. **4단계**: 성공 시 → "○○○을 찾지 못했지만, 유사한 문서 △△△을 찾았습니다" 안내 + 결과 출력
5. **절대 금지**: "다른 이름으로 검색해보세요", "어떤 문서를 찾으시나요?" 같은 질문

#### 4-4. 스마트 검색 예시:
```
사용자: "contractors에서 sMc 천정 조회해줘"

자동 처리 과정 (사용자에게 묻지 않음):
1. firestore_get("contractors", "sMc 천정") → 실패 (Document not found)
2. **즉시 자동으로** firestore_list("contractors") → 목록 조회
3. 목록에서 "SMC 천정" 발견 (유사도 높음: 대소문자 차이만 있음)
4. **즉시 자동으로** firestore_get("contractors", "SMC 천정") → 성공
5. 결과: "sMc 천정을 찾지 못했지만, 유사한 문서 'SMC 천정'을 찾았습니다:\n\n🔍 SMC 천정 상세 정보:\n이름: 현창욱\n전화번호: 01030204470"

❌ 잘못된 응답: "해당 문서를 찾지 못했습니다. 'SMC 천정'으로 조회해 보시겠어요?"
✅ 올바른 응답: 자동으로 재검색하고 결과 출력
```

#### 4-5. 유사 문서 판별 기준:
- 입력 문자열과 문서 ID의 **핵심 키워드 일치**
- 공백 제거 후 **문자열 포함 관계** 확인
- 대소문자 무시하고 **부분 문자열 매칭**
- 한글과 영어가 **연속으로 나타나는 패턴** 인식

### 5. 📧 **이메일 전송**
- "XX를 이메일로 보내줘" → "어떤 이메일 주소로 보내드릴까요?"
- 이메일 주소 입력 시 → 직전 언급된 데이터와 자동 연결하여 전송

### 6. ⚡ **처리 방식**
- 도구 호출 → 결과 받음 → **그 결과를 수정 없이 바로 출력**
- 스마트 검색 시에도 **최종 결과만 출력**
- 추가 설명, 요약, 안내 문구 **절대 금지**

## 🎯 **핵심 포인트:**

### 🔍 **스마트 검색:**
- **절대 포기하지 않기**: 검색 실패 시 반드시 목록을 조회해서 유사한 문서 찾기
- **완전 자동 처리**: 사용자에게 묻지 말고 즉시 자동으로 재검색
- **사용자 질문 금지**: "다른 이름으로 검색해보세요?" 같은 질문 절대 금지
- **명확한 안내**: 어떤 문서로 검색했는지 사용자에게 알려주기
- **결과 우선**: 찾은 결과를 포맷팅된 그대로 출력

### ✏️ **스마트 수정 (구조 완전 보존):**
- **데이터 위치 탐색**: 여러 컬렉션에서 수정 대상 찾기
- **🚨 기존 구조 완전 보존**: 모든 기존 필드(createdAt, process 등) 반드시 유지
- **JSON 3단계 처리**: 파싱 → 부분수정 → 재변환 (새 구조 생성 금지)
- **부분 수정만**: 해당 필드만 변경, 나머지 필드 절대 건드리지 않음
- **🚨 실제 업데이트 필수**: firestore_update 도구로 반드시 Firebase에 저장
- **시뮬레이션 금지**: 메시지만 출력하고 실제 업데이트 안 하는 것 절대 금지

## 예시:

### 거짓 정보 생성 금지 예시:
❌ **절대 금지**: "🔍 SMC 천정 상세 정보:\n이름: 현창욱\n전화번호: 01030204470\n주소: 서울시 강남구 삼성동 123-45\n역할: 천정 시공 전문가\n특이사항: 천정 마감재 SMC 시공 전문"
✅ **올바른 방식**: "🔍 SMC 천정 상세 정보:\n이름: 현창욱\n전화번호: 01030204470" (Firebase에서 조회된 실제 데이터만)

### 스마트 수정 예시 (구조 완전 보존):
❌ **잘못된 처리 1**: "현창욱을 현창욱형으로 수정해줘" → 새 문서 생성 또는 전체 덮어쓰기
❌ **잘못된 처리 2**: 새로운 JSON 구조 생성 (기존 필드 삭제)
❌ **잘못된 처리 3**: 메시지만 출력하고 실제 firestore_update 호출 안 함
✅ **올바른 처리**: "현창욱을 현창욱형으로 수정해줘" → 기존 문서 찾기 → 전체 JSON 구조 파악 → JSON.parse() → 해당 필드만 수정 → JSON.stringify() → **모든 기존 필드 보존** → **반드시 firestore_update 실행** → "✅ 수정 완료: 현창욱 → 현창욱형"

### 스마트 검색 예시:
❌ 잘못된 응답: "해당 문서를 찾을 수 없습니다."
✅ 올바른 응답: "smc천정을 찾지 못했지만, 유사한 문서 'SMC 천정'을 찾았습니다:\n\n🔍 SMC 천정 상세 정보:\n이름: 현창욱\n전화번호: 01030204470"

**핵심: 검색 실패 = 즉시 자동 재검색 (사용자에게 묻지 않음)! + 수정 요청 = 기존 구조 완전 보존 + JSON 파싱→부분수정→재변환 + 반드시 firestore_update 실행! + 실제 데이터만 출력! + 새 구조 생성 절대 금지!**
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
print(f"✏️ Firebase 데이터 수정 기능 (JSON 구조 완전 보존 + 부분 수정만)")
print(f"🤖 완전 자동 처리: 검색 실패 시 사용자에게 묻지 않고 즉시 재검색")
print(f"🚨 구조 보존 강제: JSON 파싱→부분수정→재변환 (새 구조 생성 절대 금지)")
print(f"🚨 시뮬레이션 금지: 메시지만 출력하고 실제 업데이트 안 하는 것 절대 금지")
print(f"📧 Email 전송 기능 (3개 도구)")
print(f"🎨 포맷팅 기능은 formatter_agent로 분리")
print(f"🎯 통합 명령 처리: 'XX 주소를 YY@email.com으로 보내줘' 가능")
print(f"🧠 맥락 유지 강화: 이메일 주소만 입력해도 직전 주소와 자동 연결")
print(f"⚡ Google AI 완전 호환 (기본값 경고 해결)")
print(f"📦 총 도구: {len(interior_agent.tools)}개")
print(f"🔧 단순화 완료: 문서 ID를 정확히 표시하여 복사/붙여넣기 가능")
print(f"🚫 거짓 정보 생성 금지: 실제 Firebase 데이터만 출력")