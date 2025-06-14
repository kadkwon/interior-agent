#!/usr/bin/env python3
"""
ADK API 서버 연결 상태 테스트 스크립트
"""

import sys
import time
from chat_manager import ChatManager

def test_connection():
    """연결 상태 테스트"""
    print("=== ADK API 서버 연결 상태 테스트 ===\n")
    
    # ChatManager 초기화
    chat_manager = ChatManager()
    
    # 1. 기본 상태 확인
    print("1. 기본 에이전트 상태:")
    status = chat_manager.get_agent_status()
    print(f"   - 현재 에이전트: {status['agent_type']}")
    print(f"   - 에이전트 사용 가능: {status['agent_available']}")
    print(f"   - ADK API 모듈 로드: {status['adk_api_available']}")
    print()
    
    # 2. ADK API 서버 기본 연결 테스트
    print("2. ADK API 서버 기본 연결 테스트:")
    connection = chat_manager.check_adk_api_connection(test_chat=False)
    print(f"   - 연결 상태: {'✅ 연결됨' if connection['connected'] else '❌ 연결 실패'}")
    print(f"   - 서버 상태: {connection['status']}")
    print(f"   - 에이전트 사용 가능: {connection['agent_available']}")
    if connection['error']:
        print(f"   - 오류: {connection['error']}")
    print()
    
    # 3. ADK API 서버 완전 테스트 (채팅 포함)
    print("3. ADK API 서버 완전 테스트 (채팅 포함):")
    full_connection = chat_manager.check_adk_api_connection(test_chat=True)
    print(f"   - 연결 상태: {'✅ 연결됨' if full_connection['connected'] else '❌ 연결 실패'}")
    print(f"   - 서버 상태: {full_connection['status']}")
    print(f"   - 채팅 테스트: {'✅ 성공' if full_connection.get('chat_test') else '❌ 실패'}")
    if full_connection.get('chat_error'):
        print(f"   - 채팅 오류: {full_connection['chat_error']}")
    print()
    
    # 4. ChatManager를 통한 실제 채팅 테스트
    if full_connection['status'] == 'healthy' and full_connection.get('chat_test'):
        print("4. ChatManager를 통한 실제 채팅 테스트:")
        test_messages = [
            "안녕하세요!",
            "주소 리스트 보여줘"
        ]
        
        for i, msg in enumerate(test_messages, 1):
            print(f"   테스트 {i}: {msg}")
            try:
                response = chat_manager.get_response(msg)
                print(f"   응답: {response[:100]}{'...' if len(response) > 100 else ''}")
                print()
            except Exception as e:
                print(f"   오류: {e}")
                print()
    else:
        print("4. ChatManager 채팅 테스트 건너뜀 (서버 또는 에이전트 문제)")
    
    print("=== 테스트 완료 ===")

def monitor_connection(interval=5):
    """연결 상태 모니터링"""
    print(f"=== ADK API 서버 연결 모니터링 (간격: {interval}초) ===")
    print("Ctrl+C로 중지")
    
    chat_manager = ChatManager()
    
    try:
        while True:
            connection = chat_manager.check_adk_api_connection(test_chat=True)
            timestamp = time.strftime("%H:%M:%S")
            
            if connection['status'] == 'healthy' and connection.get('chat_test'):
                print(f"[{timestamp}] ✅ 완전 정상 - 서버 및 에이전트 모두 작동")
            elif connection['status'] == 'partial':
                print(f"[{timestamp}] ⚠️ 부분 연결 - 서버 OK, 에이전트 문제: {connection.get('chat_error', 'Unknown')}")
            elif connection['connected']:
                print(f"[{timestamp}] 🟡 연결됨 - 상태: {connection['status']}")
            else:
                print(f"[{timestamp}] ❌ 연결 실패 - {connection['error']}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n모니터링 중지됨")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        monitor_connection()
    else:
        test_connection() 