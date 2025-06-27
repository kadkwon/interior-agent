"""
🏠 주소 관리 하위 에이전트 - ADK 미니멀 방식
"""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .mcp_client import firebase_client

async def search_addresses(query: str = "", limit: int = 20):
    """주소 검색 - 디버그 모드로 실제 오류 확인"""
    print(f"🔍 주소 검색 시작: collection=addressesJson, limit={limit}")
    
    result = await firebase_client.call_tool("firestore_list_documents", {
        "collection": "addressesJson", 
        "limit": limit
    })
    
    print(f"🔥 MCP 호출 결과: {result}")
    
    # 실제 결과 반환 (Mock 없이)
    return result

async def get_address_detail(document_id: str):
    """주소 상세 조회"""
    return await firebase_client.call_tool("firestore_get_document", {
        "collection": "addressesJson",
        "id": document_id
    })

async def add_new_address(description: str, data_json: str):
    """새 주소 추가"""
    return await firebase_client.call_tool("firestore_add_document", {
        "collection": "addressesJson",
        "data": {"description": description, "dataJson": data_json}
    })

# 주소 관리 하위 에이전트
address_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='address_manager',
    instruction='주소 관리 전문 에이전트. addressesJson 컬렉션에서 주소를 검색, 조회, 추가할 수 있습니다.',
    tools=[
        FunctionTool(search_addresses),
        FunctionTool(get_address_detail),
        FunctionTool(add_new_address)
    ]
) 