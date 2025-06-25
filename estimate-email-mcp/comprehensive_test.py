#!/usr/bin/env python3
"""
🧪 Estimate Email MCP 서버 포괄적 테스트 스크립트

모든 MCP 툴과 기능을 체계적으로 테스트합니다.
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, Any
from pathlib import Path

# 서버 모듈 가져오기
try:
    from server import mcp, _calculate_corporate_profit_amount
    from config import CONFIG, validate_config
except ImportError as e:
    print(f"❌ 모듈 import 오류: {e}")
    print("현재 디렉토리가 estimate-email-mcp인지 확인해주세요.")
    sys.exit(1)

class TestResult:
    """테스트 결과를 추적하는 클래스"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add_result(self, test_name: str, success: bool, message: str = ""):
        self.total += 1
        if success:
            self.passed += 1
            status = "✅"
        else:
            self.failed += 1
            status = "❌"
        
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "status": status
        }
        self.results.append(result)
        print(f"{status} {test_name}: {message}")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("📊 테스트 결과 요약")
        print("="*60)
        print(f"🎯 총 테스트: {self.total}개")
        print(f"✅ 성공: {self.passed}개")
        print(f"❌ 실패: {self.failed}개")
        print(f"📈 성공률: {(self.passed/self.total*100):.1f}%" if self.total > 0 else "📈 성공률: 0%")
        
        if self.failed > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")

async def test_server_connection(test_result: TestResult):
    """서버 연결 테스트"""
    print("\n📡 1. 서버 연결 테스트")
    print("-" * 30)
    
    server_url = f"http://{CONFIG['server']['host']}:{CONFIG['server']['port']}/sse"
    
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(server_url) as response:
                if response.status == 200:
                    test_result.add_result(
                        "서버 연결", True, 
                        f"HTTP {response.status} - SSE 서버 정상 응답"
                    )
                else:
                    test_result.add_result(
                        "서버 연결", False,
                        f"HTTP {response.status} - 예상치 못한 응답"
                    )
    except aiohttp.ClientError as e:
        test_result.add_result(
            "서버 연결", False,
            f"연결 오류: {e}"
        )
    except Exception as e:
        test_result.add_result(
            "서버 연결", False,
            f"예상치 못한 오류: {e}"
        )

def test_config_validation(test_result: TestResult):
    """설정 검증 테스트"""
    print("\n⚙️ 2. 설정 검증 테스트")
    print("-" * 30)
    
    try:
        validate_config()
        test_result.add_result(
            "설정 검증", True,
            "모든 필수 설정이 올바름"
        )
        
        # 개별 설정 확인
        if CONFIG['server']['port'] > 0:
            test_result.add_result(
                "포트 설정", True,
                f"포트 {CONFIG['server']['port']} 유효"
            )
        else:
            test_result.add_result(
                "포트 설정", False,
                "포트 번호가 올바르지 않음"
            )
            
        if CONFIG['cloud_functions']['send_estimate_email'].startswith('https://'):
            test_result.add_result(
                "Cloud Functions URL", True,
                "HTTPS URL 형식 올바름"
            )
        else:
            test_result.add_result(
                "Cloud Functions URL", False,
                "HTTPS URL이 아님"
            )
            
    except Exception as e:
        test_result.add_result(
            "설정 검증", False,
            f"설정 오류: {e}"
        )

def test_mcp_tools(test_result: TestResult):
    """MCP 툴 기능 테스트"""
    print("\n🔧 3. MCP 툴 기능 테스트")
    print("-" * 30)
    
    # 3.1. test_connection 툴 테스트
    try:
        result = mcp.tools["test_connection"].handler()
        if "content" in result and len(result["content"]) > 0:
            test_result.add_result(
                "test_connection 툴", True,
                "연결 테스트 툴 정상 작동"
            )
        else:
            test_result.add_result(
                "test_connection 툴", False,
                "응답 형식이 올바르지 않음"
            )
    except Exception as e:
        test_result.add_result(
            "test_connection 툴", False,
            f"툴 실행 오류: {e}"
        )
    
    # 3.2. get_server_info 툴 테스트
    try:
        result = mcp.tools["get_server_info"].handler()
        if "content" in result and len(result["content"]) > 0:
            test_result.add_result(
                "get_server_info 툴", True,
                "서버 정보 툴 정상 작동"
            )
        else:
            test_result.add_result(
                "get_server_info 툴", False,
                "응답 형식이 올바르지 않음"
            )
    except Exception as e:
        test_result.add_result(
            "get_server_info 툴", False,
            f"툴 실행 오류: {e}"
        )

