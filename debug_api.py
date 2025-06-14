#!/usr/bin/env python3
"""
ADK API 서버 디버깅 스크립트
"""

import requests
import json
import time

def test_health():
    """Health Check 테스트"""
    print("=== Health Check 테스트 ===")
    try:
        response = requests.get("http://localhost:8505/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health Check 실패: {e}")
        return False

def test_chat(message="안녕하세요"):
    """Chat API 테스트"""
    print(f"\n=== Chat API 테스트: '{message}' ===")
    try:
        payload = {"message": message}
        response = requests.post(
            "http://localhost:8505/agent/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            json_response = response.json()
            print(f"Response: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
        except:
            print(f"Raw Response: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print("요청 시간 초과 (30초)")
        return False
    except Exception as e:
        print(f"Chat API 실패: {e}")
        return False

def main():
    print("🔍 ADK API 서버 디버깅 시작")
    
    # 1. Health Check
    health_ok = test_health()
    
    if not health_ok:
        print("❌ Health Check 실패 - 서버가 실행되지 않았습니다.")
        return
    
    # 2. 간단한 메시지 테스트
    test_messages = [
        "안녕하세요",
        "연결 테스트",
        "주소 리스트 보여줘"
    ]
    
    for msg in test_messages:
        success = test_chat(msg)
        if not success:
            print(f"❌ '{msg}' 테스트 실패")
        else:
            print(f"✅ '{msg}' 테스트 성공")
        
        time.sleep(1)  # 1초 대기
    
    print("\n🔍 디버깅 완료")

if __name__ == "__main__":
    main() 