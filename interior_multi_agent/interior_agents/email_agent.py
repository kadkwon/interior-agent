"""
📧 이메일 전문 하위 에이전트 - estimate-email-mcp 전용 처리
"""

import json
from typing import Optional
from .mcp_client import email_client

async def send_estimate_email(email: str, address: str, process_data: Optional[str] = None, session_id: str = None):
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

async def test_email_connection(session_id: str = None):
    """이메일 서버 연결 테스트"""
    print(f"🔧 [EMAIL-AGENT] 이메일 서버 연결 테스트 시작")
    
    result = await email_client.call_tool("test_connection", {
        "random_string": "test"
    }, session_id)
    
    if "error" in result:
        return f"❌ 이메일 서버 연결 실패: {result['error']}"
    return "✅ 이메일 서버 연결 성공"

async def get_email_server_info(session_id: str = None):
    """이메일 서버 정보 조회"""
    print(f"📊 [EMAIL-AGENT] 이메일 서버 정보 조회 시작")
    
    result = await email_client.call_tool("get_server_info", {
        "random_string": "info"
    }, session_id)
    
    if "error" in result:
        return f"❌ 서버 정보 조회 실패: {result['error']}"
    return f"📧 이메일 서버 정보: {result}"

# 하위 에이전트 함수들 export
__all__ = [
    'send_estimate_email',
    'test_email_connection', 
    'get_email_server_info'
] 