#!/usr/bin/env python3
"""
🧪 Estimate Email MCP 서버 테스트 클라이언트

수정된 Cloud Functions 직접 호출 방식을 테스트하기 위한 스크립트입니다.
"""

import asyncio
import json
from server import mcp

async def test_email_mcp():
    """이메일 MCP 서버 기능 테스트"""
    
    print("🧪 Estimate Email MCP 서버 테스트 시작")
    print("=" * 50)
    
    # 1. 연결 테스트
    print("📡 1. 서버 연결 테스트")
    try:
        result = mcp.tools["test_connection"].handler()
        print("✅ 연결 성공!")
        print(f"📄 응답: {result['content'][0]['text'][:100]}...")
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return
    
    print()
    
    # 2. 서버 정보 조회 테스트
    print("📊 2. 서버 정보 조회 테스트")
    try:
        result = mcp.tools["get_server_info"].handler()
        print("✅ 정보 조회 성공!")
        print(f"📄 응답: {result['content'][0]['text'][:200]}...")
    except Exception as e:
        print(f"❌ 정보 조회 실패: {e}")
    
    print()
    
    # 3. 이메일 전송 테스트 (실제 전송 없이 유효성 검사만)
    print("📧 3. 이메일 전송 함수 테스트 (모의 데이터)")
    
    # 테스트 데이터 준비
    test_email = "test@example.com"
    test_address = "수성구 래미안 아파트 103동 702호"
    
    # 샘플 공정 데이터 (Firebase에서 조회한 형태)
    test_process_data = [
        {
            "id": "process_1",
            "name": "바닥 시공",
            "items": [
                {
                    "name": "마루 설치",
                    "quantity": 20,
                    "unit": "평",
                    "unitPrice": 50000,
                    "totalPrice": 1000000,
                    "isAdditional": False
                },
                {
                    "name": "걸레받이 설치",
                    "quantity": 50,
                    "unit": "m",
                    "unitPrice": 10000,
                    "totalPrice": 500000,
                    "isAdditional": False
                }
            ]
        },
        {
            "id": "process_2", 
            "name": "벽면 시공",
            "items": [
                {
                    "name": "벽지 시공",
                    "quantity": 30,
                    "unit": "평",
                    "unitPrice": 30000,
                    "totalPrice": 900000,
                    "isAdditional": False
                }
            ]
        }
    ]
    
    test_notes = {
        "process_1": "바닥 시공 시 주의사항",
        "general": "전체 공정 관련 메모"
    }
    
    test_hidden_processes = {
        "process_1": False,
        "process_2": False
    }
    
    try:
        print(f"📤 테스트 파라미터:")
        print(f"   📧 이메일: {test_email}")
        print(f"   🏠 주소: {test_address}")
        print(f"   📊 공정 수: {len(test_process_data)}개")
        print(f"   💰 예상 기업이윤: {240000:,}원 (총액 2,400,000원의 10%)")
        
        print()
        print("⚠️  실제 이메일 전송은 Cloud Functions 연결이 필요합니다.")
        print("   지금은 함수 호출 구조만 테스트합니다.")
        
        # 함수 파라미터 검증만 수행
        from server import _calculate_corporate_profit_amount
        
        # 기업이윤 계산 테스트
        test_corporate_profit = {"percentage": 10, "isVisible": True}
        calculated_profit = _calculate_corporate_profit_amount(test_process_data, test_corporate_profit)
        
        print(f"🧮 기업이윤 계산 테스트: {calculated_profit:,}원")
        
        if calculated_profit == 240000:  # 2,400,000 * 10%
            print("✅ 기업이윤 계산 정확!")
        else:
            print(f"⚠️  기업이윤 계산 확인 필요 (예상: 240,000원)")
        
        print()
        print("🎯 함수 구조 테스트 완료!")
        print("   실제 이메일 전송을 테스트하려면 Cloud Functions가 활성화되어야 합니다.")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
    
    print()
    print("=" * 50)
    print("🎉 테스트 완료!")
    print()
    print("📋 다음 단계:")
    print("1. python server.py 실행")
    print("2. Claude Web에서 Remote MCP 서버 연결")
    print("3. 실제 이메일 전송 테스트")

def test_config():
    """설정 파일 테스트"""
    print("⚙️ 설정 파일 테스트")
    print("-" * 30)
    
    try:
        from config import CONFIG, validate_config
        
        # 설정 검증
        validate_config()
        
        print(f"📊 서버: {CONFIG['server']['name']}")
        print(f"📡 주소: http://{CONFIG['server']['host']}:{CONFIG['server']['port']}/sse")
        print(f"☁️  Cloud Functions: {CONFIG['cloud_functions']['send_estimate_email']}")
        print(f"⏱️  타임아웃: {CONFIG['email']['timeout']}초")
        print(f"💰 기본 기업이윤: {CONFIG['email']['default_corporate_profit']['percentage']}%")
        print("✅ 설정 검증 완료!")
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 오류: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Estimate Email MCP 서버 종합 테스트")
    print("=" * 60)
    print()
    
    # 설정 테스트
    if not test_config():
        print("❌ 설정 테스트 실패로 인해 종료합니다.")
        exit(1)
    
    print()
    
    # MCP 서버 기능 테스트
    try:
        asyncio.run(test_email_mcp())
    except KeyboardInterrupt:
        print("\n⏹️  테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 중 예상치 못한 오류: {e}")
        exit(1) 