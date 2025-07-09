"""
📊 견적 상담 전용 루트 에이전트 - 최소한 구성

목적: 견적 상담 요청 시 기존 estimate_agent.py 호출
"""

from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService  
from google.adk.runners import Runner
from .agents.estimate_agent import estimate_agent

# ========================================
# 🤖 견적 상담 전용 루트 에이전트 (최소한)
# ========================================

# estimate_agent 복사본 생성 (부모 에이전트 충돌 방지)
estimate_agent_copy = LlmAgent(
    model=estimate_agent.model,
    name='estimate_agent_copy',
    tools=estimate_agent.tools,
    instruction=estimate_agent.instruction,
    description="견적 상담 전용 복사본 에이전트"
)

estimate_root_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='estimate_root_agent',
    
    # estimate_agent 복사본 사용 (충돌 방지)
    sub_agents=[estimate_agent_copy],
    
    # 최소한의 라우팅 instruction
    instruction='''
견적 상담 전용 루트 에이전트입니다.

모든 요청을 estimate_agent_copy에게 위임합니다.
직접 처리하지 않고 estimate_agent_copy 호출만 담당합니다.
''',
    
    description="견적 상담 전용 라우팅 에이전트"
)

# ========================================
# 🏃 Runner 및 세션 서비스 설정
# ========================================

estimate_session_service = InMemorySessionService()

estimate_runner = Runner(
    agent=estimate_root_agent,
    app_name="estimate_root_agent",
    session_service=estimate_session_service
)

# ========================================
# 📤 모듈 Export
# ========================================

__all__ = [
    'estimate_root_agent',
    'estimate_runner', 
    'estimate_session_service'
]

# ========================================
# 🚀 초기화 로그
# ========================================

print("="*50)
print("📊 견적 상담 전용 루트 에이전트 초기화 완료!")
print("🔀 기존 estimate_agent.py 호출 방식")
print("📝 최소한 구성")
print("="*50) 