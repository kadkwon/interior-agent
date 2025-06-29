"""
🔥 인테리어 Firebase 에이전트 시스템 - HTTP Direct 방식

Firebase 전체 기능을 지원하는 인테리어 프로젝트 관리 에이전트
"""

# MCP HTTP Direct 클라이언트
from .mcp_client import firebase_client, email_client

# 에이전트들
from .email_agent import email_agent

# 루트 에이전트 (Firebase 전체 기능)
from .agent_main import interior_agent

__all__ = [
    'firebase_client',
    'email_client', 
    'email_agent',
    'interior_agent'
]

print("🚀 인테리어 Firebase 에이전트 시스템 (HTTP Direct) 로드 완료")
print(f"🔥 Firebase 도구: 10개 (Firestore 5개 + Auth 1개 + Storage 4개)")
print(f"📧 이메일 도구: 2개") 
print(f"📦 총 도구: 12개") 