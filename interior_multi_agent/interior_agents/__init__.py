"""
🏠 인테리어 멀티 에이전트 시스템 - ADK 공식 간단 방식
"""

from .agent_main import interior_agent

__version__ = "3.0.0"
__description__ = "ADK MCP 공식 방식 - 초간단 인테리어 멀티 에이전트 시스템"

# 메인 에이전트만 익스포트
__all__ = ["interior_agent"]

print(f"📦 인테리어 에이전트 시스템 v{__version__} (초간단 버전) 로드 완료") 