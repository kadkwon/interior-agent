"""
🔥 인테리어 Firebase 에이전트 시스템 - Firebase + Email 통합 버전

Firebase와 Email 기능을 모두 지원하는 인테리어 프로젝트 관리 에이전트
"""

# MCP HTTP Direct 클라이언트
from .mcp_client import firebase_client, email_client

# 하위 에이전트 함수들 (더 이상 LlmAgent 객체가 아님)
# from .email_agent import email_agent (제거됨)

# 루트 에이전트 (Firebase 전용)
from .agent_main import interior_agent

__all__ = [
    'firebase_client',
    'email_client',
    'interior_agent'
]

print("🚀 인테리어 Firebase 에이전트 시스템 로드 완료")
print(f"🔥 Firebase 도구: 6개 (컬렉션 조회, 문서 CRUD)")
print(f"📧 Email 도구: 3개 (하위 에이전트 패턴으로 email_agent에 위임)")
print(f"🎯 라우팅 패턴: 메인 에이전트 → 전문 하위 에이전트 위임")
print(f"📦 총 도구: 9개") 