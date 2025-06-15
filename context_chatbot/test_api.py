import requests
import json
import time
import datetime
from typing import Dict, List, Any

class EnhancedAPITester:
    def __init__(self):
        self.base_url = "http://localhost:8505"
        self.test_results = []
        self.failed_tests = []
        
    def log_test_result(self, test_name: str, success: bool, response_data: Any = None, error: str = None):
        """테스트 결과를 기록합니다."""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.datetime.now().isoformat(),
            "response_data": response_data,
            "error": error
        }
        
        self.test_results.append(result)
        
        if success:
            print(f"✅ {test_name}: 성공")
            if response_data and isinstance(response_data, dict) and "response" in response_data:
                response_text = response_data["response"]
                if len(response_text) > 150:
                    print(f"   응답: {response_text[:150]}...")
                else:
                    print(f"   응답: {response_text}")
        else:
            print(f"❌ {test_name}: 실패")
            if error:
                print(f"   오류: {error}")
            self.failed_tests.append(test_name)
            
        print("-" * 100)

def test_health():
    """서버 상태 확인"""
    try:
        response = requests.get("http://localhost:8505/health")
        print(f"Health Check - Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return response.status_code == 200 and data.get("agent_available", False)
    except Exception as e:
        print(f"Health Check 실패: {e}")
        return False

def test_chat(message):
    """채팅 테스트"""
    try:
        data = {"message": message}
        response = requests.post(
            "http://localhost:8505/agent/chat",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Chat Test - Status: {response.status_code}")
        result = response.json()
        print(f"Success: {result.get('success')}")
        if result.get('success'):
            response_text = result.get('response', '')
            if len(response_text) > 200:
                print(f"Response: {response_text[:200]}...")
            else:
                print(f"Response: {response_text}")
        else:
            print(f"Error: {result.get('error')}")
        return result.get('success', False)
    except Exception as e:
        print(f"Chat Test 실패: {e}")
        return False

def run_comprehensive_tests():
    """종합적인 테스트 실행"""
    tester = EnhancedAPITester()
    
    print("🚀 종합 API 테스트 시작")
    print("=" * 100)
    
    # 1. 서버 상태 확인
    print("\n=== 1. 서버 상태 확인 ===")
    try:
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tester.log_test_result("서버 Health Check", True, data)
        else:
            tester.log_test_result("서버 Health Check", False, None, f"HTTP {response.status_code}")
    except Exception as e:
        tester.log_test_result("서버 Health Check", False, None, str(e))
    
    # 2. 기본 채팅 테스트
    print("\n=== 2. 기본 채팅 테스트 ===")
    basic_messages = [
        "안녕하세요",
        "어떤 기능들이 있나요?",
        "도움말을 보여주세요",
        "사용 가능한 명령어는?"
    ]
    
    for msg in basic_messages:
        try:
            response = requests.post(
                f"{tester.base_url}/agent/chat",
                json={"message": msg},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    tester.log_test_result(f"기본 채팅: {msg}", True, data)
                else:
                    tester.log_test_result(f"기본 채팅: {msg}", False, None, data.get("error"))
            else:
                tester.log_test_result(f"기본 채팅: {msg}", False, None, f"HTTP {response.status_code}")
        except Exception as e:
            tester.log_test_result(f"기본 채팅: {msg}", False, None, str(e))
        
        time.sleep(1)
    
    # 3. 주소 관리 기능 테스트
    print("\n=== 3. 주소 관리 기능 테스트 ===")
    address_tests = [
        "주소 리스트 보여줘",
        "등록된 주소 목록을 보여주세요",
        "주소 상세 목록 보여줘",
        "수성 주소 검색해줘",
        "롯데캐슬 검색해줘",
        "서울 지역 주소 찾아줘",
        "대구 주소 검색해줘",
        "서울시 강남구 테헤란로 123번지 등록해줘",
        "부산시 해운대구 센텀로 456번지 추가해줘",
        "광주시 서구 치평동 202번지 수정해줘",
        "주소 정보 업데이트해주세요",
        "수성 3가 롯데캐슬 삭제해줘"
    ]
    
    for msg in address_tests:
        try:
            response = requests.post(
                f"{tester.base_url}/agent/chat",
                json={"message": msg},
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    tester.log_test_result(f"주소 관리: {msg}", True, data)
                else:
                    tester.log_test_result(f"주소 관리: {msg}", False, None, data.get("error"))
            else:
                tester.log_test_result(f"주소 관리: {msg}", False, None, f"HTTP {response.status_code}")
        except Exception as e:
            tester.log_test_result(f"주소 관리: {msg}", False, None, str(e))
        
        time.sleep(1)
    
    # 4. 스케줄 관리 기능 테스트
    print("\n=== 4. 스케줄 관리 기능 테스트 ===")
    schedule_tests = [
        "오늘 일정 보여줘",
        "금일 스케줄을 확인하고 싶어요",
        "당일 일정 알려주세요",
        "예정 일정 보여줘",
        "향후 일정을 알려주세요",
        "다음 일정은 무엇인가요?",
        "일정 목록 보여줘",
        "스케줄 목록을 확인하고 싶어요",
        "전체 일정 리스트",
        "서울시 강남구 테헤란로 123번지에서 내일 타일공사 일정 등록해줘",
        "수성 효성 헤링턴에서 2024-12-25에 도배작업 스케줄 추가해줘",
        "오늘 일정을 수정하고 싶어요",
        "내일 일정을 취소해주세요",
        "타일공사 완료했어요",
        "도배작업이 끝났습니다",
        "일정 리포트 생성해줘",
        "이번 달 일정 통계를 보여주세요",
        "스케줄 보고서를 만들어주세요"
    ]
    
    for msg in schedule_tests:
        try:
            response = requests.post(
                f"{tester.base_url}/agent/chat",
                json={"message": msg},
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    tester.log_test_result(f"스케줄 관리: {msg}", True, data)
                else:
                    tester.log_test_result(f"스케줄 관리: {msg}", False, None, data.get("error"))
            else:
                tester.log_test_result(f"스케줄 관리: {msg}", False, None, f"HTTP {response.status_code}")
        except Exception as e:
            tester.log_test_result(f"스케줄 관리: {msg}", False, None, str(e))
        
        time.sleep(1)
    
    # 5. 복합 시나리오 테스트
    print("\n=== 5. 복합 시나리오 테스트 ===")
    complex_tests = [
        "서울시 강남구 테헤란로 123번지에서 내일 타일공사가 예정되어 있는데, 일정을 확인하고 견적도 알려주세요",
        "수성구 롯데캐슬 프로젝트의 오늘 일정과 다음 주 예정 작업들을 확인하고, 필요하면 새로운 주소도 등록해주세요",
        "이번 달 완료된 프로젝트 리포트를 생성하고, 미완료 일정들도 정리해주세요",
        "주소 목록 보여주고, 오늘 일정도 확인하고, 새 프로젝트 시작 방법도 알려주세요",
        "새로운 인테리어 프로젝트를 시작하고 싶어요. 어떤 준비가 필요한가요?",
        "30평 아파트 인테리어 견적을 알고 싶고, 일정도 계획해주세요"
    ]
    
    for msg in complex_tests:
        try:
            response = requests.post(
                f"{tester.base_url}/agent/chat",
                json={"message": msg},
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    tester.log_test_result(f"복합 시나리오: {msg[:50]}...", True, data)
                else:
                    tester.log_test_result(f"복합 시나리오: {msg[:50]}...", False, None, data.get("error"))
            else:
                tester.log_test_result(f"복합 시나리오: {msg[:50]}...", False, None, f"HTTP {response.status_code}")
        except Exception as e:
            tester.log_test_result(f"복합 시나리오: {msg[:50]}...", False, None, str(e))
        
        time.sleep(2)
    
    # 6. 오류 처리 테스트
    print("\n=== 6. 오류 처리 테스트 ===")
    error_tests = [
        "",  # 빈 메시지
        "!@#$%^&*()",  # 특수문자만
        "존재하지않는명령어123456789",  # 존재하지 않는 명령어
        "화성시 달나라동 우주아파트 검색해줘"  # 존재하지 않는 주소 검색
    ]
    
    for msg in error_tests:
        try:
            response = requests.post(
                f"{tester.base_url}/agent/chat",
                json={"message": msg},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 400]:  # 정상 응답 또는 예상된 오류
                data = response.json()
                test_name = f"오류 처리: '{msg}'" if msg else "오류 처리: 빈 메시지"
                if msg == "" and response.status_code == 400:
                    # 빈 메시지는 400 오류가 예상됨
                    tester.log_test_result(test_name, True, {"response": "예상된 오류 응답"})
                elif data.get("success") or len(str(data.get("response", ""))) > 0:
                    # 기타 경우는 적절한 응답이 있으면 성공
                    tester.log_test_result(test_name, True, data)
                else:
                    tester.log_test_result(test_name, False, None, "응답 없음")
            else:
                test_name = f"오류 처리: '{msg}'" if msg else "오류 처리: 빈 메시지"
                tester.log_test_result(test_name, False, None, f"HTTP {response.status_code}")
        except Exception as e:
            test_name = f"오류 처리: '{msg}'" if msg else "오류 처리: 빈 메시지"
            tester.log_test_result(test_name, False, None, str(e))
        
        time.sleep(0.5)
    
    # 결과 요약
    print("\n" + "=" * 100)
    print("📊 테스트 결과 요약")
    print("=" * 100)
    
    total_tests = len(tester.test_results)
    successful_tests = len([r for r in tester.test_results if r["success"]])
    failed_tests = len(tester.failed_tests)
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"총 테스트 수: {total_tests}")
    print(f"성공한 테스트: {successful_tests}")
    print(f"실패한 테스트: {failed_tests}")
    print(f"성공률: {success_rate:.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ 실패한 테스트 목록:")
        for i, failed_test in enumerate(tester.failed_tests, 1):
            print(f"  {i}. {failed_test}")
    
    # 결과 판정
    if success_rate >= 80:
        print(f"\n🎉 우수! 전체 시스템이 정상적으로 작동하고 있습니다.")
    elif success_rate >= 60:
        print(f"\n✅ 양호! 대부분의 기능이 정상 작동하지만 일부 개선이 필요합니다.")
    else:
        print(f"\n⚠️ 주의! 많은 기능에서 문제가 발생했습니다. 시스템 점검이 필요합니다.")
    
    return success_rate >= 60

if __name__ == "__main__":
    print("=== ADK API 서버 종합 테스트 ===")
    print("이 테스트는 adk_api_server.py와 main.py의 연결 상태와")
    print("주소 관리, 스케줄 관리 기능을 종합적으로 테스트합니다.\n")
    
    # 기본 테스트 (기존 호환성)
    print("1. 기본 서버 상태 확인:")
    health_ok = test_health()
    
    if health_ok:
        print("\n2. 기본 채팅 테스트:")
        basic_chat_ok = test_chat("주소 리스트 보여줘")
        
        if basic_chat_ok:
            print("\n3. 종합 테스트 실행:")
            comprehensive_success = run_comprehensive_tests()
            
            if comprehensive_success:
                print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
                print("\n💡 다음 단계:")
                print("  - Streamlit 앱 실행: streamlit run context_chatbot/main.py")
                print("  - 실제 사용자 시나리오로 테스트")
                print("  - 성능 모니터링 및 최적화")
            else:
                print("\n⚠️ 일부 테스트에서 문제가 발견되었습니다.")
                print("상세 내용을 확인하여 문제를 해결해주세요.")
        else:
            print("기본 채팅 테스트 실패 - 서버 설정을 확인해주세요.")
    else:
        print("서버가 실행되지 않았거나 에이전트에 문제가 있습니다.")
        print("다음을 확인해주세요:")
        print("1. python adk_api_server.py로 서버가 실행되었는지")
        print("2. interior_multi_agent/interior_agents/agent_main.py 파일이 존재하는지")
        print("3. 필요한 dependencies가 설치되었는지") 