#!/usr/bin/env python3
"""
Firebase Cloud Functions 연동 테스트 스크립트

이 스크립트는 배포된 Firebase Cloud Functions와 ADK 시스템의 연동을 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'interior_agents'))

from interior_agents.firebase_client import firebase_client, schedule_formatter

def test_firebase_connection():
    """Firebase 연결 및 기본 기능 테스트"""
    
    print("🔥 Firebase Cloud Functions 연동 테스트 시작")
    print("=" * 60)
    
    # 1. 프로젝트 정보 조회 테스트
    print("\n1️⃣ Firebase 프로젝트 정보 조회 테스트")
    print("-" * 40)
    
    project_response = firebase_client.get_project_info()
    print(f"응답: {project_response}")
    
    # 2. API 목록 조회 테스트
    print("\n2️⃣ 사용 가능한 API 목록 조회 테스트")
    print("-" * 40)
    
    apis_response = firebase_client.list_apis()
    print(f"응답: {apis_response}")
    
    # 3. Firestore 컬렉션 목록 조회 테스트
    print("\n3️⃣ Firestore 컬렉션 목록 조회 테스트")
    print("-" * 40)
    
    collections_response = firebase_client.list_collections()
    print(f"응답: {collections_response}")
    
    # 4. Schedule 컬렉션 조회 테스트
    print("\n4️⃣ Schedule 컬렉션 조회 테스트")
    print("-" * 40)
    
    schedule_response = firebase_client.query_collection("schedule", limit=10)
    print(f"Raw 응답: {schedule_response}")
    
    # 포맷팅된 결과
    if schedule_response.get("success"):
        formatted_result = schedule_formatter.format_schedule_data(schedule_response)
        print(f"\n📅 포맷팅된 결과:\n{formatted_result}")
    
    # 5. Storage 파일 목록 조회 테스트
    print("\n5️⃣ Firebase Storage 파일 목록 조회 테스트")
    print("-" * 40)
    
    storage_response = firebase_client.list_files()
    print(f"응답: {storage_response}")
    
    # 6. 사용자 목록 조회 테스트
    print("\n6️⃣ Firebase Auth 사용자 목록 조회 테스트")
    print("-" * 40)
    
    users_response = firebase_client.list_users(max_results=5)
    print(f"응답: {users_response}")
    
    print("\n" + "=" * 60)
    print("✅ 모든 테스트 완료!")

def test_agent_functions():
    """ADK 에이전트 함수들 테스트"""
    
    print("\n🤖 ADK 에이전트 Firebase 함수 테스트")
    print("=" * 60)
    
    try:
        from interior_agents.agent import (
            query_schedule_collection,
            get_firebase_project_info,
            list_firestore_collections,
            query_any_collection,
            list_storage_files
        )
        
        # 1. Schedule 컬렉션 조회
        print("\n1️⃣ query_schedule_collection() 테스트")
        print("-" * 40)
        
        schedule_result = query_schedule_collection(limit=5)
        print(f"Status: {schedule_result.get('status')}")
        print(f"Message: {schedule_result.get('message')}")
        if schedule_result.get('formatted_result'):
            print(f"Formatted Result:\n{schedule_result['formatted_result']}")
        
        # 2. Firebase 프로젝트 정보
        print("\n2️⃣ get_firebase_project_info() 테스트")
        print("-" * 40)
        
        project_result = get_firebase_project_info()
        print(f"Status: {project_result.get('status')}")
        print(f"Message: {project_result.get('message')}")
        if project_result.get('project_info'):
            print(f"Project Info: {project_result['project_info']}")
        
        # 3. 컬렉션 목록
        print("\n3️⃣ list_firestore_collections() 테스트")
        print("-" * 40)
        
        collections_result = list_firestore_collections()
        print(f"Status: {collections_result.get('status')}")
        print(f"Message: {collections_result.get('message')}")
        if collections_result.get('formatted_list'):
            print(f"Collections:\n{collections_result['formatted_list']}")
        
        # 4. Storage 파일 목록
        print("\n4️⃣ list_storage_files() 테스트")
        print("-" * 40)
        
        storage_result = list_storage_files()
        print(f"Status: {storage_result.get('status')}")
        print(f"Message: {storage_result.get('message')}")
        
        print("\n✅ 에이전트 함수 테스트 완료!")
        
    except ImportError as e:
        print(f"❌ 에이전트 함수 임포트 실패: {e}")
    except Exception as e:
        print(f"❌ 에이전트 함수 테스트 중 오류: {e}")

def simulate_user_commands():
    """사용자 명령어 시뮬레이션"""
    
    print("\n🎯 사용자 명령어 시뮬레이션")
    print("=" * 60)
    
    # 일반적인 사용자 요청들을 시뮬레이션
    test_commands = [
        "schedule 컬렉션을 조회해서",
        "Firebase 프로젝트 정보를 확인해줘",
        "Firestore 컬렉션 목록을 보여줘",
        "Storage 파일 목록을 조회해줘"
    ]
    
    print("📋 테스트할 명령어들:")
    for i, cmd in enumerate(test_commands, 1):
        print(f"{i}. \"{cmd}\"")
    
    print("\n💡 이제 ADK 웹 인터페이스에서 위 명령어들을 테스트해보세요!")
    print("👉 실행 방법: adk web")
    print("👉 접속 URL: http://localhost:8000")

def main():
    """메인 함수"""
    
    print("🚀 Interior Multi-Agent Firebase 연동 테스트")
    print(f"🔗 Base URL: {firebase_client.base_url}")
    
    try:
        # 기본 Firebase 연결 테스트
        test_firebase_connection()
        
        # ADK 에이전트 함수 테스트
        test_agent_functions()
        
        # 사용자 명령어 가이드
        simulate_user_commands()
        
        print("\n🎉 모든 테스트가 완료되었습니다!")
        print("📚 이제 다음 단계로 진행하세요:")
        print("  1. cd interior_multi_agent")
        print("  2. adk web")
        print("  3. http://localhost:8000 접속")
        print("  4. 'schedule 컬렉션을 조회해서' 명령어 입력")
        
    except Exception as e:
        print(f"❌ 테스트 중 치명적 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 