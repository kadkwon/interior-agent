#!/usr/bin/env python3
"""
MCP 클라이언트 테스트 스크립트
"""

import asyncio
import aiohttp
import json

async def test_chat_api():
    """채팅 API 테스트"""
    url = "http://localhost:8505/chat"
    data = {
        "message": "안녕하세요, 주소 저장해주세요: 서울시 강남구 역삼동 123-45",
        "user_id": "test-user",
        "session_id": "test-session"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                print(f"Status: {response.status}")
                result = await response.json()
                print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
        except Exception as e:
            print(f"Error: {e}")

async def test_health_api():
    """Health API 테스트"""
    url = "http://localhost:8505/health"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                print(f"Health Status: {response.status}")
                result = await response.json()
                print(f"Health Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
        except Exception as e:
            print(f"Health Error: {e}")

async def main():
    print("=== Health Check ===")
    await test_health_api()
    
    print("\n=== Chat Test ===")
    await test_chat_api()

if __name__ == "__main__":
    asyncio.run(main()) 