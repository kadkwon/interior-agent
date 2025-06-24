#!/usr/bin/env python3
"""
🔧 Estimate Email MCP 서버
FastMCP 기반 견적서 이메일 전송 전용 MCP 서버

역할:
- Claude Web에서 Firebase MCP로 조회한 견적서 데이터를 받아서
- 직접 Cloud Functions API를 호출하여 PDF 첨부 이메일 전송
- 기존 PDF 생성 및 이메일 전송 로직 재사용 (React 앱 우회)
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional
from fastmcp import FastMCP
from config import CONFIG

# MCP 서버 초기화
mcp = FastMCP("Estimate Email Server")

# Cloud Functions 직접 호출 (React 앱 우회)
CLOUD_FUNCTIONS_URL = CONFIG["cloud_functions"]["send_estimate_pdf"]

@mcp.tool()
def send_estimate_email(
    email: str,
    address: str, 
    process_data: list,
    notes: dict = None,
    hidden_processes: dict = None,
    corporate_profit: dict = None,
    subject: str = None,
    template_content: str = None
) -> Dict[str, Any]:
    """
    견적서를 이메일로 전송합니다.
    
    Args:
        email: 수신자 이메일 주소 (예: "user@naver.com")
        address: 견적서 주소 (예: "수성구 래미안 아파트 103동 702호")
        process_data: 공정 데이터 리스트 (Firebase에서 조회된 데이터)
        notes: 견적서 메모 (선택사항)
        hidden_processes: 숨김 공정 설정 (선택사항)
        corporate_profit: 기업이윤 설정 (선택사항)
        subject: 이메일 제목 (선택사항, 기본값 자동 생성)
        template_content: 이메일 본문 (선택사항, 기본값 자동 생성)
    
    Returns:
        Dict[str, Any]: 전송 결과 및 상태 정보
    """
    return asyncio.run(_send_estimate_email_async(
        email, address, process_data, notes, hidden_processes, 
        corporate_profit, subject, template_content
    ))

async def _send_estimate_email_async(
    email: str,
    address: str,
    process_data: list,
    notes: dict = None,
    hidden_processes: dict = None,
    corporate_profit: dict = None,
    subject: str = None,
    template_content: str = None
) -> Dict[str, Any]:
    """
    비동기 이메일 전송 실행 함수 - Cloud Functions 직접 호출
    """
    try:
        print(f"📧 이메일 전송 시작: {email} → {address}")
        
        # 기본값 설정
        if notes is None:
            notes = {}
        if hidden_processes is None:
            hidden_processes = {}
        if corporate_profit is None:
            corporate_profit = CONFIG["email"]["default_corporate_profit"].copy()
        if subject is None:
            subject = CONFIG["email"]["subject_template"].format(address=address)
        if template_content is None:
            template_content = CONFIG["email"]["content_template"].format(address=address)
        
        # Cloud Functions API 호출을 위한 데이터 준비 (기존 emailService.js 형식과 동일)
        cloud_functions_payload = {
            "to": email,
            "subject": subject,
            "html": template_content,
            # PDF 생성을 위한 견적서 데이터
            "estimateData": {
                "selectedAddress": address,
                "processData": process_data,
                "notes": notes,
                "hiddenProcesses": hidden_processes,
                "corporateProfit": corporate_profit,
                "isCorporateProfitVisible": True,
                "calculateCorporateProfitAmount": _calculate_corporate_profit_amount(process_data, corporate_profit)
            }
        }
        
        print(f"🔄 Cloud Functions API 호출 준비: {CLOUD_FUNCTIONS_URL}")
        print(f"📊 전송 데이터: 공정 {len(process_data)}개, 수신자 {email}")
        
        # HTTP 요청으로 Cloud Functions 직접 호출
        timeout = aiohttp.ClientTimeout(total=CONFIG["email"]["timeout"])
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    CLOUD_FUNCTIONS_URL,
                    json=cloud_functions_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    timeout=timeout
                ) as response:
                    
                    response_text = await response.text()
                    print(f"📨 Cloud Functions 응답 상태: {response.status}")
                    print(f"📨 API 응답 내용: {response_text[:200]}")
                    
                    if response.status == 200:
                        try:
                            result_data = await response.json()
                            print(f"✅ 이메일 전송 성공: {email}")
                            return {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"✅ 견적서가 {email}로 성공적으로 전송되었습니다!\n\n📋 전송 정보:\n- 수신자: {email}\n- 주소: {address}\n- 제목: {subject}\n- 공정 개수: {len(process_data)}개\n- 기업이윤: {_calculate_corporate_profit_amount(process_data, corporate_profit):,}원"
                                    }
                                ]
                            }
                        except json.JSONDecodeError:
                            # JSON이 아닌 응답도 성공으로 처리
                            return {
                                "content": [
                                    {
                                        "type": "text", 
                                        "text": f"✅ 견적서가 {email}로 전송되었습니다.\n\n📋 전송 정보:\n- 주소: {address}\n- 공정 개수: {len(process_data)}개"
                                    }
                                ]
                            }
                    else:
                        error_message = f"❌ Cloud Functions 호출 실패: HTTP {response.status}\n응답: {response_text}"
                        print(f"❌ {error_message}")
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": error_message
                                }
                            ]
                        }
                        
            except aiohttp.ClientError as e:
                error_message = f"❌ HTTP 요청 오류: {str(e)}"
                print(f"❌ {error_message}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": error_message
                        }
                    ]
                }
            except asyncio.TimeoutError:
                error_message = f"❌ 이메일 전송 시간 초과 ({CONFIG['email']['timeout']}초)"
                print(f"❌ {error_message}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": error_message
                        }
                    ]
                }
                
    except Exception as e:
        error_message = f"❌ 이메일 전송 중 예상치 못한 오류: {str(e)}"
        print(f"❌ {error_message}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_message
                }
            ]
        }

def _calculate_corporate_profit_amount(process_data: list, corporate_profit: dict) -> int:
    """
    기업이윤 금액 계산
    """
    try:
        # 기본 공정들의 합계 계산 (추가금액 제외)
        basic_total = 0
        for process in process_data:
            if isinstance(process, dict) and "items" in process:
                for item in process["items"]:
                    if isinstance(item, dict) and not item.get("isAdditional", False):
                        basic_total += item.get("totalPrice", 0)
        
        # 기업이윤 계산
        percentage = corporate_profit.get("percentage", 10)
        profit_amount = int(basic_total * (percentage / 100))
        
        print(f"💰 기업이윤 계산: 기본합계 {basic_total:,}원 × {percentage}% = {profit_amount:,}원")
        return profit_amount
        
    except Exception as e:
        print(f"⚠️ 기업이윤 계산 중 오류: {e}")
        return 0

@mcp.tool()
def test_connection() -> Dict[str, Any]:
    """
    MCP 서버 연결 테스트
    
    Returns:
        Dict[str, Any]: 서버 상태 정보
    """
    return {
        "content": [
            {
                "type": "text",
                "text": f"🔧 Estimate Email MCP 서버 연결 성공!\n\n📊 서버 정보:\n- 이름: {CONFIG['server']['name']}\n- 버전: {CONFIG['server']['version']}\n- 설명: {CONFIG['server']['description']}\n- Cloud Functions URL: {CLOUD_FUNCTIONS_URL}\n- 타임아웃: {CONFIG['email']['timeout']}초\n\n🛠️ 지원 도구:\n- send_estimate_email: 견적서 이메일 전송\n- test_connection: 연결 테스트\n- get_server_info: 서버 정보 조회"
            }
        ]
    }

@mcp.tool()
def get_server_info() -> Dict[str, Any]:
    """
    서버 정보 및 설정 조회
    
    Returns:
        Dict[str, Any]: 상세 서버 정보
    """
    info_text = f"""🔧 Estimate Email MCP 서버 상세 정보