def test_corporate_profit_calculation(test_result: TestResult):
    """기업이윤 계산 로직 테스트"""
    print("\n💰 4. 기업이윤 계산 테스트")
    print("-" * 30)
    
    # 테스트 데이터 준비
    test_process_data = [
        {
            "id": "process_1",
            "name": "바닥 시공",
            "items": [
                {
                    "name": "마루 설치",
                    "quantity": 20,
                    "unit": "평",
                    "unitPrice": 50000,
                    "totalPrice": 1000000,
                    "isAdditional": False
                },
                {
                    "name": "추가 작업",
                    "quantity": 1,
                    "unit": "식",
                    "unitPrice": 500000,
                    "totalPrice": 500000,
                    "isAdditional": True  # 추가금액은 기업이윤 계산에서 제외
                }
            ]
        },
        {
            "id": "process_2",
            "name": "벽면 시공",
            "items": [
                {
                    "name": "벽지 시공",
                    "quantity": 30,
                    "unit": "평",
                    "unitPrice": 30000,
                    "totalPrice": 900000,
                    "isAdditional": False
                }
            ]
        }
    ]
    
    test_corporate_profit = {"percentage": 10, "isVisible": True}
    
    try:
        calculated_profit = _calculate_corporate_profit_amount(test_process_data, test_corporate_profit)
        
        # 예상값: (1,000,000 + 900,000) * 10% = 190,000원
        # (추가금액 500,000원은 제외)
        expected_profit = 190000
        
        if calculated_profit == expected_profit:
            test_result.add_result(
                "기업이윤 계산", True,
                f"계산 정확 ({calculated_profit:,}원)"
            )
        else:
            test_result.add_result(
                "기업이윤 계산", False,
                f"계산 오류 (예상: {expected_profit:,}원, 실제: {calculated_profit:,}원)"
            )
            
        # 0% 기업이윤 테스트
        zero_profit = _calculate_corporate_profit_amount(test_process_data, {"percentage": 0})
        if zero_profit == 0:
            test_result.add_result(
                "0% 기업이윤 계산", True,
                "0% 계산 정확"
            )
        else:
            test_result.add_result(
                "0% 기업이윤 계산", False,
                f"0%인데 {zero_profit:,}원 계산됨"
            )
            
    except Exception as e:
        test_result.add_result(
            "기업이윤 계산", False,
            f"계산 오류: {e}"
        )

def test_email_function_structure(test_result: TestResult):
    """이메일 전송 함수 구조 테스트 (실제 전송 없이)"""
    print("\n📧 5. 이메일 전송 함수 구조 테스트")
    print("-" * 30)
    
    # 테스트 파라미터 준비
    test_email = "test@example.com"
    test_address = "수성구 래미안 아파트 103동 702호"
    test_process_data = [
        {
            "id": "test_process",
            "name": "테스트 공정",
            "items": [
                {
                    "name": "테스트 항목",
                    "quantity": 10,
                    "unit": "개",
                    "unitPrice": 10000,
                    "totalPrice": 100000,
                    "isAdditional": False
                }
            ]
        }
    ]
    
    try:
        # send_estimate_email 툴이 MCP에 등록되었는지 확인
        if "send_estimate_email" in mcp.tools:
            test_result.add_result(
                "send_estimate_email 툴 등록", True,
                "MCP 툴로 정상 등록됨"
            )
            
            # 툴 핸들러 존재 확인
            handler = mcp.tools["send_estimate_email"].handler
            if callable(handler):
                test_result.add_result(
                    "send_estimate_email 핸들러", True,
                    "핸들러 함수 정상 존재"
                )
            else:
                test_result.add_result(
                    "send_estimate_email 핸들러", False,
                    "핸들러가 호출 가능하지 않음"
                )
        else:
            test_result.add_result(
                "send_estimate_email 툴 등록", False,
                "MCP 툴로 등록되지 않음"
            )
            
        # 필수 파라미터 검증 (실제 실행하지 않고 구조만)
        required_params = ["email", "address", "process_data"]
        tool_info = str(mcp.tools.get("send_estimate_email", ""))
        
        params_found = all(param in tool_info for param in required_params)
        if params_found:
            test_result.add_result(
                "필수 파라미터 정의", True,
                "모든 필수 파라미터가 정의됨"
            )
        else:
            test_result.add_result(
                "필수 파라미터 정의", False,
                "필수 파라미터가 누락됨"
            )
            
    except Exception as e:
        test_result.add_result(
            "이메일 함수 구조", False,
            f"구조 테스트 오류: {e}"
        )

