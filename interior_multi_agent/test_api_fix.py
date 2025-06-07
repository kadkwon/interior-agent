#!/usr/bin/env python3
"""
Firebase API 형식 문제 테스트 및 수정 스크립트
로그에서 발견한 문제: "collection" -> "collectionPath"로 변경 필요
"""

import requests
import json
from datetime import datetime

def test_firebase_api_formats():
    """다양한 API 형식으로 테스트"""
    
    base_url = "https://us-central1-interior-one-click.cloudfunctions.net"
    endpoint = "/firestoreQueryCollection"
    url = f"{base_url}{endpoint}"
    
    print("🔍 Firebase API 형식 테스트")
    print("=" * 60)
    
    # 테스트할 다양한 형식들
    test_formats = [
        {
            "name": "현재 형식 (collection)",
            "payload": {"collection": "addresses", "limit": 3}
        },
        {
            "name": "수정된 형식 (collectionPath)", 
            "payload": {"collectionPath": "addresses", "limit": 3}
        },
        {
            "name": "MCP 형식 (collection_path)",
            "payload": {"collection_path": "addresses", "limit": 3}
        },
        {
            "name": "Firebase 표준 형식 (collectionId)",
            "payload": {"collectionId": "addresses", "limit": 3}
        }
    ]
    
    successful_format = None
    
    for i, test in enumerate(test_formats, 1):
        print(f"\n{i}️⃣ {test['name']} 테스트")
        print(f"   📦 페이로드: {json.dumps(test['payload'], ensure_ascii=False)}")
        
        try:
            response = requests.post(
                url,
                json=test['payload'],
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=10
            )
            
            print(f"   🌐 HTTP 상태: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    print(f"   ✅ 성공! JSON 응답:")
                    print(f"      📄 응답 크기: {len(json.dumps(json_response))} 바이트")
                    
                    # 문서 개수 확인
                    if 'documents' in str(json_response):
                        docs = json_response.get('data', {}).get('documents', [])
                        print(f"      📋 조회된 문서 수: {len(docs)}")
                    
                    successful_format = test
                    break
                    
                except json.JSONDecodeError:
                    print(f"   ❌ JSON 파싱 실패: {response.text[:100]}...")
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                print(f"      📝 응답: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ 타임아웃")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 연결 오류")
        except Exception as e:
            print(f"   💥 예외: {e}")
    
    return successful_format

def test_multiple_collections(successful_format):
    """성공한 형식으로 여러 컬렉션 테스트"""
    
    if not successful_format:
        print("❌ 성공한 형식이 없어서 다중 컬렉션 테스트를 건너뜁니다.")
        return
    
    print(f"\n🔍 다중 컬렉션 테스트 ({successful_format['name']})")
    print("=" * 60)
    
    base_url = "https://us-central1-interior-one-click.cloudfunctions.net"
    endpoint = "/firestoreQueryCollection" 
    url = f"{base_url}{endpoint}"
    
    # 테스트할 컬렉션들
    test_collections = ["addresses", "schedules", "customers", "users", "projects"]
    
    for collection in test_collections:
        print(f"\n🔸 '{collection}' 컬렉션 테스트")
        
        # 성공한 형식의 키 이름을 사용
        payload_key = list(successful_format['payload'].keys())[0]  # collection, collectionPath 등
        payload = {payload_key: collection, "limit": 2}
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                json_response = response.json()
                docs = json_response.get('data', {}).get('documents', [])
                print(f"   ✅ 성공: {len(docs)}개 문서 조회")
                
                # 첫 번째 문서의 필드 미리보기
                if docs:
                    first_doc = docs[0]
                    fields = list(first_doc.get('data', {}).keys())[:3]
                    print(f"   📄 필드 샘플: {fields}")
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   💥 오류: {e}")

def update_client_code(successful_format):
    """성공한 형식에 맞춰 클라이언트 코드 업데이트"""
    
    if not successful_format:
        print("❌ 성공한 형식이 없어서 코드 업데이트를 건너뜁니다.")
        return False
        
    print(f"\n🔧 클라이언트 코드 업데이트 필요")
    print("=" * 60)
    
    payload_key = list(successful_format['payload'].keys())[0]
    
    print(f"✅ 성공한 형식: {successful_format['name']}")
    print(f"🔑 사용할 키: '{payload_key}'")
    print(f"\n📝 수정이 필요한 파일:")
    print(f"   • interior_multi_agent/interior_agents/firebase_client.py")
    print(f"\n🔄 변경사항:")
    print(f"   현재: \"collection\": collection_path")
    print(f"   수정: \"{payload_key}\": collection_path")
    
    return True

def main():
    """메인 함수"""
    
    print("🚀 Firebase API 형식 문제 진단 및 수정")
    print(f"🔗 대상 URL: https://us-central1-interior-one-click.cloudfunctions.net/firestoreQueryCollection")
    print(f"🕐 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 다양한 형식으로 테스트
        successful_format = test_firebase_api_formats()
        
        # 2. 성공한 형식으로 여러 컬렉션 테스트
        test_multiple_collections(successful_format)
        
        # 3. 클라이언트 코드 업데이트 안내
        if update_client_code(successful_format):
            print(f"\n🎯 다음 단계:")
            print(f"   1. 위 변경사항을 적용하세요")
            print(f"   2. ADK 시스템을 다시 시작하세요")
            print(f"   3. 'addresses 컬렉션을 조회해서' 명령어를 테스트하세요")
        
        print(f"\n🎉 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 치명적 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 