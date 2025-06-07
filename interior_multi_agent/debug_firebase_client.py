#!/usr/bin/env python3
"""
Firebase 클라이언트 디버깅 도구
컬렉션 조회가 실패하는 원인을 찾기 위한 상세한 진단 도구
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'interior_agents'))

import requests
import json
from datetime import datetime
from interior_agents.firebase_client import firebase_client

class FirebaseDebugger:
    """Firebase 연결 및 API 디버깅 클래스"""
    
    def __init__(self):
        self.base_url = "https://us-central1-interior-one-click.cloudfunctions.net"
        self.client = firebase_client
    
    def test_basic_connectivity(self):
        """기본 연결성 테스트"""
        print("🔗 기본 연결성 테스트")
        print("-" * 50)
        
        # 1. 프로젝트 정보 테스트 (GET 요청)
        print("\n1️⃣ Firebase 프로젝트 정보 (GET)")
        try:
            response = self.client.get_project_info()
            print(f"✅ 성공: {response.get('success', False)}")
            if not response.get('success'):
                print(f"❌ 오류: {response.get('error', 'Unknown')}")
        except Exception as e:
            print(f"💥 예외: {e}")
        
        # 2. 컬렉션 목록 테스트 (POST 요청)
        print("\n2️⃣ Firestore 컬렉션 목록 (POST)")
        try:
            response = self.client.list_collections()
            print(f"✅ 성공: {response.get('success', False)}")
            if response.get('success'):
                collections = response.get('data', {}).get('collections', [])
                print(f"📋 컬렉션 수: {len(collections)}")
                print(f"📋 처음 5개: {collections[:5]}")
            else:
                print(f"❌ 오류: {response.get('error', 'Unknown')}")
        except Exception as e:
            print(f"💥 예외: {e}")
    
    def test_raw_http_request(self, collection_name: str):
        """원시 HTTP 요청으로 컬렉션 조회 테스트"""
        print(f"\n🔍 '{collection_name}' 컬렉션 원시 HTTP 테스트")
        print("-" * 50)
        
        url = f"{self.base_url}/firestoreQueryCollection"
        
        # 여러 가지 요청 형식 시도
        test_payloads = [
            {
                "collection": collection_name,
                "limit": 5
            },
            {
                "collection_path": collection_name,  # 다른 필드명 시도
                "limit": 5
            },
            {
                "collectionId": collection_name,     # Firebase API 표준 필드명
                "limit": 5
            }
        ]
        
        for i, payload in enumerate(test_payloads, 1):
            print(f"\n{i}️⃣ 테스트 페이로드: {payload}")
            
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    timeout=30
                )
                
                print(f"🌐 HTTP 상태: {response.status_code}")
                print(f"📄 응답 헤더: {dict(response.headers)}")
                
                # 응답 내용 확인
                if response.status_code == 200:
                    try:
                        json_response = response.json()
                        print(f"✅ JSON 응답: {json_response}")
                    except json.JSONDecodeError:
                        print(f"❌ JSON 파싱 실패. Raw 응답: {response.text[:200]}...")
                else:
                    print(f"❌ HTTP 오류. Raw 응답: {response.text[:200]}...")
                    
            except requests.exceptions.Timeout:
                print("⏰ 요청 타임아웃 (30초)")
            except requests.exceptions.ConnectionError:
                print("🔌 연결 오류")
            except Exception as e:
                print(f"💥 예외: {e}")
    
    def test_collection_exists(self, collection_name: str):
        """컬렉션이 실제로 존재하는지 확인"""
        print(f"\n📋 '{collection_name}' 컬렉션 존재 여부 확인")
        print("-" * 50)
        
        # 컬렉션 목록에서 찾기
        collections_response = self.client.list_collections()
        
        if collections_response.get('success'):
            collections = collections_response.get('data', {}).get('collections', [])
            
            # 정확한 이름 매치
            exact_match = collection_name in collections
            print(f"🎯 정확한 매치 ('{collection_name}'): {exact_match}")
            
            # 유사한 이름 찾기
            similar_names = [c for c in collections if collection_name.lower() in c.lower()]
            print(f"🔍 유사한 이름들: {similar_names}")
            
            # 대소문자 구분 없이 찾기
            case_insensitive_matches = [c for c in collections if c.lower() == collection_name.lower()]
            print(f"📝 대소문자 무시 매치: {case_insensitive_matches}")
            
            return exact_match, similar_names, case_insensitive_matches
        else:
            print(f"❌ 컬렉션 목록 조회 실패: {collections_response.get('error')}")
            return False, [], []
    
    def test_different_endpoints(self, collection_name: str):
        """다른 엔드포인트들 테스트"""
        print(f"\n🚀 다른 Firebase 엔드포인트들 테스트")
        print("-" * 50)
        
        endpoints_to_test = [
            ('/firebaseGetProject', 'GET', None),
            ('/mcpListApis', 'GET', None),
            ('/firestoreListCollections', 'POST', {}),
            ('/storageListFiles', 'POST', {"prefix": ""}),
            ('/authListUsers', 'POST', {"maxResults": 1}),
        ]
        
        for endpoint, method, data in endpoints_to_test:
            print(f"\n🔸 {endpoint} ({method})")
            try:
                response = self.client._make_request(endpoint, method, data)
                success = response.get('success', False)
                print(f"   ✅ 성공: {success}")
                if not success:
                    print(f"   ❌ 오류: {response.get('error', 'Unknown')}")
            except Exception as e:
                print(f"   💥 예외: {e}")

def main():
    """메인 디버깅 함수"""
    print("🐛 Firebase 컬렉션 조회 문제 진단 도구")
    print("=" * 60)
    
    debugger = FirebaseDebugger()
    
    # 테스트할 컬렉션들
    test_collections = ["addresses", "schedules", "schedule", "customers", "users"]
    
    # 1. 기본 연결성 테스트
    debugger.test_basic_connectivity()
    
    # 2. 각 컬렉션에 대한 상세 테스트
    for collection in test_collections:
        print(f"\n{'='*60}")
        print(f"🔍 '{collection}' 컬렉션 상세 진단")
        print(f"{'='*60}")
        
        # 컬렉션 존재 여부 확인
        exact, similar, case_insensitive = debugger.test_collection_exists(collection)
        
        # 원시 HTTP 요청 테스트
        debugger.test_raw_http_request(collection)
    
    # 3. 다른 엔드포인트들 테스트
    debugger.test_different_endpoints("addresses")
    
    print(f"\n{'='*60}")
    print("🎯 진단 결과 요약")
    print(f"{'='*60}")
    print("📋 확인된 문제점들:")
    print("   1. /firestoreQueryCollection 엔드포인트의 500 오류")
    print("   2. 다른 Firebase API들은 정상 작동하는지 확인 필요")
    print("   3. 컬렉션 이름의 정확성 확인 필요")
    print("\n🔧 권장 해결책:")
    print("   1. Cloud Functions 로그 확인")
    print("   2. Firestore 보안 규칙 확인")
    print("   3. 요청 페이로드 형식 확인")

if __name__ == "__main__":
    main() 