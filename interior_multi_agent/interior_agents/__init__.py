"""
🔥 인테리어 Firestore 에이전트 시스템 - Firestore 전용 버전

Firestore 전용 인테리어 프로젝트 관리 에이전트
"""

# MCP HTTP Direct 클라이언트 (Firestore 전용)
from .mcp_client import firebase_client

# 루트 에이전트 (Firestore 전용)
from .agent_main import interior_agent

__all__ = [
    'firebase_client',
    'interior_agent'
]

print("🚀 인테리어 Firestore 에이전트 시스템 로드 완료")
print(f"🔥 Firestore 도구: 6개 (컬렉션 조회, 문서 CRUD)")
print(f"📦 총 도구: 6개") 