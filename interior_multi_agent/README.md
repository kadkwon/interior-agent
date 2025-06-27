# 🏠 인테리어 멀티 에이전트 시스템 v2.0

**ADK MCP 직접 사용 방식**으로 완전히 재구성된 간단하고 효율적인 인테리어 프로젝트 관리 시스템

## 🎯 주요 특징

- ✅ **미니멀한 설계**: 복잡한 클라이언트 제거, ADK MCP 직접 사용
- ✅ **단순한 도구 함수**: 각 기능을 독립적인 함수로 구현
- ✅ **Firebase MCP 연동**: 주소 관리, 데이터 저장
- ✅ **Email MCP 연동**: 견적서 이메일 전송
- ✅ **코드 간소화**: 319줄 → 50줄 미만으로 축소

## 📁 파일 구조

```
interior_multi_agent/
├── interior_agents/
│   ├── __init__.py                    # 시스템 초기화
│   ├── agent_main.py                  # 메인 에이전트 (간단)
│   ├── address_management_agent.py    # 주소 관리 도구들
│   └── email_agent.py                 # 이메일 관리 도구들
├── requirements.txt                   # 최소 의존성
└── README.md                          # 이 파일
```

## 🔧 주요 도구

### 📍 주소 관리
- `search_addresses()` - 주소 검색
- `get_address_by_id()` - ID로 주소 조회  
- `add_new_address()` - 새 주소 추가
- `update_address()` - 주소 수정
- `delete_address()` - 주소 삭제

### 📧 이메일 관리
- `send_estimate_email()` - 견적서 이메일 전송
- `test_email_connection()` - 연결 테스트
- `get_email_server_info()` - 서버 정보
- `create_simple_estimate()` - 간단한 견적 생성

## 🚀 사용 방법

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 에이전트 사용
```python
from interior_agents import interior_agent

# 자연어로 요청
response = interior_agent.process("주소 목록을 조회해주세요")
print(response)

# 견적서 이메일 전송
response = interior_agent.process(
    "test@naver.com으로 월배아파트 견적서를 전송해주세요"
)
```

## 🔗 MCP 서버 연결

### Firebase MCP 서버
- **URL**: `https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp`
- **기능**: Firestore 데이터 관리, 주소 정보 저장

### Email MCP 서버  
- **URL**: `https://estimate-email-mcp-638331849453.asia-northeast3.run.app/mcp`
- **기능**: 견적서 이메일 전송, 템플릿 적용

## 💡 v2.0 주요 개선사항

### ❌ 제거된 복잡성
- `firebase_client.py` (319줄) 완전 삭제
- MCP 프로토콜 직접 구현 제거
- 복잡한 세션 관리 제거
- 과도한 에러 처리 로직 제거

### ✅ 추가된 간편성
- ADK `call_mcp_tool()` 직접 사용
- 각 기능을 독립적인 함수로 분리
- 표준 ADK Agent 구조 적용
- 최소한의 의존성만 유지

## 🏗️ 아키텍처

```
사용자 요청
    ↓
ADK Agent (interior_agent)
    ↓
도구 함수 (search_addresses, send_estimate_email, etc.)
    ↓
call_mcp_tool() → MCP 서버
    ↓
Firebase/Email 서비스
```

## 📈 성능 비교

| 항목 | v1.0 (기존) | v2.0 (신규) |
|------|------------|------------|
| 코드 라인 수 | ~1000줄 | ~200줄 |
| 파일 수 | 4개 (복잡) | 4개 (간단) |
| 의존성 | 15+ 패키지 | 1개 패키지 |
| 유지보수성 | 어려움 | 쉬움 |
| 확장성 | 복잡 | 간단 |

## 🎉 결론

**ADK MCP 직접 사용 방식**으로 완전히 재구성하여:
- 🎯 **80% 코드 감소**
- ⚡ **단순성 극대화** 
- 🔧 **유지보수 용이성**
- 📦 **의존성 최소화**

이제 **정말 간단한 에이전트 시스템**이 되었습니다! 🚀