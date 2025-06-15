import sys
import os
import time
import requests
import json
from datetime import datetime
from typing import Dict, Any

# context_chatbot 디렉토리를 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "context_chatbot"))

class StreamlitIntegrationTest:
    def __init__(self):
        self.adk_api_url = "http://localhost:8505"
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """테스트 결과 로깅"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} - {test_name}")
        if details:
            print(f"   세부사항: {details}")
        print("-" * 60)

    def test_adk_api_server_status(self):
        """ADK API 서버 상태 확인"""
        print("\n=== ADK API 서버 상태 확인 ===")
        
        try:
            response = requests.get(f"{self.adk_api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                details = f"Status: {data.get('status')}, Agent Available: {data.get('agent_available')}"
                self.log_result("ADK API 서버 Health Check", True, details)
                return data
            else:
                self.log_result("ADK API 서버 Health Check", False, f"HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log_result("ADK API 서버 Health Check", False, str(e))
            return None

    def test_chat_manager_imports(self):
        """ChatManager 임포트 테스트"""
        print("\n=== ChatManager 임포트 테스트 ===")
        
        try:
            from chat_manager import ChatManager
            self.log_result("ChatManager 임포트", True, "모듈 로드 성공")
            return ChatManager
        except Exception as e:
            self.log_result("ChatManager 임포트", False, str(e))
            return None

    def test_chat_manager_initialization(self, ChatManager):
        """ChatManager 초기화 테스트"""
        print("\n=== ChatManager 초기화 테스트 ===")
        
        if not ChatManager:
            self.log_result("ChatManager 초기화", False, "ChatManager 클래스가 없음")
            return None
            
        try:
            chat_manager = ChatManager()
            agent_type = getattr(chat_manager, 'agent_type', 'UNKNOWN')
            agent_name = getattr(chat_manager.agent, 'name', 'Unknown') if chat_manager.agent else 'None'
            
            details = f"에이전트 타입: {agent_type}, 에이전트 이름: {agent_name}"
            self.log_result("ChatManager 초기화", True, details)
            return chat_manager
        except Exception as e:
            self.log_result("ChatManager 초기화", False, str(e))
            return None

    def test_adk_api_connection_check(self, chat_manager):
        """ChatManager의 ADK API 연결 확인 테스트"""
        print("\n=== ChatManager ADK API 연결 확인 ===")
        
        if not chat_manager:
            self.log_result("ADK API 연결 확인", False, "ChatManager가 없음")
            return None
            
        try:
            # check_adk_api_connection 메서드 호출
            connection_status = chat_manager.check_adk_api_connection(test_chat=False)
            
            status = connection_status.get("status", "unknown")
            connected = connection_status.get("connected", False)
            
            details = f"Status: {status}, Connected: {connected}"
            success = status in ["healthy", "partial"] and connected
            
            self.log_result("ChatManager ADK API 연결 확인", success, details)
            return connection_status
        except Exception as e:
            self.log_result("ChatManager ADK API 연결 확인", False, str(e))
            return None

    def test_chat_manager_response(self, chat_manager):
        """ChatManager 응답 생성 테스트"""
        print("\n=== ChatManager 응답 생성 테스트 ===")
        
        if not chat_manager:
            self.log_result("ChatManager 응답 생성", False, "ChatManager가 없음")
            return
            
        test_messages = [
            "안녕하세요",
            "주소 리스트 보여줘",
            "오늘 일정 확인해주세요",
            "어떤 기능들이 있나요?"
        ]
        
        success_count = 0
        for i, message in enumerate(test_messages, 1):
            try:
                response = chat_manager.get_response(message)
                
                if response and len(response) > 0:
                    details = f"응답 길이: {len(response)}자, 내용: {response[:50]}..."
                    self.log_result(f"응답 테스트 {i}", True, details)
                    success_count += 1
                else:
                    self.log_result(f"응답 테스트 {i}", False, "빈 응답")
                    
            except Exception as e:
                self.log_result(f"응답 테스트 {i}", False, str(e))
                
            time.sleep(1)  # 서버 부하 방지
        
        overall_success = success_count >= len(test_messages) * 0.5  # 50% 이상 성공
        self.log_result("전체 응답 테스트", overall_success, f"{success_count}/{len(test_messages)} 성공")

    def test_agent_status_method(self, chat_manager):
        """ChatManager의 get_agent_status 메서드 테스트"""
        print("\n=== Agent Status 메서드 테스트 ===")
        
        if not chat_manager:
            self.log_result("Agent Status 조회", False, "ChatManager가 없음")
            return
            
        try:
            agent_status = chat_manager.get_agent_status()
            
            if isinstance(agent_status, dict):
                agent_type = agent_status.get("agent_type", "UNKNOWN")
                agent_available = agent_status.get("agent_available", False)
                
                details = f"Agent Type: {agent_type}, Available: {agent_available}"
                self.log_result("Agent Status 조회", True, details)
                
                # 상세 정보 출력
                print(f"   📊 에이전트 상태 상세:")
                for key, value in agent_status.items():
                    print(f"     - {key}: {value}")
                    
            else:
                self.log_result("Agent Status 조회", False, "잘못된 응답 형식")
                
        except Exception as e:
            self.log_result("Agent Status 조회", False, str(e))

    def test_direct_api_vs_chatmanager(self, chat_manager):
        """직접 API 호출과 ChatManager 비교 테스트"""
        print("\n=== API 직접 호출 vs ChatManager 비교 ===")
        
        test_message = "주소 리스트 보여줘"
        
        # 1. 직접 API 호출
        try:
            api_response = requests.post(
                f"{self.adk_api_url}/agent/chat",
                json={"message": test_message},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if api_response.status_code == 200:
                api_data = api_response.json()
                api_result = api_data.get("response", "") if api_data.get("success") else "API 오류"
                api_success = True
            else:
                api_result = f"HTTP {api_response.status_code}"
                api_success = False
                
        except Exception as e:
            api_result = str(e)
            api_success = False
        
        # 2. ChatManager를 통한 호출
        if chat_manager:
            try:
                cm_result = chat_manager.get_response(test_message)
                cm_success = bool(cm_result and len(cm_result) > 0)
            except Exception as e:
                cm_result = str(e)
                cm_success = False
        else:
            cm_result = "ChatManager 없음"
            cm_success = False
        
        # 결과 비교
        both_success = api_success and cm_success
        
        details = f"API 직접호출: {'성공' if api_success else '실패'}, ChatManager: {'성공' if cm_success else '실패'}"
        self.log_result("API vs ChatManager 비교", both_success, details)
        
        print(f"   📝 API 직접 호출 결과: {api_result[:100]}...")
        print(f"   📝 ChatManager 결과: {cm_result[:100]}...")

    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        print("🚀 Streamlit-ADK API 연동 종합 테스트 시작")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # 1. ADK API 서버 상태 확인
        server_status = self.test_adk_api_server_status()
        
        # 2. ChatManager 임포트
        ChatManager = self.test_chat_manager_imports()
        
        # 3. ChatManager 초기화
        chat_manager = self.test_chat_manager_initialization(ChatManager)
        
        # 4. ADK API 연결 확인
        self.test_adk_api_connection_check(chat_manager)
        
        # 5. 응답 생성 테스트
        self.test_chat_manager_response(chat_manager)
        
        # 6. Agent Status 테스트
        self.test_agent_status_method(chat_manager)
        
        # 7. 직접 API vs ChatManager 비교
        self.test_direct_api_vs_chatmanager(chat_manager)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # 결과 요약
        print("\n" + "=" * 80)
        print("📊 테스트 결과 요약")
        print("=" * 80)
        
        success_count = len([r for r in self.test_results if r["success"]])
        total_count = len(self.test_results)
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        
        print(f"총 테스트: {total_count}")
        print(f"성공: {success_count}")
        print(f"실패: {total_count - success_count}")
        print(f"성공률: {success_rate:.1f}%")
        print(f"실행 시간: {duration.total_seconds():.1f}초")
        
        # 실패한 테스트 출력
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ 실패한 테스트들:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        
        # 추천 사항
        print(f"\n💡 추천 사항:")
        if server_status and server_status.get("agent_available"):
            print("  ✅ ADK API 서버가 정상 작동 중입니다.")
        else:
            print("  ⚠️ ADK API 서버 문제가 있습니다. 서버를 재시작해보세요.")
            
        if chat_manager and chat_manager.agent_type == "ADK_API":
            print("  ✅ ChatManager가 ADK API를 사용하고 있습니다.")
        else:
            print("  ⚠️ ChatManager가 ADK API를 사용하지 않습니다. 연결을 확인해보세요.")
        
        return success_rate >= 70  # 70% 이상 성공시 전체 성공으로 간주

def test_specific_functionality():
    """특정 기능 테스트"""
    print("\n🎯 특정 기능 테스트")
    print("=" * 50)
    
    # 주소 관리 기능 테스트
    address_tests = [
        "주소 리스트 보여줘",
        "수성 주소 검색해줘",
        "서울시 강남구 테헤란로 123번지 등록해줘",
        "주소 상세 목록 보여줘"
    ]
    
    # 스케줄 관리 기능 테스트
    schedule_tests = [
        "오늘 일정 보여줘",
        "예정 일정 보여줘",
        "일정 목록 보여줘",
        "일정 리포트 생성해줘"
    ]
    
    all_tests = address_tests + schedule_tests
    
    try:
        success_count = 0
        for i, test_msg in enumerate(all_tests, 1):
            try:
                response = requests.post(
                    "http://localhost:8505/agent/chat",
                    json={"message": test_msg},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        print(f"✅ 테스트 {i}: {test_msg}")
                        print(f"   응답: {data.get('response', '')[:100]}...")
                        success_count += 1
                    else:
                        print(f"❌ 테스트 {i}: {test_msg}")
                        print(f"   오류: {data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ 테스트 {i}: {test_msg}")
                    print(f"   HTTP 오류: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 테스트 {i}: {test_msg}")
                print(f"   예외: {str(e)}")
                
            time.sleep(1)
            print("-" * 40)
        
        print(f"\n📊 기능 테스트 결과: {success_count}/{len(all_tests)} 성공")
        
    except Exception as e:
        print(f"❌ 기능 테스트 중 오류: {e}")

if __name__ == "__main__":
    print("🏠 Streamlit-ADK API 연동 테스트")
    print("이 테스트는 context_chatbot/main.py와 adk_api_server.py 간의")
    print("연결 상태를 확인합니다.\n")
    
    # ADK API 서버 실행 확인
    try:
        requests.get("http://localhost:8505/health", timeout=3)
        print("✅ ADK API 서버가 실행 중입니다.\n")
    except:
        print("❌ ADK API 서버가 실행되지 않았습니다.")
        print("먼저 'python adk_api_server.py'로 서버를 실행해주세요.\n")
        exit(1)
    
    # 종합 테스트 실행
    integration_test = StreamlitIntegrationTest()
    overall_success = integration_test.run_comprehensive_test()
    
    # 특정 기능 테스트
    test_specific_functionality()
    
    if overall_success:
        print("\n🎉 전체 연동 테스트가 성공했습니다!")
        print("Streamlit 앱을 실행하여 실제 사용해보세요:")
        print("streamlit run context_chatbot/main.py")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다.")
        print("위의 추천 사항을 참고하여 문제를 해결해주세요.") 