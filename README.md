# 🏠 인테리어 에이전트 - Firebase MCP 연동 시스템

> **React 챗봇 + FastAPI + Firebase MCP 서버**

## 🎯 시스템 개요

```
📱 React 챗봇 UI (port:3000)
       ↓ HTTP 요청
🌐 FastAPI 서버 (port:8505) 
       ↓ MCP 프로토콜
🔥 Firebase MCP 서버 (Remote)
       ↓ Firebase API
☁️ Firebase Firestore/Storage
```

## 🚀 빠른 시작

### 1️⃣ FastAPI 서버 시작
```bash
python simple_api_server.py
```

### 2️⃣ React 챗봇 시작 (새 터미널)
```bash
cd mobile_chatbot
npm install
npm start
```

## 📱 접속 URL

- **📱 React 챗봇**: http://localhost:3000
- **🌐 API 서버**: http://localhost:8505  
- **📖 API 문서**: http://localhost:8505/docs
- **🔥 Firebase MCP**: https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp

## 🗂️ 프로젝트 구조

```
📁 interior-agent/
├── 🌐 simple_api_server.py         # Firebase MCP 연동 FastAPI 서버
├── 📁 mobile_chatbot/              # React 챗봇 UI
│   ├── 📁 src/
│   │   ├── 🎨 Chat.js             # 메인 챗봇 컴포넌트
│   │   ├── 🎨 Chat.css            # 챗봇 스타일
│   │   └── 📱 App.js              # React 앱
│   ├── 📦 package.json            # React 의존성
│   └── 🌐 public/index.html       # HTML 템플릿
├── 📁 firebase-mcp/               # Firebase MCP 서버 소스
└── 📋 README.md                   # 이 파일
```

## 🎨 React 챗봇 특징

### 📱 **모바일 우선 설계**
- **반응형 디자인**: 스마트폰 → 태블릿 → 데스크톱 최적화
- **터치 친화적**: 큰 버튼, 쉬운 조작
- **실시간 상태**: Firebase 연결 상태 표시
- **고정 입력창**: 하단 고정으로 편리한 입력

### 🖥️ **데스크톱 호환**
- **넓은 화면 활용**: 더 많은 메시지 표시
- **키보드 단축키**: Enter로 메시지 전송
- **스크롤 최적화**: 자동 스크롤 및 커스텀 스크롤바

## 🔧 API 엔드포인트

### `POST /chat`
```json
{
  "message": "주소 목록을 보여줘",
  "session_id": "react-session-123"
}
```

### `GET /health`
```json
{
  "status": "healthy",
  "agent_available": true,
  "firebase_connected": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

### `GET /addresses`
```json
{
  "result": {
    "content": [...]
  }
}
```

## 🛠️ 기술 스택

| **구성요소** | **기술** | **역할** |
|-------------|---------|----------|
| **UI** | React 18 + CSS | 모바일 최적화 챗봇 |
| **API** | FastAPI + Uvicorn | Firebase MCP 연동 서버 |
| **MCP 서버** | Firebase MCP (Remote) | Firebase 도구 제공 |
| **데이터베이스** | Firebase Firestore | 주소 데이터 저장 |

## 🔥 Firebase MCP 기능

### 📄 **Firestore 관리**
- ✅ 문서 추가 (`firestore_add_document`)
- ✅ 문서 목록 조회 (`firestore_list_documents`)
- ✅ 문서 조회 (`firestore_get_document`)
- ✅ 문서 수정 (`firestore_update_document`)
- ✅ 문서 삭제 (`firestore_delete_document`)

### 📂 **Storage 관리**
- ✅ 파일 업로드 (`storage_upload`)
- ✅ 파일 목록 (`storage_list_files`)
- ✅ 파일 정보 (`storage_get_file_info`)

### 👤 **Authentication**
- ✅ 사용자 조회 (`auth_get_user`)

## 🎯 주요 기능

### 🏠 **인테리어 주소 관리**
- ✅ 주소 저장 (자동 키워드 감지)
- ✅ 주소 목록 조회
- ✅ 실시간 Firebase 연동
- ✅ 타임스탬프 추가

### 📱 **React UI 기능**
- ✅ 서버 상태 실시간 표시
- ✅ 메시지 타임스탬프
- ✅ Firebase 도구 사용 표시
- ✅ 로딩 애니메이션
- ✅ 에러 처리

### 🔗 **MCP 프로토콜 준수**
- ✅ 표준 MCP 초기화
- ✅ 세션 관리
- ✅ SSE 응답 처리
- ✅ 올바른 헤더 사용

## 🚨 트러블슈팅

### ❌ **Firebase MCP 연결 실패**
```bash
# 서버 상태 확인
curl http://localhost:8505/health

# Firebase MCP 서버 직접 테스트
curl https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp
```

### ❌ **React 앱 빌드 오류**
```bash
cd mobile_chatbot
npm install
npm start
```

### ❌ **포트 충돌**
```bash
# 포트 8505, 3000 확인
netstat -an | grep :8505
netstat -an | grep :3000

# 프로세스 종료
taskkill /F /IM node.exe
taskkill /F /IM python.exe
```

## 📊 성능 최적화

- **⚡ FastAPI**: 비동기 MCP 클라이언트로 빠른 응답
- **⚛️ React**: 효율적인 상태 관리 및 렌더링  
- **🔥 Firebase MCP**: 원격 서버로 확장성 보장
- **📱 반응형 CSS**: 디바이스별 최적화

## 🔄 시스템 흐름

1. **📱 사용자** → React 챗봇에서 메시지 입력
2. **🌐 FastAPI** → HTTP 요청 수신, 키워드 분석
3. **🔥 Firebase MCP** → MCP 프로토콜로 도구 호출
4. **☁️ Firebase** → Firestore/Storage 작업 수행
5. **📤 응답 반환** → 결과를 React UI로 전송

## 📈 확장 계획

### **Phase 2: 고급 기능**
- 🎤 음성 인터페이스
- 📸 이미지 업로드 및 분석
- 🌐 다국어 지원
- 📊 대시보드 추가

### **Phase 3: 엔터프라이즈**
- 🔒 인증 시스템
- 📈 사용량 모니터링
- 🔄 자동 백업
- 🌐 PWA 변환

---

## 💡 사용 팁

1. **📱 모바일 사용 시**: 하단 입력창 활용
2. **🖥️ 데스크톱 사용 시**: Enter 키로 빠른 전송  
3. **🔍 연결 상태**: 헤더의 상태 표시기 확인
4. **🏠 주소 관리**: "주소 저장", "주소 목록" 키워드 사용

## 🔑 주요 키워드

- **주소 저장**: "주소 저장해줘", "주소 등록"
- **주소 조회**: "주소 목록", "주소 보여줘"
- **일반 상담**: "인테리어", "리모델링", "예산"

**🎉 준비 완료! Firebase 연동 인테리어 에이전트와 대화를 시작하세요!** 