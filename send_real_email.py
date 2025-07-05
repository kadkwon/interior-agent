import requests
import json

def send_real_email():
    """실제 이메일 전송 테스트"""
    
    print("📧 gncloud86@naver.com으로 실제 이메일 전송 테스트")
    print("=" * 60)
    
    # 실제 이메일 전송 요청
    message = """
    gncloud86@naver.com으로 테스트 견적서를 보내주세요.
    
    주소: 테스트 주소 (서울시 강남구 테스트동 123-456)
    
    공정 데이터:
    - 도배 공사: 30평, 100,000원
    - 마루 공사: 20평, 200,000원
    - 타일 공사: 15평, 150,000원
    
    총 금액: 450,000원
    """
    
    try:
        data = {
            "message": message,
            "session_id": "real_email_test"
        }
        
        response = requests.post(
            "http://localhost:8506/chat",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        print(f"✅ 응답 받음")
        print(f"📄 응답 내용:\n{result['response']}")
        
        # 응답에서 이메일 전송 성공 여부 확인
        if "전송" in result['response'] and "성공" in result['response']:
            print("\n🎉 이메일 전송 성공!")
        elif "오류" in result['response'] or "실패" in result['response']:
            print("\n❌ 이메일 전송 실패")
        else:
            print("\n⚠️ 이메일 전송 상태 확인 필요")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    send_real_email() 