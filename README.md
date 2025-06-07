# 🏠🔥 Interior Firebase System

**인테리어 업무 자동화를 위한 통합 AI 시스템**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![Firebase](https://img.shields.io/badge/Firebase-Functions-orange.svg)](https://firebase.google.com/)
[![ADK](https://img.shields.io/badge/Google-ADK-red.svg)](https://github.com/google/agent-development-kit)

## 📋 **프로젝트 개요**

인테리어 업계의 **현장 업무 자동화**와 **고객 관리**를 위한 통합 AI 시스템입니다. 
Google ADK 기반의 멀티 에이전트와 Firebase Cloud Functions를 통해 실시간 데이터 접근 및 업무 처리를 자동화합니다.

## 🏗️ **시스템 구조**

```
Interior Firebase System/
├── 🏠 interior_multi_agent/     # Python ADK 멀티 에이전트 시스템
│   ├── agent.py                 # 메인 ADK 에이전트
│   ├── interior_agents/         # Firebase 클라이언트 & 서브 에이전트
│   ├── requirements.txt         # Python 의존성
│   └── README.md               # ADK 에이전트 가이드
│
├── 🔥 firebase-mcp-api/        # Firebase Cloud Functions API 서버
│   ├── functions/              # Cloud Functions 소스코드
│   ├── firebase.json           # Firebase 설정
│   ├── package.json            # Node.js 의존성
│   └── README.md              # API 서버 가이드
│
└── 📚 이 README.md             # 통합 프로젝트 가이드
```

## 🚀 **주요 기능**

### **🤖 AI 에이전트 기능 (interior_multi_agent)**
- ✅ **음성/텍스트 명령어 처리**: "schedules 컬렉션을 조회해서"
- ✅ **Firestore 데이터 조회**: 고객, 일정, 주소, 견적 등
- ✅ **Firebase Storage 관리**: 파일 업로드/다운로드
- ✅ **Firebase Auth 사용자 관리**: 사용자 정보 조회
- ✅ **실시간 현장 업무 지원**: 일정 관리, 자재 확인 등

### **🔥 Firebase API 서버 (firebase-mcp-api)**
- ✅ **Firestore CRUD 작업**: 컬렉션/문서 읽기/쓰기
- ✅ **Firebase Storage 관리**: 파일 업로드/다운로드
- ✅ **Firebase Auth 관리**: 사용자 인증/권한
- ✅ **실시간 데이터 동기화**: 실시간 업데이트 지원
- ✅ **HTTP API 엔드포인트**: RESTful API 제공

## 🛠️ **기술 스택**

| 구분 | 기술 | 용도 |
|---|---|---|
| **AI 에이전트** | Python 3.8+, Google ADK | 자연어 처리 및 업무 자동화 |
| **백엔드 API** | Node.js 18+, Firebase Functions | 서버리스 API 서버 |
| **데이터베이스** | Firebase Firestore | NoSQL 문서 데이터베이스 |
| **파일 저장소** | Firebase Storage | 클라우드 파일 스토리지 |
| **인증** | Firebase Auth | 사용자 인증 시스템 |
| **배포** | Firebase Hosting, Cloud Functions | 서버리스 배포 |

## 📦 **설치 및 실행**

### **1️⃣ 전체 프로젝트 클론**

```bash
git clone https://github.com/YOUR_USERNAME/interior-firebase-system.git
cd interior-firebase-system
```

### **2️⃣ Python ADK 에이전트 설정**

```bash
cd interior_multi_agent

# 가상환경 생성 및 활성화
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# ADK 에이전트 실행
adk web
```

### **3️⃣ Firebase API 서버 설정**

```bash
cd firebase-mcp-api

# Node.js 의존성 설치
npm install

# Firebase CLI 설치 (전역)
npm install -g firebase-tools

# Firebase 로그인
firebase login

# Cloud Functions 배포
firebase deploy --only functions
```

## 🔧 **사용법**

### **🤖 ADK 에이전트 사용법**

1. **웹 브라우저에서 접속**: `http://localhost:8000`
2. **음성 또는 텍스트로 명령어 입력**:

```
✅ 지원되는 명령어 예시:
• "schedules 컬렉션을 조회해서"
• "customers 컬렉션에서 최근 고객 10명 보여줘"
• "Firebase 프로젝트 정보를 알려줘"
• "Firestore 컬렉션 목록을 보여줘"
• "Firebase Storage 파일 목록을 확인해줘"
```

### **🔥 Firebase API 직접 호출**

```bash
# Firestore 컬렉션 조회
curl -X POST https://us-central1-interior-one-click.cloudfunctions.net/firestoreQueryCollection \
  -H "Content-Type: application/json" \
  -d '{"collectionPath": "schedules", "limit": 10}'

# Firebase 프로젝트 정보
curl https://us-central1-interior-one-click.cloudfunctions.net/getFirebaseProjectInfo
```

## 📊 **프로젝트 성과**

### **✅ 완료된 기능**
- [x] Firebase Cloud Functions API 서버 구축 (11개 엔드포인트)
- [x] ADK 멀티 에이전트 시스템 구현
- [x] Firestore 데이터 실시간 조회 (55개 컬렉션)
- [x] Firebase Storage 파일 관리 (46개 파일)
- [x] 사용자 인증 및 권한 관리
- [x] 음성/텍스트 명령어 처리
- [x] 웹 인터페이스 제공

### **📈 시스템 현황**
- **Firebase 프로젝트**: `interior-one-click`
- **Firestore 컬렉션**: 55개 (customers, schedules, addresses 등)
- **Storage 파일**: 46개
- **API 엔드포인트**: 11개 
- **지원 언어**: 한국어 음성/텍스트 처리

## 🔒 **보안 및 권한**

- ✅ **Firebase Security Rules**: Firestore 접근 제어
- ✅ **IAM 권한 관리**: Cloud Functions 실행 권한
- ✅ **API 키 보안**: 환경변수로 관리
- ✅ **CORS 설정**: 브라우저 접근 제어

## 🐛 **문제 해결**

### **일반적인 문제들**

#### **1. 컬렉션 조회 실패**
```bash
# 해결: API 파라미터 형식 확인
# ❌ {"collection": "schedules"}
# ✅ {"collectionPath": "schedules"}
```

#### **2. ADK 웹 인터페이스 실행 실패**
```bash
# 해결: 가상환경 활성화 확인
cd interior_multi_agent
.venv\Scripts\activate  # Windows
adk web
```

#### **3. Firebase 권한 오류**
```bash
# 해결: Firebase 로그인 상태 확인
firebase login:list
firebase use interior-one-click
```

## 📚 **추가 문서**

- **[interior_multi_agent/README.md](./interior_multi_agent/README.md)**: ADK 에이전트 상세 가이드
- **[firebase-mcp-api/README.md](./firebase-mcp-api/README.md)**: Firebase API 서버 가이드
- **[interior_multi_agent/README_Firebase_Integration.md](./interior_multi_agent/README_Firebase_Integration.md)**: Firebase 통합 가이드

## 👥 **기여하기**

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 **라이선스**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 **연락처**

프로젝트에 대한 문의나 지원이 필요하시면 이슈를 생성해주세요.

---

**🎯 Interior Firebase System** - 인테리어 업무의 미래를 만들어갑니다! 🚀 