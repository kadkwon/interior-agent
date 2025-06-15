# 🏠 인테리어 에이전트 - 모바일 최적화 시스템

> **Google ADK 기반 멀티 에이전트 시스템 + 모바일 우선 UI**

## 🎯 시스템 개요

```
📱 모바일 챗봇 UI (Streamlit) 
       ↓ HTTP 요청
🌐 FastAPI 서버 (단순 인터페이스)
       ↓ 직접 호출
🤖 루트 에이전트 (Google ADK)
       ↓ 도구 활용
🔧 29개 전문 도구 (Firebase, 스케줄, 주소 등)
```

## 🚀 빠른 시작

### 1️⃣ 전체 시스템 한 번에 실행
```bash
python start_system.py
```

### 2️⃣ 개별 실행 (개발용)
```bash
# 1단계: FastAPI 서버 시작
python simple_api_server.py

# 2단계: 모바일 챗봇 UI 시작 (새 터미널)
cd mobile_chatbot
streamlit run main.py
```

## 📱 접속 URL

- **📱 모바일 챗봇**: http://localhost:8501
- **🌐 API 서버**: http://localhost:8505  
- **📖 API 문서**: http://localhost:8505/docs

## 🗂️ 프로젝트 구조

```
📁 interior-agent/
├── 🚀 start_system.py              # 통합 실행 스크립트
├── 🌐 simple_api_server.py         # 단순 FastAPI 서버
├── 📁 mobile_chatbot/              # 모바일 최적화 UI
│   ├── 🎨 main.py                 # 메인 챗봇 UI
│   └── 📦 requirements.txt         # UI 의존성
├── ✅ interior_multi_agent/        # 핵심 에이전트 (기존 유지)
│   ├── 🤖 interior_agents/        # 루트 에이전트 + 29개 도구
│   └── 🏗️ chatbot_architecture_guide.md
└── 📋 README.md                   # 이 파일
```

## 🎨 UI 특징

### 📱 **모바일 우선 설계**
- **반응형 디자인**: 스마트폰 → 태블릿 → 데스크톱 최적화
- **터치 친화적**: 큰 버튼, 쉬운 조작
- **상태 표시**: 실시간 연결 상태 확인
- **빠른 입력**: 하단 고정 입력창

### 🖥️ **데스크톱 호환**
- **사이드바 레이아웃**: 넓은 화면 활용
- **키보드 단축키**: Enter로 메시지 전송
- **큰 화면 최적화**: 더 많은 정보 표시

## 🔧 API 엔드포인트

### `POST /chat`
```json
{
  "message": "인테리어 일정을 확인해줘",
  "session_id": "session_123"
}
```

### `GET /health`
```json
{
  "status": "healthy",
  "agent_available": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

## 🛠️ 기술 스택

| **구성요소** | **기술** | **역할** |
|-------------|---------|----------|
| **UI** | Streamlit + 반응형 CSS | 모바일 최적화 챗봇 |
| **API** | FastAPI | 단순 HTTP 인터페이스 |
| **에이전트** | Google ADK | 멀티 에이전트 시스템 |
| **도구** | Firebase + 커스텀 | 29개 전문 도구 |

## 🎯 주요 기능

### 🏠 **인테리어 전문 서비스**
- ✅ 스케줄 관리 (17개 함수)
- ✅ 주소 관리 (5개 함수)
- ✅ Firebase 연동 (5개 함수)
- ✅ 지급 계획 (3개 함수)

### 📱 **모바일 최적화**
- ✅ 반응형 디자인
- ✅ 터치 우선 인터페이스
- ✅ 실시간 상태 표시
- ✅ 빠른 응답 시간

### 🔗 **API 통합**
- ✅ RESTful API
- ✅ 자동 문서 생성
- ✅ 에러 처리
- ✅ 세션 관리

## 🚨 트러블슈팅

### ❌ **에이전트 로드 실패**
```bash
# 의존성 재설치
pip install -r requirements_fastapi.txt
pip install -r mobile_chatbot/requirements.txt

# Google ADK 설정 확인
python -c "from interior_agents import root_agent; print('✅ 에이전트 로드 성공')"
```

### ❌ **포트 충돌**
```bash
# 포트 8505, 8501 사용 중 확인
netstat -an | grep :8505
netstat -an | grep :8501

# 프로세스 종료 후 재시작
python start_system.py
```

### ❌ **모바일에서 접속 안됨**
```bash
# 방화벽 설정 확인
# 네트워크 IP로 접속: http://[IP]:8501
```

## 📊 성능 최적화

- **⚡ FastAPI**: 비동기 처리로 빠른 응답
- **🎨 Streamlit**: 효율적인 UI 렌더링  
- **🤖 Google ADK**: 최적화된 에이전트 런타임
- **📱 반응형 CSS**: 디바이스별 최적화

## 🔄 시스템 흐름

1. **📱 사용자** → 모바일 챗봇에서 메시지 입력
2. **🌐 FastAPI** → HTTP 요청 수신, 루트 에이전트 호출
3. **🤖 루트 에이전트** → 요청 분석, 적절한 도구 선택
4. **🔧 도구 실행** → Firebase, 스케줄, 주소 등 작업 수행
5. **📤 응답 반환** → 결과를 모바일 UI로 전송

## 📈 확장 계획

### **Phase 2: Vertex AI 통합**
- 🔄 Vertex AI Agent Engine 배포
- 📈 엔터프라이즈급 스케일링
- 🔒 고급 보안 및 모니터링

### **Phase 3: 고급 기능**
- 🎤 음성 인터페이스
- 📸 이미지 분석
- 🌐 다국어 지원

---

## 💡 사용 팁

1. **📱 모바일 사용 시**: 하단 입력창 활용
2. **🖥️ 데스크톱 사용 시**: Enter 키로 빠른 전송  
3. **🔍 연결 상태**: 우측 상단 상태 표시기 확인
4. **❓ 도움말**: "도움말" 또는 "사용법"으로 기능 안내

**🎉 준비 완료! 인테리어 전문가와 대화를 시작하세요!** 