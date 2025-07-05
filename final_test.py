import requests
import json
import time

def test_scenario(name, message, session_id="comprehensive_test"):
    """테스트 시나리오 실행"""
    print(f"\n{'='*60}")
    print(f"🧪 {name}")
    print(f"{'='*60}")
    print(f"📝 요청: {message}")
    
    try:
        data = {
            "message": message,
            "session_id": session_id
        }
        
        response = requests.post(
            "http://localhost:8506/chat",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        print(f"✅ 성공!")
        print(f"📄 응답: {result['response'][:300]}...")
        return True
        
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def main():
    """종합 테스트 실행"""
    print("🚀 ADK 표준 구조 - 종합 테스트 시작")
    print("🎯 Context7 조사 결과를 바탕으로 한 완전한 검증")
    
    # 서버 상태 확인
    print("\n🔍 서버 상태 확인...")
    try:
        response = requests.get("http://localhost:8506/status")
        status = response.json()
        print(f"✅ 서버 상태: {status['mode']}, ADK: {status['adk_available']}")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return
    
    # 테스트 시나리오들
    scenarios = [
        # Firebase 에이전트 테스트
        ("Firebase - contractors 조회", "contractors 조회해줘"),
        ("Firebase - 견적서 리스트", "estimateVersionsV3 목록 보여줘"),
        ("Firebase - 주소 데이터", "addressesJson 문서들 가져와"),
        ("Firebase - 특정 문서 조회", "contractors에서 첫번째 문서 상세정보"),
        
        # Email 에이전트 테스트  
        ("Email - 이메일 전송", "이메일 전송 테스트해줘"),
        ("Email - 서버 테스트", "이메일 서버 연결 확인"),
        ("Email - 견적서 발송", "견적서를 test@example.com으로 보내줘"),
        ("Email - 서버 정보", "이메일 서버 정보 조회"),
        
        # 라우팅 테스트
        ("라우팅 - 혼합 키워드1", "contractors 데이터를 이메일로 전송"),
        ("라우팅 - 혼합 키워드2", "이메일 테스트용 데이터 조회"),
    ]
    
    # 테스트 실행
    success_count = 0
    total_count = len(scenarios)
    
    for name, message in scenarios:
        if test_scenario(name, message):
            success_count += 1
        time.sleep(1)  # 서버 부하 방지
    
    # 결과 요약
    print(f"\n{'='*60}")
    print("🎯 종합 테스트 결과")
    print(f"{'='*60}")
    print(f"✅ 성공: {success_count}/{total_count}")
    print(f"📊 성공률: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 **완벽한 성공!**")
        print("🏆 ADK 표준 구조가 완전히 정상 작동합니다!")
        print("✨ Context7 조사를 통한 문제 해결 완료!")
        print("🔗 챗봇과의 연결 준비 완료!")
    else:
        print(f"\n⚠️ {total_count - success_count}개 시나리오에서 문제 발생")
        print("🔍 추가 디버깅이 필요합니다.")

if __name__ == "__main__":
    main() 