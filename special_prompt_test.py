import requests
import json
import time
from datetime import datetime

def test_special_prompts():
    """특별한 프롬프트들을 테스트합니다"""
    
    base_url = "http://localhost:8505"
    
    # 특별한 프롬프트 테스트 모음
    special_tests = [
        # 주소 관리 - 복잡한 시나리오
        {
            "category": "주소 관리 - 복합 요청",
            "prompts": [
                "수성구에 있는 모든 주소를 검색하고, 그 중에서 효성 헤링턴 관련 주소의 상세 정보도 함께 보여주세요",
                "롯데캐슬 관련 주소들을 찾아서 리스트로 정리해주시고, 각 주소별 계약금액도 확인해주세요",
                "대구지역 프로젝트 현황을 파악하기 위해 대구 주소들을 검색하고 요약 보고서를 만들어주세요",
                "새로운 주소 '인천시 연수구 송도국제도시 123번지'를 등록하고, 감독자명은 '김철수'로 설정해주세요",
                "기존에 등록된 '수목원 삼성래미안' 주소 정보를 업데이트하고 싶은데, 계약금액을 5억원으로 변경해주세요"
            ]
        },
        
        # 스케줄 관리 - 복잡한 시나리오
        {
            "category": "스케줄 관리 - 복합 요청", 
            "prompts": [
                "오늘부터 다음 주까지의 모든 일정을 조회하고, 완료되지 않은 작업들만 따로 정리해서 보여주세요",
                "수성 효성 헤링턴에서 진행할 타일공사를 내일(2025-06-16) 오전 9시에 예약하고, 관련 일정 리포트도 생성해주세요",
                "이번 달 완료된 모든 작업들의 통계와 다음 달 예정 작업들을 비교 분석해주세요",
                "도원동 롯데캐슬에서 12월 25일 크리스마스에 도배작업 일정을 등록하고, 작업 완료 시간은 오후 6시로 설정해주세요",
                "개인 일정을 포함한 전체 스케줄에서 6월 중 가장 바쁜 날짜를 찾아서 일정 조정 제안을 해주세요"
            ]
        },
        
        # 프로젝트 관리 - 전체적인 워크플로우
        {
            "category": "프로젝트 관리 - 전체 워크플로우",
            "prompts": [
                "새로운 30평 아파트 인테리어 프로젝트를 시작합니다. 주소는 '서울시 서초구 반포동 456번지'이고, 예산은 7천만원입니다. 전체 프로젝트 계획을 세워주세요",
                "현재 진행 중인 모든 프로젝트의 진행상황을 점검하고, 지연된 작업이 있다면 일정 재조정 방안을 제시해주세요",
                "수성구 지역 프로젝트들의 월별 매출 분석과 내년도 사업 계획을 위한 기초 자료를 준비해주세요",
                "고객 만족도 향상을 위해 완료된 프로젝트들을 분석하고, 개선점과 베스트 프랙티스를 도출해주세요"
            ]
        },
        
        # 데이터 분석 및 리포트
        {
            "category": "데이터 분석 및 리포트",
            "prompts": [
                "지난 6개월간의 프로젝트 데이터를 분석해서 가장 수익성이 높은 지역과 작업 유형을 찾아주세요",
                "주소별 프로젝트 완료율과 평균 소요 시간을 계산해서 효율성 개선 방안을 제안해주세요",
                "Firebase에 저장된 모든 데이터를 종합해서 월간 사업 현황 보고서를 작성해주세요",
                "예정된 일정들을 기반으로 다음 분기 인력 배치 계획과 자재 발주 스케줄을 최적화해주세요"
            ]
        },
        
        # 문제 해결 및 최적화
        {
            "category": "문제 해결 및 최적화",
            "prompts": [
                "중복된 주소가 있는지 확인하고, 발견되면 자동으로 정리해주세요",
                "스케줄 충돌이 있는 날짜들을 찾아서 해결 방안을 제시해주세요",
                "데이터 무결성 검사를 수행하고, 문제가 있는 레코드들을 수정해주세요",
                "시스템 성능 최적화를 위한 데이터 정리 작업을 실행해주세요"
            ]
        }
    ]
    
    print("🎯 특별 프롬프트 테스트 시작")
    print("=" * 100)
    
    total_tests = 0
    successful_tests = 0
    
    for test_category in special_tests:
        category_name = test_category["category"]
        prompts = test_category["prompts"]
        
        print(f"\n=== {category_name} ===")
        
        category_success = 0
        
        for i, prompt in enumerate(prompts, 1):
            total_tests += 1
            
            try:
                print(f"\n🔍 테스트 {i}: {prompt[:80]}...")
                
                response = requests.post(
                    f"{base_url}/agent/chat",
                    json={"message": prompt},
                    headers={"Content-Type": "application/json"},
                    timeout=30  # 복잡한 요청이므로 타임아웃 증가
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        response_text = data.get("response", "")
                        
                        # 응답 품질 평가
                        quality_score = evaluate_response_quality(prompt, response_text)
                        
                        print(f"✅ 성공 (품질: {quality_score}/5)")
                        print(f"   📝 응답 길이: {len(response_text)}자")
                        print(f"   📋 응답 미리보기: {response_text[:200]}...")
                        
                        if quality_score >= 3:
                            successful_tests += 1
                            category_success += 1
                        
                        # 도구 사용 여부 확인
                        if "tool_used" in data:
                            print(f"   🔧 사용된 도구: {data['tool_used']}")
                            
                    else:
                        print(f"❌ 실패: {data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ HTTP 오류: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 예외 발생: {e}")
            
            print("-" * 80)
            time.sleep(2)  # 서버 부하 방지
        
        print(f"\n📊 {category_name} 결과: {category_success}/{len(prompts)} 성공")
    
    # 전체 결과 요약
    print("\n" + "=" * 100)
    print("📊 특별 프롬프트 테스트 결과 요약")
    print("=" * 100)
    
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"총 테스트: {total_tests}")
    print(f"성공: {successful_tests}")
    print(f"실패: {total_tests - successful_tests}")
    print(f"성공률: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 우수! AI 에이전트가 복잡한 요청들을 매우 잘 처리하고 있습니다.")
    elif success_rate >= 60:
        print("\n✅ 양호! 대부분의 복잡한 요청을 처리할 수 있지만 일부 개선이 필요합니다.")
    else:
        print("\n⚠️ 주의! 복잡한 요청 처리에서 문제가 많습니다. 시스템 점검이 필요합니다.")
    
    return success_rate >= 60