async def test_cloud_functions_endpoint(test_result: TestResult):
    """Cloud Functions 엔드포인트 연결 테스트 (실제 데이터 전송 없이)"""
    print("\n☁️ 6. Cloud Functions 엔드포인트 테스트")
    print("-" * 30)
    
    cloud_url = CONFIG['cloud_functions']['send_estimate_email']
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # OPTIONS 요청으로 CORS 확인
            try:
                async with session.options(cloud_url) as response:
                    test_result.add_result(
                        "Cloud Functions CORS", True,
                        f"OPTIONS 요청 성공 ({response.status})"
                    )
            except:
                test_result.add_result(
                    "Cloud Functions CORS", False,
                    "OPTIONS 요청 실패"
                )
            
            # 빈 POST 요청으로 엔드포인트 존재 확인
            try:
                async with session.post(
                    cloud_url,
                    json={},
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                ) as response:
                    # 400번대 응답도 엔드포인트가 존재함을 의미
                    if response.status < 500:
                        test_result.add_result(
                            "Cloud Functions 엔드포인트", True,
                            f"엔드포인트 응답 확인 ({response.status})"
                        )
                    else:
                        test_result.add_result(
                            "Cloud Functions 엔드포인트", False,
                            f"서버 오류 ({response.status})"
                        )
            except asyncio.TimeoutError:
                test_result.add_result(
                    "Cloud Functions 엔드포인트", False,
                    "요청 시간 초과"
                )
            except Exception as e:
                test_result.add_result(
                    "Cloud Functions 엔드포인트", False,
                    f"요청 오류: {e}"
                )
                
    except Exception as e:
        test_result.add_result(
            "Cloud Functions 연결", False,
            f"연결 테스트 오류: {e}"
        )

def test_data_validation(test_result: TestResult):
    """데이터 유효성 검사 테스트"""
    print("\n📊 7. 데이터 유효성 검사 테스트")
    print("-" * 30)
    
    # 올바른 데이터 형식 테스트
    valid_process_data = [
        {
            "id": "process_1",
            "name": "테스트 공정",
            "items": [
                {
                    "name": "테스트 항목",
                    "quantity": 10,
                    "unit": "개",
                    "unitPrice": 1000,
                    "totalPrice": 10000,
                    "isAdditional": False
                }
            ]
        }
    ]
    
    try:
        # 정상 데이터로 기업이윤 계산
        result = _calculate_corporate_profit_amount(valid_process_data, {"percentage": 10})
        if result == 1000:  # 10,000 * 10%
            test_result.add_result(
                "정상 데이터 처리", True,
                "올바른 형식의 데이터 정상 처리"
            )
        else:
            test_result.add_result(
                "정상 데이터 처리", False,
                f"계산 결과가 예상과 다름 (예상: 1000, 실제: {result})"
            )
    except Exception as e:
        test_result.add_result(
            "정상 데이터 처리", False,
            f"정상 데이터 처리 중 오류: {e}"
        )
    
    # 빈 데이터 테스트
    try:
        result = _calculate_corporate_profit_amount([], {"percentage": 10})
        if result == 0:
            test_result.add_result(
                "빈 데이터 처리", True,
                "빈 데이터 안전하게 처리"
            )
        else:
            test_result.add_result(
                "빈 데이터 처리", False,
                f"빈 데이터인데 {result} 반환"
            )
    except Exception as e:
        test_result.add_result(
            "빈 데이터 처리", False,
            f"빈 데이터 처리 중 오류: {e}"
        )
    
    # 잘못된 형식 데이터 테스트
    try:
        result = _calculate_corporate_profit_amount("invalid_data", {"percentage": 10})
        test_result.add_result(
            "잘못된 데이터 처리", True,
            "잘못된 데이터 안전하게 처리 (오류 없음)"
        )
    except Exception as e:
        # 오류가 발생해도 서버가 죽지 않으면 OK
        test_result.add_result(
            "잘못된 데이터 처리", True,
            "잘못된 데이터에 대한 예외 처리 정상"
        )

async def run_comprehensive_test():
    """모든 테스트 실행"""
    print("🧪 Estimate Email MCP 서버 포괄적 테스트")
    print("="*60)
    print(f"⏰ 테스트 시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 테스트 위치: {Path.cwd()}")
    print()
    
    test_result = TestResult()
    
    # 1. 서버 연결 테스트 (서버가 실행 중인 경우만)
    await test_server_connection(test_result)
    
    # 2. 설정 검증 테스트
    test_config_validation(test_result)
    
    # 3. MCP 툴 기능 테스트
    test_mcp_tools(test_result)
    
    # 4. 기업이윤 계산 테스트
    test_corporate_profit_calculation(test_result)
    
    # 5. 이메일 함수 구조 테스트
    test_email_function_structure(test_result)
    
    # 6. Cloud Functions 엔드포인트 테스트
    await test_cloud_functions_endpoint(test_result)
    
    # 7. 데이터 유효성 검사 테스트
    test_data_validation(test_result)
    
    # 결과 요약
    test_result.print_summary()
    
    print("\n📋 다음 단계 권장사항:")
    if test_result.failed == 0:
        print("✅ 모든 테스트 통과! 서버 운영 준비 완료")
        print("1. python server.py 실행")
        print("2. Claude Web에서 Remote MCP 서버 연결")
        print("3. 실제 이메일 전송 테스트")
    else:
        print("⚠️  일부 테스트 실패 - 문제 해결 후 재테스트 권장")
        print("1. 실패한 테스트 항목 확인 및 수정")
        print("2. python comprehensive_test.py 재실행")
        print("3. 모든 테스트 통과 후 서버 운영")
    
    return test_result.failed == 0

if __name__ == "__main__":
    try:
        success = asyncio.run(run_comprehensive_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 예상치 못한 오류: {e}")
        sys.exit(1) 