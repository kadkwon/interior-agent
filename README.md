# 🏠 인테리어 에이전트 - 통합 서버

**Firebase MCP + FastAPI + ADK 에이전트 통합 플랫폼**

## 📋 프로젝트 개요

인테리어 디자인과 프로젝트 관리를 위한 AI 에이전트 시스템입니다. 사용자는 채팅을 통해 인테리어 상담, 주소 관리, 프로젝트 스케줄링 등의 서비스를 이용할 수 있습니다.

### ✨ 주요 기능
- 🤖 **AI 인테리어 상담**: ADK 기반 전문 에이전트
- 🗂️ **주소 관리**: Firebase Firestore 기반 데이터 관리
- 📅 **스케줄 관리**: 프로젝트 일정 및 현장 관리
- 💬 **실시간 채팅**: React 기반 웹 인터페이스
- ☁️ **클라우드 배포**: Google Cloud Run 통합 서버

## 🏗️ 아키텍처

### 통합 서버 구조
```
통합 Docker 컨테이너 (Cloud Run)
├── 📱 React 클라이언트 → 🔗 Nginx (Port 8080) ← 외부 접근
├── 🐍 FastAPI 서버 (Port 8081) ← 내부 서비스
├── 🟢 Firebase MCP 서버 (Port 3000) ← 내부 서비스
└── 🔄 Nginx 리버스 프록시 ← 라우팅 관리
```

### 데이터 흐름
```
사용자 → React UI → FastAPI → Firebase MCP → Firebase
                  ↓
               ADK 에이전트 → 인테리어 전문 응답
```

## 📂 프로젝트 구조

```
interior-agent/
├── 📁 docs/                           # 문서 관리
│   ├── deployment/                    # 배포 관련 문서
│   │   ├── 통합_서버_배포_가이드.md    # 완전한 배포 가이드
│   │   ├── 통합_서버_빠른_실행_스크립트.sh  # 자동화 스크립트
│   │   ├── Dockerfile.integrated      # 통합 Docker 설정
│   │   ├── supervisord.conf          # 멀티 프로세스 관리
│   │   └── nginx.conf                # 리버스 프록시 설정
│   └── archive/                       # 구 문서 아카이브
├── 📁 firebase-mcp/                   # Firebase MCP 서버
│   ├── src/                          # TypeScript 소스
│   ├── dist/                         # 빌드된 JavaScript
│   └── package.json                  # Node.js 의존성
├── 📁 interior_multi_agent/           # ADK 에이전트 시스템
│   ├── interior_agents/              # 에이전트 구현체
│   │   ├── agent_main.py             # 루트 에이전트
│   │   └── address_management_agent.py  # 주소 관리 에이전트
│   └── requirements.txt              # Python 의존성
├── 📁 mobile_chatbot/                 # React 웹 앱
│   ├── src/                          # React 소스 코드
│   │   ├── App.js                    # 메인 앱 컴포넌트
│   │   ├── Chat.js                   # 채팅 인터페이스
│   │   └── Chat.css                  # 스타일링
│   └── package.json                  # React 의존성
├── 🐍 simple_api_server.py            # FastAPI 메인 서버
├── 📋 requirements_fastapi.txt        # FastAPI 의존성
└── 📚 README.md                       # 이 문서
```

## 🚀 빠른 시작

### 1️⃣ 전체 시스템 배포 (원클릭)
```bash
# 배포 스크립트 실행
bash docs/deployment/통합_서버_빠른_실행_스크립트.sh
```

### 2️⃣ 단계별 배포

#### 준비 단계
```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd interior-agent

# 2. Firebase MCP 빌드
cd firebase-mcp
npm install
npm run build
cd ..
```

#### 로컬 테스트
```bash
# Docker 빌드 및 실행
docker build -f docs/deployment/Dockerfile.integrated -t interior-integrated .
docker run -p 8080:8080 interior-integrated

# 테스트
curl http://localhost:8080/health
```

#### 프로덕션 배포
```bash
# Cloud Run 배포
gcloud run deploy interior-integrated \
  --source . \
  --dockerfile docs/deployment/Dockerfile.integrated \
  --region asia-northeast3 \
  --allow-unauthenticated
```

## 🔧 개발 환경 설정

### 로컬 개발 (개별 서비스)

#### FastAPI 서버
```bash
pip install -r requirements_fastapi.txt
python simple_api_server.py
# http://localhost:8505
```

#### React 앱
```bash
cd mobile_chatbot
npm install
npm start
# http://localhost:3000
```

#### Firebase MCP 서버
```bash
cd firebase-mcp
npm install
npm run dev
# http://localhost:3000
```

## 📊 API 엔드포인트

### 메인 API
- `GET /health` - 시스템 상태 확인
- `POST /chat` - AI 채팅 인터페이스
- `POST /firebase/tool` - Firebase 도구 직접 호출

### 예제 요청
```bash
# 채팅 요청
curl -X POST https://your-service-url/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요, 거실 인테리어 상담을 받고 싶어요"}'

# Firebase 도구 호출
curl -X POST https://your-service-url/firebase/tool \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "firestore_list_collections", "arguments": {"random_string": "test"}}'
```

## 🔐 환경 설정

### 필수 환경변수
```bash
# .env 파일 생성
GOOGLE_API_KEY=your_google_api_key
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

### Firebase 설정
- `firebase-mcp/interior-one-click-firebase-adminsdk-*.json` 서비스 계정 키 필요
- Firestore 데이터베이스 활성화
- Firebase Storage 버킷 설정

## 📈 모니터링

### 로그 확인
```bash
# Cloud Run 로그
gcloud logs read --service interior-integrated --region asia-northeast3

# 실시간 로그
gcloud logs tail --service interior-integrated --region asia-northeast3
```

### 서비스 상태
```bash
# 헬스체크
curl https://your-service-url/health

# 서비스 정보
gcloud run services describe interior-integrated --region asia-northeast3
```

## 🛠️ 트러블슈팅

### 일반적인 문제들

#### 1. 서비스 시작 실패
```bash
# 로그 확인
gcloud logs read --service interior-integrated --limit 50

# 메모리 부족 시 메모리 증가
gcloud run services update interior-integrated --memory 4Gi
```

#### 2. Firebase 연결 실패
- 서비스 계정 키 파일 경로 확인
- Firestore 데이터베이스 활성화 상태 확인
- 네트워크 방화벽 설정 점검

#### 3. React 앱 연결 실패
- CORS 설정 확인
- API URL 올바른지 확인
- 네트워크 연결 상태 점검

## 📚 문서

- 📖 [통합 서버 배포 가이드](docs/deployment/통합_서버_배포_가이드.md)
- 🚀 [자동화 배포 스크립트](docs/deployment/통합_서버_빠른_실행_스크립트.sh)
- 📂 [아카이브 문서](docs/archive/) - 이전 버전 문서들

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/amazing-feature`)
3. Commit your Changes (`git commit -m 'Add some amazing feature'`)
4. Push to the Branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 지원

문제가 있거나 질문이 있으시면 이슈를 생성해주세요.

---

**🏠 인테리어의 미래를 AI와 함께 만들어갑니다!** 