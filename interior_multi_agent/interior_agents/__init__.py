"""
🔥 인테리어 Firebase 에이전트 시스템 - Firebase + Email 통합 버전

Firebase와 Email 기능을 모두 지원하는 인테리어 프로젝트 관리 에이전트
"""

# MCP HTTP Direct 클라이언트
from .mcp_client import firebase_client, email_client

# 에이전트들
from .email_agent import email_agent

# 루트 에이전트 (Firebase 전용)
from .agent_main import interior_agent

__all__ = [
    'firebase_client',
    'email_client',
    'email_agent',
    'interior_agent'
]

print("🚀 인테리어 Firebase 에이전트 시스템 로드 완료")
print(f"🔥 Firebase 도구: 6개 (컬렉션 조회, 문서 CRUD)")
print(f"📧 Email 도구: 3개 (전송, 연결 테스트, 서버 정보)")
print(f"📦 총 도구: 9개") 