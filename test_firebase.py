#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Firebase 연결 테스트 스크립트"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'interior_agents'))

def test_firebase_connection():
    try:
        from interior_agents.client.firebase_client import firebase_client
        
        print("🔥 Firebase 연결 테스트 시작...")
        print(f"📍 Base URL: {firebase_client.base_url}")
        
        # 1. 프로젝트 정보 조회 테스트
        print("\n1️⃣ 프로젝트 정보 조회 테스트...")
        result = firebase_client.get_project_info()
        
        # 2. 간단한 쿼리 테스트
        print("\n2️⃣ 컬렉션 목록 조회 테스트...")
        result2 = firebase_client.list_collections()
        
        print("\n✅ Firebase 연결 테스트 완료")
        
    except ImportError as e:
        print(f"❌ 모듈 임포트 오류: {e}")
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")

if __name__ == "__main__":
    test_firebase_connection() 