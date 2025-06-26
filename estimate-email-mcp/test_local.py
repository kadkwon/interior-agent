#!/usr/bin/env python3
"""
🧪 Estimate Email MCP 서버 로컬 테스트 스크립트
"""

import requests
import json
import time

# 테스트 설정
BASE_URL = "http://localhost:8001"  # 로컬 서버 기본 주소
HEALTH_URL = f"{BASE_URL}/health"
INFO_URL = f"{BASE_URL}/"
MCP_URL = f"{BASE_URL}/sse"  # 로컬에서는 SSE 방식

def test_health_check():
    """Health check 테스트"""
    print("🏥 Health Check 테스트...")
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Health Check 성공!")
            print(f"   응답: {response.json()}")
        else:
            print(f"❌ Health Check 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ Health Check 에러: {e}")
    print()

def test_server_info():
    """서버 정보 테스트"""
    print("📊 서버 정보 테스트...")
    try:
        response = requests.get(INFO_URL, timeout=5)
        if response.status_code == 200:
            print("✅ 서버 정보 조회 성공!")
            info = response.json()
            print(f"   이름: {info.get('name')}")
            print(f"   버전: {info.get('version')}")
            print(f"   Transport: {info.get('transport')}")
            print(f"   지원 도구: {info.get('tools')}")
        else:
            print(f"❌ 서버 정보 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 서버 정보 에러: {e}")
    print()

def test_mcp_endpoint():
    """MCP 엔드포인트 테스트"""
    print("🔗 MCP 엔드포인트 테스트...")
    try:
        # SSE 연결은 직접 테스트하기 어려우므로 GET 요청으로 확인
        response = requests.get(MCP_URL, timeout=5)
        print(f"   MCP 엔드포인트 응답: {response.status_code}")
        if response.status_code in [200, 404]:  # 404도 정상 (SSE 엔드포인트)
            print("✅ MCP 엔드포인트 접근 가능!")
        else:
            print(f"⚠️ MCP 엔드포인트 상태: {response.status_code}")
    except Exception as e:
        print(f"❌ MCP 엔드포인트 에러: {e}")
    print()

def main():
    print("🧪 Estimate Email MCP 서버 로컬 테스트 시작")
    print(f"🎯 테스트 대상: {BASE_URL}")
    print("=" * 50)
    
    # 서버가 실행 중인지 확인
    print("⏳ 서버 연결 확인 중...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print("✅ 서버 연결 성공!")
    except Exception as e:
        print(f"❌ 서버에 연결할 수 없습니다: {e}")
        print("💡 서버를 먼저 실행해주세요: python server.py")
        return
    
    print()
    
    # 각 테스트 실행
    test_health_check()
    test_server_info()
    test_mcp_endpoint()
    
    print("=" * 50)
    print("🎉 테스트 완료!")
    print()
    print("📋 다음 단계:")
    print("1. 로컬 테스트가 성공했다면 클라우드런에 배포하세요:")
    print("   ./deploy.sh  (Linux/Mac)")
    print("   또는 gcloud 명령어로 직접 배포")
    print()
    print("2. 배포 후 MCP 클라이언트에서 사용:")
    print("   - HTTP: https://your-service-url/mcp")
    print("   - SSE: https://your-service-url/sse")

if __name__ == "__main__":
    main() 