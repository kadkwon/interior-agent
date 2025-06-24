#!/usr/bin/env python3

"""
간단한 MCP 서버 연결 테스트
"""

import asyncio
import aiohttp
import json

async def test_mcp_server():
    """MCP 서버 연결 테스트"""
    
    print("🧪 FastMCP 서버 연결 테스트")
    print("=" * 40)
    
    server_url = "http://localhost:8001/sse"
    
    try:
        # 1. 기본 연결 테스트
        print(f"📡 서버 연결 시도: {server_url}")
        
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(server_url) as response:
                print(f"📊 응답 상태: {response.status}")
                print(f"📋 헤더: {dict(response.headers)}")
                
                if response.status == 200:
                    print("✅ 서버 연결 성공!")
                    
                    # SSE 연결이므로 첫 번째 청크만 읽어보기
                    try:
                        first_chunk = await asyncio.wait_for(
                            response.content.read(1024), 
                            timeout=2.0
                        )
                        print(f"📨 첫 번째 응답 데이터: {first_chunk[:100]}...")
                    except asyncio.TimeoutError:
                        print("⏱️  SSE 스트리밍 연결 대기 중 (정상)")
                    
                else:
                    print(f"❌ 서버 연결 실패: HTTP {response.status}")
                    
    except aiohttp.ClientError as e:
        print(f"❌ 연결 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
    
    print()
    print("🎯 테스트 결과:")
    print("- 서버가 실행 중이면 HTTP 200 응답이 나와야 합니다")
    print("- SSE 연결이므로 streaming 응답을 기대합니다")
    print("- Claude Web에서 이 URL로 Remote MCP 연결이 가능합니다")

if __name__ == "__main__":
    asyncio.run(test_mcp_server()) 