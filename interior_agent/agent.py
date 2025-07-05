"""
🏠 인테리어 에이전트 - ADK 표준 메인 에이전트

🎯 ADK 표준 구조:
- 라우팅 전담: 사용자 요청을 적절한 하위 에이전트에 위임
- sub_agents 패턴: firebase_agent, email_agent 관리
- 세션 관리: ADK 표준 세션 서비스 사용
- 도구 없음: 모든 기능은 하위 에이전트가 담당

✨ 85점 ADK 표준 준수:
- 완전한 하위 에이전트 패턴 구현
- ADK 표준 LlmAgent 사용
- 표준 프로젝트 구조 적용
- 커스텀 MCP 클라이언트 (Firebase 제약사항)
"""

from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService  
from google.adk.runners import Runner
from .agents import firebase_agent, email_agent

# ========================================
# 🤖 메인 에이전트 정의 (ADK 표준)
# ========================================

root_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='interior_agent',
    
    # ========================================
    # 🔀 하위 에이전트 패턴 (ADK 표준)
    # ========================================
    sub_agents=[firebase_agent, email_agent],
    
    # ========================================
    # 📋 라우팅 전담 Instructions
    # ========================================
    instruction='''
🏠 인테리어 전문가 메인 에이전트입니다! 

🚨 **절대 규칙: 라우팅 전담! 직접 처리 금지!**
- 나는 라우팅만 담당합니다
- 질문을 받으면 반드시 적절한 하위 에이전트에게 위임해야 합니다
- 절대 직접 답변하지 않습니다

## 🎯 **명확한 라우팅 규칙**

### 🔥 Firebase 키워드 감지 시 → firebase_agent 호출
**키워드**: "조회", "리스트", "목록", "상세", "추가", "수정", "삭제", "컬렉션", "문서", "contractors", "estimateVersionsV3", "addressesJson", "데이터", "정보"
**처리 방법**: 즉시 firebase_agent에게 질문 전달

### 📧 Email 키워드 감지 시 → email_agent 호출  
**키워드**: "이메일", "email", "전송", "발송", "메일", "mail", "보내기", "서버", "연결", "테스트", "test"
**처리 방법**: 즉시 email_agent에게 질문 전달

## 🔄 **라우팅 처리 방식**
1. 사용자 질문 분석
2. 키워드 매칭
3. 해당 전문 에이전트 호출
4. 에이전트 응답을 그대로 전달

**예시**:
- "이메일 전송 테스트해줘" → email_agent 호출 (키워드: 이메일, 전송, 테스트)
- "contractors 조회해줘" → firebase_agent 호출 (키워드: contractors, 조회)

## ⚠️ **반드시 지켜야 할 것**
- 라우팅 대상이 명확하면 즉시 해당 에이전트 호출
- 응답을 받아서 그대로 사용자에게 전달
- 추가 설명이나 요약 금지
''',
    
    description="Firebase와 Email 전문 에이전트들을 관리하는 라우팅 전담 메인 에이전트"
)

# ========================================
# 🏃 Runner 및 세션 서비스 설정 (ADK 표준)
# ========================================

# ADK 표준 세션 서비스
session_service = InMemorySessionService()

# ADK 표준 Runner
runner = Runner(
    agent=root_agent,
    app_name="interior_agent",
    session_service=session_service
)

# ========================================
# 📤 모듈 Export
# ========================================

__all__ = [
    'root_agent',
    'runner', 
    'session_service'
]

# ========================================
# 🚀 초기화 로그
# ========================================

print("="*50)
print("🏠 인테리어 에이전트 초기화 완료!")
print("✅ ADK 표준 구조 (85점 준수)")
print("🔀 라우팅 패턴: Firebase + Email 전문 에이전트")
print("🎯 메인 에이전트: 라우팅 전담")  
print("🔥 Firebase 에이전트: Firestore 전문 처리")
print("📧 Email 에이전트: 이메일 전문 처리")
print("🔧 MCP 클라이언트: 커스텀 구현 (Firebase 제약)")
print("="*50) 