"""
�� 인테리어 멀티 에이전트 시스템 - HTTP Direct 방식

미니멀한 ADK 구조로 구현된 인테리어 프로젝트 관리 에이전트
"""

# MCP HTTP Direct 클라이언트
from .mcp_client import firebase_client, email_client

# 하위 에이전트들
from .address_management_agent import address_agent
from .email_agent import email_agent

# 루트 에이전트 (라우팅 시스템)
from .agent_main import interior_agent

__all__ = [
    'firebase_client',
    'email_client', 
    'address_agent',
    'email_agent',
    'interior_agent'
]

print("🚀 인테리어 멀티 에이전트 시스템 (HTTP Direct) 로드 완료")
print(f"📦 에이전트: {len(__all__) - 2}개, 클라이언트: 2개") 