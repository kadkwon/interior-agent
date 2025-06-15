# Firebase MCP API

Firebase MCP 도구들을 웹에서 사용할 수 있도록 HTTP API로 제공하는 서비스입니다.

## 🎯 목적
- 구글 A2A(AI to AI)에서 Firebase 기능을 웹으로 사용
- Firebase MCP 프로토콜을 HTTP REST API로 변환
- Firestore와 Storage를 중심으로 한 Firebase 도구 제공

## 🚀 배포된 API 엔드포인트

### Base URL
```
https://us-central1-interior-one-click.cloudfunctions.net
```

### 📋 사용 가능한 API들

#### 1. 🔥 Core APIs
- `GET /firebaseGetProject` - Firebase 프로젝트 정보 조회

#### 2. 🗄️ Firestore APIs  
- `POST /firestoreGetDocuments` - Firestore 문서 조회

#### 3. 📋 API 목록
- `GET /mcpListApis` - 사용 가능한 모든 API 목록 조회

## 💻 사용 예시

### API 목록 확인
```bash
curl https://us-central1-interior-one-click.cloudfunctions.net/mcpListApis
```

### Firestore 문서 조회
```bash
curl -X POST https://us-central1-interior-one-click.cloudfunctions.net/firestoreGetDocuments \
  -H "Content-Type: application/json" \
  -d '{
    "paths": ["users/user123", "posts/post456"]
  }'
```

## 🔧 로컬 개발

```bash
# Functions 폴더로 이동
cd functions

# 의존성 설치 (이미 완료)
npm install

# 로컬 에뮬레이터 실행
npm run serve
```

## 📦 배포

```bash
# Firebase Functions에 배포
npm run deploy
```

## 🛠️ 기술 스택
- Firebase Functions
- Firebase Admin SDK  
- Node.js 22
- CORS 지원 