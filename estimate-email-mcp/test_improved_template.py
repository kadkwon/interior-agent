#!/usr/bin/env python3
"""
개선된 이메일 템플릿 테스트 스크립트
- 공정 번호 제거 및 아이콘 사용
- 숨겨진 공정 필터링
- 깔끔한 HTML 디자인
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# 테스트 데이터
test_process_data = [
    {
        "id": "design", 
        "name": "디자인", 
        "items": [], 
        "total": 0, 
        "processOrder": 1
    },
    {
        "id": "demolition", 
        "name": "철거폐기물", 
        "items": [
            {
                "name": "욕실 철거 및 몰딩 철거",
                "quantity": 1,
                "unitPrice": 490000,
                "totalPrice": 490000,
                "isAdditional": False
            },
            {
                "name": "폐기물 처리",
                "quantity": 1,
                "unitPrice": 350000,
                "totalPrice": 350000,
                "isAdditional": False
            }
        ], 
        "total": 840000, 
        "processOrder": 2
    },
    {
        "id": "carpentry", 
        "name": "목공사", 
        "items": [
            {
                "name": "목수 인건비",
                "quantity": 2,
                "unitPrice": 525000,
                "totalPrice": 1050000,
                "isAdditional": False
            },
            {
                "name": "목자재",
                "quantity": 1,
                "unitPrice": 670000,
                "totalPrice": 670000,
                "isAdditional": False
            }
        ], 
        "total": 1720000, 
        "processOrder": 6
    },
    {
        "id": "film", 
        "name": "필름공사", 
        "items": [
            {
                "name": "인테리어필름 인건비 및 부자재",
                "quantity": 1,
                "unitPrice": 3400000,
                "totalPrice": 3400000,
                "isAdditional": False
            }
        ], 
        "total": 3400000, 
        "processOrder": 10
    },
    {
        "id": "wallpaper", 
        "name": "도배공사", 
        "items": [
            {
                "name": "벽지(방 베스락)",
                "quantity": 8,
                "unitPrice": 60000,
                "totalPrice": 480000,
                "isAdditional": False
            },
            {
                "name": "인건비",
                "quantity": 4,
                "unitPrice": 290000,
                "totalPrice": 1160000,
                "isAdditional": False
            },
            {
                "name": "드레스룸 단열 벽지 재시공 시 추가금",
                "quantity": 1,
                "unitPrice": 100000,
                "totalPrice": 100000,
                "isAdditional": True
            },
            {
                "name": "DC",
                "quantity": 1,
                "unitPrice": -35000,
                "totalPrice": -35000,
                "isAdditional": True
            }
        ], 
        "total": 1705000, 
        "processOrder": 18
    }
]

# 숨겨진 공정 (total이 0인 공정들)
hidden_processes = {
    "design": {"hidden": True, "type": "auto"},
    "window": {"hidden": True, "type": "auto"},
    "plumbing": {"hidden": True, "type": "auto"},
    "ac": {"hidden": True, "type": "auto"},
    "electrical": {"hidden": True, "type": "auto"},
    "door": {"hidden": True, "type": "auto"},
    "tile": {"hidden": True, "type": "auto"},
    "painting": {"hidden": True, "type": "auto"}
}

async def test_improved_email():
    """개선된 이메일 템플릿 테스트"""
    
    print("🧪 개선된 이메일 템플릿 테스트")
    print("=" * 50)
    
    # MCP 메시지 구성
    mcp_message = {
        "jsonrpc": "2.0",
        "id": "test-improved-email",
        "method": "tools/call",
        "params": {
            "name": "send_estimate_email",
            "arguments": {
                "email": "test@example.com",
                "address": "개선된 템플릿 테스트 - 아이콘 및 숨겨진 공정 필터링",
                "process_data": test_process_data,
                "hidden_processes": hidden_processes,
                "corporate_profit": {"percentage": 10, "amount": 716500},
                "subject": "🏠 아마레디자인 견적서 - 개선된 템플릿 테스트"
            }
        }
    }
    
    try:
        # 로컬 서버에 요청
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/mcp",
                json=mcp_message,
                headers={"Content-Type": "application/json"},
                timeout=30
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ 테스트 성공!")
                    print(f"📨 응답: {result}")
                    
                    # 생성된 HTML 템플릿 미리보기
                    if "result" in result and "content" in result["result"]:
                        print("\n📋 생성된 이메일 내용:")
                        print("-" * 30)
                        content = result["result"]["content"]
                        if isinstance(content, list) and len(content) > 0:
                            print(content[0].get("text", "내용 없음"))
                        
                else:
                    print(f"❌ 테스트 실패: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"📄 에러 내용: {error_text}")
                    
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
        print("\n💡 해결 방법:")
        print("1. estimate-email-mcp 서버가 실행 중인지 확인")
        print("2. 포트 8001이 사용 가능한지 확인")
        print("3. python server.py 명령으로 서버 시작")

def main():
    """메인 함수"""
    print("🚀 개선된 이메일 템플릿 기능 테스트")
    print("✨ 새로운 기능:")
    print("  - 🔧 공정 번호 대신 아이콘 사용")
    print("  - 👁️ 숨겨진 공정 자동 필터링")
    print("  - 🎨 깔끔한 HTML 디자인")
    print("  - 📱 반응형 레이아웃")
    print()
    
    # 비동기 함수 실행
    asyncio.run(test_improved_email())

if __name__ == "__main__":
    main() 