📊 서버 설정:
- 이름: {CONFIG['server']['name']}
- 버전: {CONFIG['server']['version']}
- 호스트: {CONFIG['server']['host']}
- 포트: {CONFIG['server']['port']}

📧 이메일 설정:
- Cloud Functions URL: {CONFIG['cloud_functions']['send_estimate_pdf']}
- 타임아웃: {CONFIG['email']['timeout']}초
- 기본 제목 템플릿: {CONFIG['email']['subject_template']}

💰 기본 기업이윤:
- 비율: {CONFIG['email']['default_corporate_profit']['percentage']}%
- 표시 여부: {CONFIG['email']['default_corporate_profit']['isVisible']}

🛠️ 지원 기능:
- PDF 생성 및 첨부
- Gmail API를 통한 이메일 전송
- 기업이윤 자동 계산
- 에러 처리 및 로깅
"""
    
    return {
        "content": [
            {
                "type": "text",
                "text": info_text
            }
        ]
    }

if __name__ == "__main__":
    # Remote MCP 서버로 실행 (Claude Web에서 접근 가능)
    print("🚀 Estimate Email MCP 서버 시작...")
    print(f"📡 SSE 서버 주소: http://{CONFIG['server']['host']}:{CONFIG['server']['port']}/sse")
    print(f"🔧 지원 도구: send_estimate_email, test_connection, get_server_info")
    print(f"☁️ Cloud Functions: {CLOUD_FUNCTIONS_URL}")
    print()
    print("⏹️  서버를 중지하려면 Ctrl+C를 누르세요.")
    
    # SSE 방식으로 실행 (Claude Web 호환)
    mcp.run(
        transport="sse",
        host=CONFIG['server']['host'],
        port=CONFIG['server']['port'],
        log_level="info"
    ) 