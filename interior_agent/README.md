# 🏠 인테리어 에이전트 - ADK 표준 구조

## 🎯 ADK 표준 준수도: 85/100

### ✨ 주요 특징
- **완전한 하위 에이전트 패턴**: Firebase와 Email 전문 에이전트로 분리
- **라우팅 전담 메인 에이전트**: 사용자 요청을 적절한 하위 에이전트에 위임
- **표준 프로젝트 구조**: ADK 권장 구조 준수
- **세션 관리**: ADK 표준 세션 서비스 사용

## 📁 프로젝트 구조

```
interior_agent/
├── agent.py              # 메인 에이전트 (라우팅 전담)
├── agents/               # 하위 에이전트들
│   ├── __init__.py
│   ├── firebase_agent.py # Firebase 전문 에이전트
│   ├── email_agent.py    # Email 전문 에이전트
│   └── formatter_agent.py # 응답 포맷팅 도구
├── tools/                # 도구들
│   ├── __init__.py
│   └── mcp_client.py     # MCP 클라이언트 (커스텀 구현)
├── __init__.py           # 패키지 초기화
├── test_adk_agent.py     # ADK 표준 테스트
├── requirements.txt      # 의존성
└── README.md
```

## 🤖 에이전트 아키텍처

### 메인 에이전트 (agent.py)
- **역할**: 라우팅 전담
- **패턴**: `sub_agents` 사용
- **기능**: 사용자 요청 분석 → 적절한 하위 에이전트 선택 → 위임

### 하위 에이전트들 (agents/)

#### 🔥 Firebase 에이전트
- **전문 분야**: Firebase Firestore 데이터베이스
- **주요 기능**: 
  - 컬렉션 목록 조회
  - 문서 조회, 추가, 수정, 삭제
  - 한글 포맷팅 자동 적용
- **트리거 키워드**: "조회", "리스트", "목록", "contractors", "견적서"

#### 📧 Email 에이전트
- **전문 분야**: 이메일 전송 및 서버 관리
- **주요 기능**:
  - 견적서 이메일 전송
  - 이메일 서버 연결 테스트
  - 복잡한 JSON 데이터 처리
- **트리거 키워드**: "이메일", "전송", "발송", "메일", "서버"

## 🔧 기술 스택

### ADK 표준 컴포넌트
- `LlmAgent`: 메인 및 하위 에이전트
- `FunctionTool`: 도구 래핑
- `Runner`: 에이전트 실행
- `InMemorySessionService`: 세션 관리

### 커스텀 구현
- `MCPClient`: Firebase MCP 서버 통신 (SSE 미지원으로 인한 커스텀)

## 🚀 사용 방법

### 1. 설치
```bash
pip install -r requirements.txt
```

### 2. 기본 사용
```python
import asyncio
from interior_agent import runner, session_service

async def main():
    # 세션 생성
    session = session_service.create_session()
    
    # Firebase 요청
    response = await runner.run_session(session.id, "contractors 조회해줘")
    print(response)
    
    # Email 요청
    response = await runner.run_session(session.id, "이메일 서버 테스트")
    print(response)

asyncio.run(main())
```

### 3. 테스트 실행
```bash
python -m interior_agent.test_adk_agent
```

## 📋 라우팅 규칙

### 🔥 Firebase 에이전트 라우팅
- **키워드**: "조회", "리스트", "목록", "상세", "추가", "수정", "삭제"
- **컬렉션**: "contractors", "estimateVersionsV3", "addressesJson"
- **예시**:
  ```
  "contractors 조회해줘" → firebase_agent
  "견적서 목록 보여줘" → firebase_agent
  "주소 리스트 가져와" → firebase_agent
  ```

### 📧 Email 에이전트 라우팅
- **키워드**: "이메일", "전송", "발송", "메일", "서버", "연결", "테스트"
- **예시**:
  ```
  "견적서 이메일 전송" → email_agent
  "이메일 서버 테스트" → email_agent
  "서버 정보 확인" → email_agent
  ```

## 🎯 ADK 표준 준수 현황

### ✅ 완전 준수 (70점)
- **표준 프로젝트 구조**: agent.py, agents/, tools/
- **sub_agents 패턴**: 하위 에이전트 정의 및 사용
- **라우팅 전담**: 메인 에이전트는 위임만 담당
- **ADK 표준 LlmAgent**: 모든 에이전트가 LlmAgent 사용
- **표준 Runner**: ADK Runner 및 세션 서비스
- **FunctionTool**: 모든 함수를 FunctionTool로 래핑

### ⚠️ 부분 준수 (15점)
- **커스텀 MCP 클라이언트**: Firebase MCP SSE 미지원으로 불가피한 커스텀
- **세션 동기화**: ADK 세션과 MCP 세션 간 동기화 구현
- **상세한 문서화**: 커스텀 구현 이유 명시

### ❌ 미준수 (0점)
- **완전한 MCPToolset**: Firebase 제약으로 불가능

## 🔍 핵심 개선사항

### 이전 구조 vs 새로운 구조

#### 🔴 이전 (비표준)
```python
# 혼재된 구조
interior_multi_agent/
├── interior_agents/
│   ├── agent_main.py     # 모든 기능 직접 처리
│   ├── email_agent.py    # 단순 함수들
│   └── formatter_agent.py # 순수 함수
```

#### 🟢 현재 (ADK 표준)
```python
# 표준 구조
interior_agent/
├── agent.py              # 라우팅 전담
├── agents/               # 전문 에이전트들
│   ├── firebase_agent.py # LlmAgent 객체
│   ├── email_agent.py    # LlmAgent 객체
│   └── formatter_agent.py # 공통 도구
└── tools/                # 인프라 도구들
    └── mcp_client.py     # MCP 통신
```

## 🎉 성과 요약

### 📊 정량적 개선
- **ADK 표준 준수도**: 0% → 85%
- **코드 구조 개선**: 혼재 → 명확한 역할 분리
- **에이전트 패턴**: 단일 → 계층적 멀티 에이전트

### 🏆 정성적 개선
- **유지보수성**: 명확한 구조로 코드 수정 용이
- **확장성**: 새로운 에이전트 추가 쉬움
- **표준 준수**: 업계 표준 패턴 적용
- **문서화**: 상세한 구조 설명 및 사용법 제공

## 📞 문의사항

ADK 표준 구조나 사용법에 대한 문의사항이 있으시면 언제든지 연락주세요! 