#!/usr/bin/env python3
"""
🧪 Vertex AI Agent Engine 배포 테스트 스크립트
배포된 에이전트의 기능과 성능을 검증합니다
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path

# 현재 디렉터리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

try:
    import vertexai
    from vertexai import agent_engines
    from dotenv import load_dotenv
    
except ImportError as e:
    print(f"❌ 필수 패키지 누락: {e}")
    print("💡 다음 명령으로 설치하세요:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

class AgentTester:
    """
    배포된 Agent Engine 테스트 클래스
    """
    
    def __init__(self, resource_name: str = None):
        """
        테스터 초기화
        
        Args:
            resource_name: 테스트할 에이전트의 리소스 이름
        """
        self.resource_name = resource_name
        self.remote_agent = None
        self.test_results = {}
        
        # 환경설정 로드
        load_dotenv()
        
        # Vertex AI 초기화
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("AGENT_ENGINE_LOCATION", "us-central1")
        staging_bucket = f"gs://{project_id}-agent-staging"
        
        vertexai.init(
            project=project_id,
            location=location,
            staging_bucket=staging_bucket
        )
        
        print(f"🎯 Agent Engine 테스트 시작")
        print(f"   프로젝트: {project_id}")
        print(f"   지역: {location}")
    
    def list_deployed_agents(self):
        """
        배포된 모든 에이전트 목록 조회
        """
        print("\n📋 배포된 에이전트 목록 조회 중...")
        
        try:
            agents = agent_engines.list()
            
            if not agents:
                print("❌ 배포된 에이전트가 없습니다")
                return False
            
            print(f"✅ 총 {len(agents)}개의 에이전트 발견:")
            
            for i, agent in enumerate(agents, 1):
                resource_name = getattr(agent, 'resource_name', 'N/A')
                display_name = getattr(agent, 'display_name', 'N/A')
                
                print(f"   {i}. {display_name}")
                print(f"      리소스: {resource_name}")
            
            # 첫 번째 에이전트를 기본 테스트 대상으로 설정
            if not self.resource_name and agents:
                self.resource_name = getattr(agents[0], 'resource_name', None)
                print(f"\n🎯 테스트 대상 에이전트: {getattr(agents[0], 'display_name', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 에이전트 목록 조회 실패: {e}")
            return False
    
    def connect_to_agent(self):
        """
        특정 에이전트에 연결
        """
        if not self.resource_name:
            print("❌ 에이전트 리소스 이름이 필요합니다")
            return False
        
        print(f"\n🔗 에이전트 연결 중: {self.resource_name}")
        
        try:
            self.remote_agent = agent_engines.get(self.resource_name)
            print("✅ 에이전트 연결 성공")
            return True
            
        except Exception as e:
            print(f"❌ 에이전트 연결 실패: {e}")
            return False
    
    def test_basic_functionality(self):
        """
        기본 기능 테스트
        """
        print("\n🧪 기본 기능 테스트 실행 중...")
        
        if not self.remote_agent:
            print("❌ 에이전트에 연결되지 않았습니다")
            return False
        
        test_queries = [
            "안녕하세요! 인테리어 프로젝트 도움이 필요합니다.",
            "현재 등록된 모든 현장 주소를 보여주세요.",
            "Firebase 프로젝트 정보를 확인해주세요.",
            "새로운 현장을 등록하고 싶습니다. 도와주세요."
        ]
        
        success_count = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 테스트 {i}: {query[:30]}...")
            
            try:
                start_time = time.time()
                response = self.remote_agent.query(query)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_length = len(str(response))
                
                print(f"✅ 응답 성공 (시간: {response_time:.2f}초, 길이: {response_length}자)")
                print(f"   응답 미리보기: {str(response)[:100]}...")
                
                # 테스트 결과 저장
                self.test_results[f"test_{i}"] = {
                    "query": query,
                    "success": True,
                    "response_time": response_time,
                    "response_length": response_length,
                    "response_preview": str(response)[:200]
                }
                
                success_count += 1
                
            except Exception as e:
                print(f"❌ 응답 실패: {e}")
                
                self.test_results[f"test_{i}"] = {
                    "query": query,
                    "success": False,
                    "error": str(e)
                }
        
        success_rate = (success_count / len(test_queries)) * 100
        print(f"\n📊 기본 기능 테스트 결과: {success_count}/{len(test_queries)} 성공 ({success_rate:.1f}%)")
        
        return success_rate > 50  # 50% 이상 성공하면 통과
    
    def test_firebase_integration(self):
        """
        Firebase 연동 기능 테스트
        """
        print("\n🔥 Firebase 연동 테스트 실행 중...")
        
        if not self.remote_agent:
            print("❌ 에이전트에 연결되지 않았습니다")
            return False
        
        firebase_queries = [
            "Firebase 프로젝트 정보를 확인해주세요.",
            "Firestore 컬렉션 목록을 보여주세요.",
            "Firebase Storage에 있는 파일들을 나열해주세요.",
            "schedule 컬렉션에서 데이터를 조회해주세요."
        ]
        
        success_count = 0
        
        for i, query in enumerate(firebase_queries, 1):
            print(f"\n🔥 Firebase 테스트 {i}: {query[:40]}...")
            
            try:
                start_time = time.time()
                response = self.remote_agent.query(query)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # Firebase 관련 키워드 확인
                firebase_keywords = ["firebase", "firestore", "storage", "collection", "document"]
                response_str = str(response).lower()
                
                if any(keyword in response_str for keyword in firebase_keywords):
                    print(f"✅ Firebase 응답 성공 (시간: {response_time:.2f}초)")
                    success_count += 1
                else:
                    print(f"⚠️ Firebase 관련 응답 불분명")
                
            except Exception as e:
                print(f"❌ Firebase 테스트 실패: {e}")
        
        success_rate = (success_count / len(firebase_queries)) * 100
        print(f"\n🔥 Firebase 연동 테스트 결과: {success_count}/{len(firebase_queries)} 성공 ({success_rate:.1f}%)")
        
        return success_rate > 25  # 25% 이상 성공하면 통과 (Firebase 설정에 따라 다를 수 있음)
    
    def test_interior_agent_features(self):
        """
        인테리어 에이전트 특화 기능 테스트
        """
        print("\n🏠 인테리어 에이전트 기능 테스트 실행 중...")
        
        if not self.remote_agent:
            print("❌ 에이전트에 연결되지 않았습니다")
            return False
        
        interior_queries = [
            "서울시 강남구 테헤란로 123번지 현장을 등록하고 싶습니다.",
            "30평 거실 리모델링 비용을 계산해주세요.",
            "현재 진행 중인 모든 프로젝트 현황을 요약해주세요.",
            "공사 단계별 지급 계획을 만들어주세요."
        ]
        
        success_count = 0
        
        for i, query in enumerate(interior_queries, 1):
            print(f"\n🏠 인테리어 테스트 {i}: {query[:40]}...")
            
            try:
                start_time = time.time()
                response = self.remote_agent.query(query)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # 인테리어 관련 키워드 확인
                interior_keywords = ["현장", "리모델링", "비용", "계산", "프로젝트", "지급", "계획", "등록"]
                response_str = str(response).lower()
                
                if any(keyword in response_str for keyword in interior_keywords):
                    print(f"✅ 인테리어 기능 응답 성공 (시간: {response_time:.2f}초)")
                    success_count += 1
                else:
                    print(f"⚠️ 인테리어 관련 응답 불분명")
                
            except Exception as e:
                print(f"❌ 인테리어 기능 테스트 실패: {e}")
        
        success_rate = (success_count / len(interior_queries)) * 100
        print(f"\n🏠 인테리어 기능 테스트 결과: {success_count}/{len(interior_queries)} 성공 ({success_rate:.1f}%)")
        
        return success_rate > 50  # 50% 이상 성공하면 통과
    
    def performance_stress_test(self):
        """
        성능 및 부하 테스트
        """
        print("\n⚡ 성능 부하 테스트 실행 중...")
        
        if not self.remote_agent:
            print("❌ 에이전트에 연결되지 않았습니다")
            return False
        
        # 간단한 쿼리로 부하 테스트
        test_query = "안녕하세요!"
        num_requests = 5  # 테스트용으로 5회만 실행
        
        response_times = []
        success_count = 0
        
        print(f"📊 {num_requests}회 요청 테스트 시작...")
        
        for i in range(num_requests):
            try:
                start_time = time.time()
                response = self.remote_agent.query(test_query)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                success_count += 1
                
                print(f"   요청 {i+1}: {response_time:.2f}초")
                
            except Exception as e:
                print(f"   요청 {i+1}: 실패 - {e}")
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print(f"\n📊 성능 테스트 결과:")
            print(f"   성공률: {success_count}/{num_requests} ({(success_count/num_requests)*100:.1f}%)")
            print(f"   평균 응답 시간: {avg_time:.2f}초")
            print(f"   최소 응답 시간: {min_time:.2f}초")
            print(f"   최대 응답 시간: {max_time:.2f}초")
            
            # 성능 기준: 평균 응답 시간 10초 이하, 성공률 80% 이상
            performance_ok = avg_time <= 10.0 and (success_count/num_requests) >= 0.8
            
            if performance_ok:
                print("✅ 성능 테스트 통과")
            else:
                print("⚠️ 성능 개선 필요")
            
            return performance_ok
        else:
            print("❌ 모든 요청 실패")
            return False
    
    def generate_test_report(self):
        """
        테스트 결과 보고서 생성
        """
        print("\n📄 테스트 보고서 생성 중...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"agent_test_report_{timestamp}.json"
        
        report = {
            "test_timestamp": timestamp,
            "agent_resource_name": self.resource_name,
            "test_results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "successful_tests": len([r for r in self.test_results.values() if r.get("success", False)]),
                "average_response_time": sum([r.get("response_time", 0) for r in self.test_results.values()]) / max(len(self.test_results), 1)
            }
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 테스트 보고서 생성: {report_file}")
            return True
            
        except Exception as e:
            print(f"❌ 보고서 생성 실패: {e}")
            return False
    
    def run_all_tests(self):
        """
        모든 테스트 실행
        """
        print("🧪 Vertex AI Agent Engine 전체 테스트 시작")
        print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        test_steps = [
            ("배포된 에이전트 목록 조회", self.list_deployed_agents),
            ("에이전트 연결", self.connect_to_agent),
            ("기본 기능 테스트", self.test_basic_functionality),
            ("Firebase 연동 테스트", self.test_firebase_integration),
            ("인테리어 에이전트 기능 테스트", self.test_interior_agent_features),
            ("성능 부하 테스트", self.performance_stress_test),
            ("테스트 보고서 생성", self.generate_test_report),
        ]
        
        passed_tests = 0
        
        for i, (test_name, test_func) in enumerate(test_steps, 1):
            print(f"\n{'='*60}")
            print(f"🧪 {i}단계: {test_name}")
            print('='*60)
            
            if test_func():
                print(f"✅ {i}단계 통과: {test_name}")
                passed_tests += 1
            else:
                print(f"❌ {i}단계 실패: {test_name}")
                
                # 중요한 테스트 실패 시 중단 여부 결정
                if i <= 2:  # 에이전트 목록 조회, 연결 실패 시 중단
                    print("💡 기본 연결에 실패했습니다. 테스트를 중단합니다.")
                    break
        
        # 최종 결과
        total_tests = len(test_steps)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"\n{'='*60}")
        print("🎯 최종 테스트 결과")
        print('='*60)
        print(f"📊 통과 테스트: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 70:
            print("🎉 전체 테스트 성공! 에이전트가 정상적으로 작동합니다.")
            return True
        elif success_rate >= 40:
            print("⚠️ 부분 성공. 일부 기능에 문제가 있을 수 있습니다.")
            return True
        else:
            print("❌ 테스트 실패. 에이전트 설정을 확인하세요.")
            return False

def main():
    """
    메인 실행 함수
    """
    parser = argparse.ArgumentParser(
        description="Vertex AI Agent Engine 배포 테스트 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
    # 자동으로 에이전트 찾아서 테스트
    python test_deployment.py
    
    # 특정 에이전트 테스트
    python test_deployment.py --resource-name "projects/.../reasoningEngines/..."
    
    # 기본 기능만 테스트
    python test_deployment.py --basic-only
        """
    )
    
    parser.add_argument(
        '--resource-name', '-r',
        help='테스트할 에이전트의 리소스 이름'
    )
    
    parser.add_argument(
        '--basic-only',
        action='store_true',
        help='기본 기능만 테스트 (빠른 검증)'
    )
    
    args = parser.parse_args()
    
    # 테스트 실행
    tester = AgentTester(args.resource_name)
    
    if args.basic_only:
        # 기본 테스트만 실행
        success = (
            tester.list_deployed_agents() and
            tester.connect_to_agent() and
            tester.test_basic_functionality()
        )
    else:
        # 전체 테스트 실행
        success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 