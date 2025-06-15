import requests
import json
import time
import datetime
from typing import Dict, List, Any

class ComprehensiveTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8505"
        self.test_results = []
        self.failed_tests = []
        
    def log_test_result(self, test_name: str, success: bool, response_data: Any = None, error: str = None):
        """테스트 결과를 로깅합니다."""
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
            if response_data:
                if isinstance(response_data, dict) and "response" in response_data:
                    print(f"   응답: {response_data['response'][:100]}...")
                elif isinstance(response_data, str):
                    print(f"   응답: {response_data[:100]}...")
        else:
            print(f"❌ {test_name}: 실패")
            if error:
                print(f"   오류: {error}")
            self.failed_tests.append(test_name)
            
        print("-" * 80)

    def test_server_health(self):
        """1. 서버 상태 확인 테스트"""
        print("\n=== 1. 서버 상태 확인 테스트 ===")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test_result(
                    "서버 Health Check", 
                    True, 
                    {
                        "status": data.get("status"),
                        "agent_available": data.get("agent_available"),
                        "agent_name": data.get("agent_name"),
                        "tools_count": data.get("tools_count")
                    }
                )
                return True
            else:
                self.log_test_result("서버 Health Check", False, None, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("서버 Health Check", False, None, str(e))
            return False

    def test_basic_chat(self):
        """2. 기본 채팅 연결 테스트"""
        print("\n=== 2. 기본 채팅 연결 테스트 ===")
        
        test_messages = [
            "안녕하세요",
            "도움이 필요해요",
            "어떤 기능들이 있나요?",
            "주요 기능 설명해주세요"
        ]
        
        success_count = 0
        for i, message in enumerate(test_messages, 1):
            try:
                response = requests.post(
                    f"{self.base_url}/agent/chat",
                    json={"message": message},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.log_test_result(f"기본 채팅 {i}", True, data.get("response"))
                        success_count += 1
                    else:
                        self.log_test_result(f"기본 채팅 {i}", False, None, data.get("error"))
                else:
                    self.log_test_result(f"기본 채팅 {i}", False, None, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test_result(f"기본 채팅 {i}", False, None, str(e))
                
            time.sleep(1)  # 서버 부하 방지
        
        return success_count == len(test_messages)

    def test_address_management(self):
        """3. 주소 관리 기능 테스트"""
        print("\n=== 3. 주소 관리 기능 테스트 ===")
        
        address_tests = [
            # 주소 조회
            {
                "name": "주소 목록 조회 1",
                "message": "주소 리스트 보여줘",
                "expect_success": True
            },
            {
                "name": "주소 목록 조회 2", 
                "message": "등록된 주소 목록을 보여주세요",
                "expect_success": True
            },
            {
                "name": "주소 상세 조회",
                "message": "주소 상세 목록 보여줘",
                "expect_success": True
            },
            
            # 주소 검색
            {
                "name": "주소 검색 - 수성",
                "message": "수성 주소 검색해줘",
                "expect_success": True
            },
            {
                "name": "주소 검색 - 롯데캐슬",
                "message": "롯데캐슬 검색해줘",
                "expect_success": True
            },
            {
                "name": "주소 검색 - 서울",
                "message": "서울 지역 주소 찾아줘",
                "expect_success": True
            },
            
            # 주소 등록
            {
                "name": "주소 등록 요청",
                "message": "서울시 강남구 테헤란로 123번지 등록해줘",
                "expect_success": True
            },
            {
                "name": "주소 추가 요청",
                "message": "부산시 해운대구 센텀로 456번지 추가해줘",
                "expect_success": True
            },
            
            # 주소 수정
            {
                "name": "주소 수정 요청",
                "message": "광주시 서구 치평동 202번지 수정해줘",
                "expect_success": True
            },
            
            # 주소 삭제
            {
                "name": "주소 삭제 요청",
                "message": "수성 3가 롯데캐슬 삭제해줘",
                "expect_success": True
            }
        ]
        
        return self._run_test_group(address_tests, "주소 관리")

    def test_schedule_management(self):
        """4. 스케줄 관리 기능 테스트"""
        print("\n=== 4. 스케줄 관리 기능 테스트 ===")
        
        schedule_tests = [
            # 스케줄 조회
            {
                "name": "오늘 일정 조회",
                "message": "오늘 일정 보여줘",
                "expect_success": True
            },
            {
                "name": "금일 스케줄 조회",
                "message": "금일 스케줄을 확인하고 싶어요",
                "expect_success": True
            },
            {
                "name": "예정된 일정 조회",
                "message": "예정 일정 보여줘",
                "expect_success": True
            },
            {
                "name": "향후 스케줄 조회",
                "message": "향후 일정을 알려주세요",
                "expect_success": True
            },
            
            # 스케줄 목록
            {
                "name": "일정 목록 전체",
                "message": "일정 목록 보여줘",
                "expect_success": True
            },
            {
                "name": "스케줄 리스트",
                "message": "스케줄 목록을 확인하고 싶어요",
                "expect_success": True
            },
            
            # 스케줄 등록
            {
                "name": "일정 등록 요청",
                "message": "서울시 강남구 테헤란로 123번지에서 내일 타일공사 일정 등록해줘",
                "expect_success": True
            },
            {
                "name": "스케줄 추가 요청",
                "message": "수성 효성 헤링턴에서 2024-12-25에 도배작업 스케줄 추가해줘",
                "expect_success": True
            },
            
            # 스케줄 수정/삭제
            {
                "name": "일정 수정 요청",
                "message": "오늘 일정을 수정하고 싶어요",
                "expect_success": True
            },
            {
                "name": "일정 삭제 요청",
                "message": "내일 일정을 취소해주세요",
                "expect_success": True
            },
            
            # 스케줄 완료
            {
                "name": "일정 완료 처리",
                "message": "타일공사 완료했어요",
                "expect_success": True
            },
            
            # 스케줄 리포트
            {
                "name": "일정 리포트 생성",
                "message": "일정 리포트 생성해줘",
                "expect_success": True
            },
            {
                "name": "통계 보고서 요청",
                "message": "이번 달 일정 통계를 보여주세요",
                "expect_success": True
            }
        ]
        
        return self._run_test_group(schedule_tests, "스케줄 관리")

    def test_complex_scenarios(self):
        """5. 복합 시나리오 테스트"""
        print("\n=== 5. 복합 시나리오 테스트 ===")
        
        complex_tests = [
            {
                "name": "종합 상황 1",
                "message": "서울시 강남구 테헤란로 123번지에서 내일 타일공사가 예정되어 있는데, 일정을 확인하고 견적도 알려주세요",
                "expect_success": True
            },
            {
                "name": "종합 상황 2", 
                "message": "수성구 롯데캐슬 프로젝트의 오늘 일정과 다음 주 예정 작업들을 확인하고, 필요하면 새로운 주소도 등록해주세요",
                "expect_success": True
            },
            {
                "name": "종합 상황 3",
                "message": "이번 달 완료된 프로젝트 리포트를 생성하고, 미완료 일정들도 정리해주세요",
                "expect_success": True
            },
            {
                "name": "다중 요청",
                "message": "주소 목록 보여주고, 오늘 일정도 확인하고, 새 프로젝트 시작 방법도 알려주세요",
                "expect_success": True
            }
        ]
        
        return self._run_test_group(complex_tests, "복합 시나리오")

    def _run_test_group(self, tests: List[Dict], group_name: str) -> bool:
        """테스트 그룹 실행"""
        success_count = 0
        
        for test in tests:
            try:
                response = requests.post(
                    f"{self.base_url}/agent/chat",
                    json={"message": test["message"]},
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.log_test_result(test["name"], True, data.get("response"))
                        success_count += 1
                    else:
                        self.log_test_result(test["name"], False, None, data.get("error"))
                else:
                    self.log_test_result(test["name"], False, None, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test_result(test["name"], False, None, str(e))
                
            time.sleep(1)  # 서버 부하 방지
        
        print(f"\n{group_name} 테스트 완료: {success_count}/{len(tests)} 성공")
        return success_count == len(tests)

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 종합 테스트 시작")
        print("=" * 100)
        
        start_time = datetime.datetime.now()
        
        # 테스트 실행
        test_results = {
            "서버 상태": self.test_server_health(),
            "기본 채팅": self.test_basic_chat(),
            "주소 관리": self.test_address_management(),
            "스케줄 관리": self.test_schedule_management(),
            "복합 시나리오": self.test_complex_scenarios()
        }
        
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        
        # 결과 요약
        print("\n" + "=" * 100)
        print("📊 테스트 결과 요약")
        print("=" * 100)
        
        total_success = sum(test_results.values())
        total_tests = len(test_results)
        
        for test_name, success in test_results.items():
            status = "✅ 성공" if success else "❌ 실패"
            print(f"{test_name:<15}: {status}")
        
        print(f"\n총 테스트: {total_tests}")
        print(f"성공: {total_success}")
        print(f"실패: {total_tests - total_success}")
        print(f"성공률: {(total_success/total_tests)*100:.1f}%")
        print(f"실행 시간: {duration.total_seconds():.1f}초")
        
        if self.failed_tests:
            print(f"\n❌ 실패한 테스트들:")
            for failed in self.failed_tests:
                print(f"  - {failed}")
        
        return total_success == total_tests

if __name__ == "__main__":
    print("🏠 인테리어 프로젝트 AI 어시스턴트 - 종합 테스트")
    print("이 테스트는 adk_api_server.py와 main.py의 연결 상태와")
    print("주소 관리, 스케줄 관리 기능을 종합적으로 테스트합니다.\n")
    
    # 서버 실행 여부 확인
    try:
        requests.get("http://localhost:8505/health", timeout=3)
        print("✅ ADK API 서버가 실행 중입니다.")
    except:
        print("❌ ADK API 서버가 실행되지 않았습니다.")
        print("먼저 'python adk_api_server.py'로 서버를 실행해주세요.")
        exit(1)
    
    # 테스트 실행
    test_suite = ComprehensiveTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 모든 테스트가 성공했습니다!")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다. 상세 내용을 확인해주세요.") 