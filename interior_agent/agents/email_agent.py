"""
📧 이메일 전문 에이전트 - ADK 표준 LlmAgent 구현

🎯 Email 관련 모든 요청을 전문적으로 처리
- 견적서 이메일 전송
- 이메일 서버 연결 테스트
- 이메일 서버 정보 조회
- 복잡한 JSON 파싱 처리
"""

import json
from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from ..tools.mcp_client import email_client

# ========================================
# 📧 이메일 전문 도구 함수들
# ========================================

async def send_estimate_email(email: str, address: str, process_data: Optional[str] = None, session_id: Optional[str] = None):
    """견적서 이메일 전송 - Google AI 호환성 및 JSON 파싱 처리"""
    print(f"📧 [EMAIL-AGENT] 이메일 전송 시작: {email}")
    
    # None이거나 빈 문자열이면 빈 배열 문자열로 설정
    if process_data is None or not process_data or process_data.strip() == "":
        process_data = "[]"
    
    # estimate-email-mcp 서버는 process_data를 배열로 받아야 함
    try:
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
        print(f"⚠️ [EMAIL-AGENT] process_data 변환 오류: {e}")
        data_to_send = []
    
    print(f"📧 [EMAIL-AGENT] 전송 데이터: email={email}, address={address}, process_data={data_to_send}")
    
    # MCP 서버 호출
    result = await email_client.call_tool("send_estimate_email", {
        "email": email,
        "address": address,
        "process_data": data_to_send
    }, session_id)
    
    # 결과 처리
    if "error" in result:
        return f"❌ 이메일 전송 실패: {result['error']}"
    return "✅ 견적서 이메일이 성공적으로 전송되었습니다."

async def test_email_connection(session_id: Optional[str] = None):
    """이메일 서버 연결 테스트"""
    print(f"🔧 [EMAIL-AGENT] 이메일 서버 연결 테스트 시작")
    
    result = await email_client.call_tool("test_connection", {
        "random_string": "test"
    }, session_id)
    
    if "error" in result:
        return f"❌ 이메일 서버 연결 실패: {result['error']}"
    return "✅ 이메일 서버 연결 성공"

async def get_email_server_info(session_id: Optional[str] = None):
    """이메일 서버 정보 조회"""
    print(f"📊 [EMAIL-AGENT] 이메일 서버 정보 조회 시작")
    
    result = await email_client.call_tool("get_server_info", {
        "random_string": "info"
    }, session_id)
    
    if "error" in result:
        return f"❌ 서버 정보 조회 실패: {result['error']}"
    return f"📧 이메일 서버 정보: {result}"

# ========================================
# 🤖 이메일 전문 LlmAgent 정의
# ========================================

email_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='email_agent',
    
    # 이메일 전문 도구들
    tools=[
        FunctionTool(send_estimate_email),
        FunctionTool(test_email_connection),
        FunctionTool(get_email_server_info),
    ],
    
    # 이메일 전문 Instructions
    instruction='''
📧 이메일 전문 에이전트입니다! 견적서 이메일 전송과 이메일 서버 관리를 전문적으로 처리합니다.

## 🎯 **전문 분야**
- 견적서 이메일 전송 (복잡한 JSON 데이터 처리)
- 이메일 서버 연결 테스트
- 이메일 서버 정보 조회

## 📋 **주요 기능**

### 1. 견적서 이메일 전송
- **명령**: "견적서 이메일 전송", "이메일 보내기", "견적서 발송"
- **처리**: send_estimate_email(email, address, process_data) 호출
- **JSON 파싱**: 복잡한 process_data 자동 처리
- **예시**: "test@example.com으로 서울시 강남구 견적서 이메일 전송"

### 2. 이메일 서버 테스트
- **명령**: "이메일 서버 테스트", "이메일 연결 확인"
- **처리**: test_email_connection() 호출
- **결과**: 연결 성공/실패 상태 반환

### 3. 이메일 서버 정보 조회
- **명령**: "이메일 서버 정보", "서버 상태 확인"
- **처리**: get_email_server_info() 호출
- **결과**: 서버 설정 정보 반환

## 🚨 **중요 처리 규칙**

### JSON 데이터 처리
- process_data가 None이거나 빈 문자열이면 빈 배열로 처리
- JSON 문자열 파싱 자동 처리
- 파싱 실패시 안전한 fallback 처리

### 세션 관리
- 모든 도구 함수 호출 시 session_id 전달
- 세션 ID는 상위 에이전트에서 전달받음

### 에러 처리
- 모든 오류 상황에 대한 명확한 메시지 제공
- 사용자 친화적인 한글 응답

## 💡 **응답 형식**
- 간결하고 명확한 한글 응답
- 성공/실패 상태 명확히 표시
- 필요한 경우 상세 정보 포함
''',
    
    description="이메일 전송 및 서버 관리 전문 에이전트"
) 