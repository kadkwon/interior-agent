import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class EnhancedFirebaseClient:
    """향상된 Firebase Cloud Functions 클라이언트 - 더 나은 오류 처리"""
    
    def __init__(self):
        self.base_url = "https://us-central1-interior-one-click.cloudfunctions.net"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Interior-Multi-Agent/1.0'
        })
    
    def _make_request_detailed(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict[str, Any]:
        """
        더 상세한 오류 정보를 제공하는 HTTP 요청 함수
        """
        url = f"{self.base_url}{endpoint}"
        
        # 요청 로깅
        print(f"🌐 요청: {method} {url}")
        if data:
            print(f"📦 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        try:
            # 요청 실행
            if method.upper() == 'GET':
                response = self.session.get(url, params=data if data else None, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data if data else {}, timeout=30)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메소드: {method}")
            
            # 응답 로깅
            print(f"📊 응답 상태: {response.status_code}")
            print(f"📄 응답 헤더: {dict(response.headers)}")
            
            # 성공적인 응답 처리
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    print(f"✅ JSON 응답 성공")
                    return json_response
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 실패: {e}")
                    return {
                        "success": False,
                        "error": f"JSON 파싱 실패: {str(e)}",
                        "raw_response": response.text[:500],
                        "status_code": response.status_code
                    }
            
            # HTTP 오류 처리
            else:
                error_text = response.text
                print(f"❌ HTTP 오류: {response.status_code}")
                print(f"📝 오류 내용: {error_text[:300]}...")
                
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code} 오류",
                    "error_details": error_text,
                    "status_code": response.status_code,
                    "endpoint": endpoint
                }
                
        except requests.exceptions.Timeout:
            print("⏰ 요청 타임아웃")
            return {
                "success": False,
                "error": "요청 타임아웃 (30초)",
                "endpoint": endpoint
            }
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 연결 오류: {e}")
            return {
                "success": False,
                "error": f"연결 오류: {str(e)}",
                "endpoint": endpoint
            }
        except Exception as e:
            print(f"💥 예상치 못한 오류: {e}")
            return {
                "success": False,
                "error": f"예상치 못한 오류: {str(e)}",
                "endpoint": endpoint
            }
    
    def query_collection_enhanced(self, collection_name: str, limit: int = 10) -> Dict[str, Any]:
        """
        향상된 컬렉션 조회 - 여러 방법으로 시도
        """
        print(f"\n🔍 '{collection_name}' 컬렉션 조회 시작")
        print("-" * 40)
        
        # 여러 가지 요청 형식으로 시도
        payload_variations = [
            # 표준 형식
            {
                "collection": collection_name,
                "limit": limit
            },
            # Firebase MCP 표준 형식
            {
                "collection_path": collection_name,
                "limit": limit
            },
            # Firestore API 표준 형식
            {
                "collectionId": collection_name,
                "limit": limit
            }
        ]
        
        for i, payload in enumerate(payload_variations, 1):
            print(f"\n{i}️⃣ 시도 #{i}: {payload}")
            
            response = self._make_request_detailed('/firestoreQueryCollection', 'POST', payload)
            
            if response.get('success'):
                print(f"✅ 성공! 방법 #{i}로 조회 완료")
                return response
            else:
                print(f"❌ 실패: {response.get('error', '알 수 없는 오류')}")
        
        # 모든 방법이 실패한 경우
        return {
            "success": False,
            "error": f"모든 조회 방법 실패: '{collection_name}' 컬렉션을 찾을 수 없습니다",
            "tried_methods": len(payload_variations)
        }
    
    def list_collections_detailed(self) -> Dict[str, Any]:
        """상세한 컬렉션 목록 조회"""
        print(f"\n📋 컬렉션 목록 조회")
        print("-" * 30)
        
        return self._make_request_detailed('/firestoreListCollections', 'POST', {})
    
    def test_all_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """모든 엔드포인트 테스트"""
        print(f"\n🚀 모든 Firebase 엔드포인트 테스트")
        print("-" * 40)
        
        endpoints = {
            'project_info': ('/firebaseGetProject', 'GET', None),
            'list_apis': ('/mcpListApis', 'GET', None),
            'list_collections': ('/firestoreListCollections', 'POST', {}),
            'list_storage': ('/storageListFiles', 'POST', {"prefix": ""}),
            'list_users': ('/authListUsers', 'POST', {"maxResults": 1}),
        }
        
        results = {}
        
        for name, (endpoint, method, data) in endpoints.items():
            print(f"\n🔸 {name} 테스트")
            response = self._make_request_detailed(endpoint, method, data)
            results[name] = response
            
            if response.get('success'):
                print(f"   ✅ 성공")
            else:
                print(f"   ❌ 실패: {response.get('error', 'Unknown')}")
        
        return results

# 전역 인스턴스
enhanced_firebase_client = EnhancedFirebaseClient() 