"""
🔧 AS 전용 루트 에이전트 - 최소한 구성

목적: 특정 키워드 수신 시 기존 as_agent.py 호출
"""

from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService  
from google.adk.runners import Runner
from .agents.as_agent import as_agent

# ========================================
# 🤖 AS 전용 루트 에이전트 (최소한)
# ========================================

# as_agent 복사본 생성 (부모 에이전트 충돌 방지)
as_agent_copy = LlmAgent(
    model=as_agent.model,
    name='as_agent_copy',
    tools=as_agent.tools,
    instruction=as_agent.instruction,
    description="AS 전용 복사본 에이전트"
)

as_root_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='as_root_agent',
    
    # as_agent 복사본 사용 (충돌 방지)
    sub_agents=[as_agent_copy],
    
    # 최소한의 라우팅 instruction
    instruction='''
AS 전용 루트 에이전트입니다.

모든 요청을 as_agent_copy에게 위임합니다.
직접 처리하지 않고 as_agent_copy 호출만 담당합니다.
''',
    
    description="AS 전용 라우팅 에이전트"
)

# ========================================
# 🏃 Runner 및 세션 서비스 설정
# ========================================

as_session_service = InMemorySessionService()

as_runner = Runner(
    agent=as_root_agent,
    app_name="as_root_agent",
    session_service=as_session_service
)

# ========================================
# 📤 모듈 Export
# ========================================

__all__ = [
    'as_root_agent',
    'as_runner', 
    'as_session_service'
]

# ========================================
# 🚀 초기화 로그
# ========================================

print("="*50)
print("🔧 AS 전용 루트 에이전트 초기화 완료!")
print("🔀 기존 as_agent.py 호출 방식")
print("📝 최소한 구성")
print("="*50) 