def evaluate_response_quality(prompt, response):
    """응답 품질을 평가합니다 (1-5점)"""
    
    score = 1  # 기본 점수
    
    # 길이 검사 (너무 짧거나 길지 않은지)
    if 50 <= len(response) <= 2000:
        score += 1
    
    # 구조화된 응답인지 확인
    structured_indicators = ["**", "📋", "💡", "🔧", "✅", "1️⃣", "2️⃣", "•", "-"]
    if any(indicator in response for indicator in structured_indicators):
        score += 1
    
    # 도구 실행 결과가 포함되어 있는지
    tool_indicators = ["결과:", "status", "success", "addresses", "schedules", "message"]
    if any(indicator in response for indicator in tool_indicators):
        score += 1
    
    # 가이드나 설명이 포함되어 있는지
    guide_indicators = ["가이드", "방법", "예시", "단계", "필요한", "확인"]
    if any(indicator in response for indicator in guide_indicators):
        score += 1
    
    return min(score, 5)  # 최대 5점

def test_edge_cases():
    """엣지 케이스 테스트"""
    
    print("\n🔬 엣지 케이스 테스트")
    print("=" * 50)
    
    edge_cases = [
        {
            "name": "매우 긴 프롬프트",
            "prompt": "인테리어 프로젝트 " * 50 + "에 대한 전체적인 분석과 향후 계획을 세워주세요"
        },
        {
            "name": "특수문자 포함",
            "prompt": "주소 검색: [서울시 강남구] & {테헤란로} @ 123번지 #신축 $고급 %완료"
        },
        {
            "name": "혼합 언어",
            "prompt": "Please show me 주소 리스트 and today's schedule 일정을 확인해주세요"
        },
        {
            "name": "숫자와 날짜 혼합",
            "prompt": "2025년 6월 15일부터 2025년 12월 31일까지 총 198일간의 프로젝트 123개에 대한 분석"
        },
        {
            "name": "모호한 요청",
            "prompt": "그거 있잖아... 뭐였지... 아무튼 저번에 했던 그 일정 말이야"
        }
    ]
    
    base_url = "http://localhost:8505"
    success_count = 0
    
    for case in edge_cases:
        try:
            print(f"\n🧪 {case['name']}: {case['prompt'][:50]}...")
            
            response = requests.post(
                f"{base_url}/agent/chat",
                json={"message": case['prompt']},
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ 처리 성공")
                    success_count += 1
                else:
                    print(f"⚠️ 처리 실패: {data.get('error', 'Unknown')}")
            else:
                print(f"❌ HTTP 오류: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 예외: {e}")
        
        time.sleep(1)
    
    print(f"\n📊 엣지 케이스 결과: {success_count}/{len(edge_cases)} 성공")
    
    return success_count >= len(edge_cases) * 0.6  # 60% 이상 성공

if __name__ == "__main__":
    print("🚀 특별 프롬프트 및 엣지 케이스 테스트")
    print("이 테스트는 복잡한 요청과 특수한 상황들을 처리하는 능력을 확인합니다.\n")
    
    # 서버 연결 확인
    try:
        response = requests.get("http://localhost:8505/health", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("agent_available"):
                print("✅ ADK API 서버 연결 확인됨\n")
            else:
                print("⚠️ 서버는 연결되지만 에이전트에 문제가 있습니다.\n")
        else:
            print("❌ 서버 응답 오류")
            exit(1)
    except:
        print("❌ ADK API 서버에 연결할 수 없습니다.")
        print("먼저 'python adk_api_server.py'로 서버를 실행해주세요.")
        exit(1)
    
    # 테스트 실행
    start_time = datetime.now()
    
    # 특별 프롬프트 테스트
    special_success = test_special_prompts()
    
    # 엣지 케이스 테스트
    edge_success = test_edge_cases()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # 최종 결과
    print("\n" + "=" * 100)
    print("🎯 최종 테스트 결과")
    print("=" * 100)
    
    print(f"특별 프롬프트 테스트: {'✅ 성공' if special_success else '❌ 실패'}")
    print(f"엣지 케이스 테스트: {'✅ 성공' if edge_success else '❌ 실패'}")
    print(f"전체 실행 시간: {duration.total_seconds():.1f}초")
    
    if special_success and edge_success:
        print("\n🏆 완벽! AI 에이전트가 모든 복잡한 상황을 훌륭하게 처리했습니다!")
        print("\n💡 시스템이 프로덕션 환경에 투입될 준비가 되었습니다.")
    elif special_success or edge_success:
        print("\n👍 양호! 대부분의 상황을 잘 처리하지만 일부 개선 여지가 있습니다.")
    else:
        print("\n🔧 개선 필요! 복잡한 요청 처리 능력을 향상시켜야 합니다.")
    
    print("\n📋 추가 권장사항:")
    print("  - 정기적인 성능 모니터링")
    print("  - 사용자 피드백 수집 및 반영") 
    print("  - 새로운 기능 추가 시 회귀 테스트")
    print("  - 데이터 백업 및 복구 계획 수립") 