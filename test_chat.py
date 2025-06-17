import asyncio
import aiohttp
import json

async def test_chat():
    async with aiohttp.ClientSession() as session:
        # 테스트 1: 일반 인사
        print("\n1. 테스트: '안녕하세요'")
        async with session.post(
            "http://localhost:8000/chat",
            json={
                "message": "안녕하세요",
                "session_id": "test-session",
                "user_id": "test-user"
            }
        ) as response:
            result = await response.json()
            print("응답:", json.dumps(result, ensure_ascii=False, indent=2))

        # 테스트 2: 주소 조회
        print("\n2. 테스트: '주소 컬렉션 조회해줘'")
        async with session.post(
            "http://localhost:8000/chat",
            json={
                "message": "주소 컬렉션 조회해줘",
                "session_id": "test-session",
                "user_id": "test-user"
            }
        ) as response:
            result = await response.json()
            print("응답:", json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(test_chat()) 