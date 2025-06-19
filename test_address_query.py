#!/usr/bin/env python3
"""
주소 조회 테스트 스크립트
"""

import requests
import json
import time
import uuid

def test_address_query():
    """주소 조회 테스트"""
    
    # 서버 URL
    url = "http://localhost:8505/chat"
    
    # 테스트 메시지
    test_message = "주소 조회해줘"
    
    # 세션 ID 생성
    session_id = str(uuid.uuid4())
    
    # 요청 데이터
    data = {
        "message": test_message,
        "session_id": session_id
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Interior-Test-Client/1.0"
    }
    
    print(f"🧪 테스트 시작: '{test_message}'")
    print(f"📡 서버: {url}")
    print(f"🆔 세션 ID: {session_id}")
    print("-" * 50)
    
    try:
        # HTTP POST 요청
        response = requests.post(url, json=data, headers=headers, timeout=60)
        
        print(f"📊 응답 상태 코드: {response.status_code}")
        print(f"📝 응답 헤더: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ 성공! 응답:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
                # 응답 분석
                if 'response' in result:
                    print(f"\n📄 메시지: {result['response']}")
                if 'agent_status' in result:
                    print(f"🤖 에이전트 상태: {result['agent_status']}")
                if 'firebase_tools_used' in result:
                    print(f"🔥 Firebase 도구 사용: {result['firebase_tools_used']}")
                    
            except json.JSONDecodeError:
                print(f"📄 텍스트 응답: {response.text}")
        else:
            print(f"❌ 에러 {response.status_code}")
            print(f"📄 응답 내용: {response.text}")
            
    except requests.exceptions.ConnectionError:  # 오타 수정: ConnectinError -> ConnectionError
        print("❌ 서버 연결 실패 - 서버가 실행되지 않았을 수 있습니다")
    except requests.exceptions.Timeout:
        print("❌ 요청 타임아웃 - 서버 응답이 너무 느립니다")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")

def test_health():
    """서버 상태 확인"""
    try:
        response = requests.get("http://localhost:8505/health", timeout=10)
        print(f"🏥 헬스체크: {response.status_code}")
        if response.status_code == 200:
            print("✅ 서버 정상 작동")
            try:
                health_data = response.json()
                print(f"📊 상태 정보: {json.dumps(health_data, ensure_ascii=False, indent=2)}")
            except:
                pass
            return True
        else:
            print(f"⚠️ 서버 상태 이상: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 헬스체크 실패: {e}")
        return False

def test_firebase_direct():
    """Firebase MCP 직접 테스트"""
    print("\n3️⃣ Firebase MCP 직접 테스트...")
    
    url = "http://localhost:8505/firebase/tool"
    data = {
        "tool_name": "firestore_list_collections",
        "arguments": {}
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"🔥 Firebase 상태: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Firebase 연결 성공!")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ Firebase 연결 실패: {response.text}")
    except Exception as e:
        print(f"❌ Firebase 테스트 실패: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 Firebase MCP 주소 조회 테스트")
    print("=" * 60)
    
    # 1. 헬스체크
    print("\n1️⃣ 서버 상태 확인...")
    if not test_health():
        print("❌ 서버가 실행되지 않았습니다. python simple_api_server.py 를 실행하세요.")
        exit(1)
    
    # 2. Firebase 직접 테스트
    test_firebase_direct()
    
    # 3. 주소 조회 테스트
    print("\n4️⃣ 주소 조회 테스트...")
    time.sleep(2)  # 서버 안정화 대기
    test_address_query()
    
    print("\n" + "=" * 60)
    print("🏁 테스트 완료")
    print("=" * 60) 