"""
인테리어 프로젝트 관리 에이전트의 루트 에이전트
"""

from .agent_main import InteriorAgent

# ADK Web이 찾을 수 있는 위치에 root_agent 노출
root_agent = InteriorAgent() 