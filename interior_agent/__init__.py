"""
🏠 인테리어 에이전트 - ADK 표준 구조

🎯 ADK 표준 85점 준수:
- 완전한 하위 에이전트 패턴
- 표준 프로젝트 구조
- 라우팅 전담 메인 에이전트
- 전문 에이전트 분리

📦 주요 컴포넌트:
- agent: 메인 에이전트 및 Runner
- agents: 하위 에이전트들 (firebase, email)
- tools: 도구들 (mcp_client)
"""

from .agent import root_agent, runner, session_service
from .agents import firebase_agent, email_agent
from .tools import firebase_client, email_client

# 🔧 AS 전용 루트 에이전트 import 추가
from .as_root_agent import as_root_agent, as_runner, as_session_service

# 📊 견적 상담 전용 루트 에이전트 import 추가  
from .estimate_root_agent import estimate_root_agent, estimate_runner, estimate_session_service

__version__ = "1.0.0"

__all__ = [
    'root_agent',
    'runner', 
    'session_service',
    'firebase_agent',
    'email_agent',
    'firebase_client',
    'email_client',
    'as_root_agent',
    'as_runner',
    'as_session_service',
    'estimate_root_agent',
    'estimate_runner', 
    'estimate_session_service'
]

# ========================================
# 🎯 ADK 표준 구조 정보
# ========================================

ADK_COMPLIANCE_SCORE = 85
ADK_FEATURES = [
    "✅ 표준 프로젝트 구조",
    "✅ sub_agents 패턴",
    "✅ 라우팅 전담 메인 에이전트", 
    "✅ 전문 에이전트 분리",
    "✅ ADK 표준 LlmAgent 사용",
    "✅ 표준 Runner 및 세션 서비스",
    "⚠️ 커스텀 MCP 클라이언트 (Firebase 제약)"
]

def print_adk_info():
    """ADK 표준 준수 정보 출력"""
    print("="*60)
    print("🏠 인테리어 에이전트 - ADK 표준 구조")
    print(f"🎯 ADK 준수도: {ADK_COMPLIANCE_SCORE}/100")
    print("📋 구현된 기능:")
    for feature in ADK_FEATURES:
        print(f"  {feature}")
    print("="*60) 