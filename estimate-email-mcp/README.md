# 📧 Estimate Email MCP 서버

TypeScript 기반 MCP(Model Context Protocol) 서버로 견적서 이메일 전송 기능을 제공합니다.

## 🎯 역할

- Claude에서 Firebase MCP로 조회한 견적서 데이터를 받아서
- **직접 Cloud Functions API를 호출**하여 PDF 첨부 이메일 전송
- Firebase-MCP와 동일한 구조로 완벽한 호환성 보장

## 🔄 동작 플로우

```
Claude (Cursor/Web)
    ↓ (자연어 파싱)
Firebase MCP (리모트)
    ↓ (견적서 데이터 조회)
Estimate Email MCP (리모트)
    ↓ (Cloud Functions 직접 호출)
PDF 생성 + Gmail API
    ↓ (결과 반환)
Claude → 사용자
```

## 🛠️ 로컬 개발

### 1. 의존성 설치
```bash
cd estimate-email-mcp
npm install
```

### 2. 개발 서버 실행
```bash
npm run dev
```

서버는 `http://localhost:8080`에서 실행됩니다.

### 3. 프로덕션 빌드
```bash
npm run build
npm start
```

## 🚀 배포

서버는 Google Cloud Run에 배포되어 있습니다:
- **URL**: `https://estimate-email-mcp-638331849453.asia-northeast3.run.app`
- **MCP 엔드포인트**: `/mcp`
- **헬스체크**: `/`

### Docker 빌드 및 배포
```bash
# 이미지 빌드
docker build -t gcr.io/interior-one-click/estimate-email-mcp:latest .

# 이미지 푸시
docker push gcr.io/interior-one-click/estimate-email-mcp:latest

# Cloud Run 배포
gcloud run deploy estimate-email-mcp \
  --image gcr.io/interior-one-click/estimate-email-mcp:latest \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1
```

## 🔧 Cursor 연동 설정

`.cursor/mcp.json`에 설정:

```json
{
  "mcpServers": {
    "firebase": {
      "url": "https://firebase-mcp-638331849453.asia-northeast3.run.app/mcp"
    },
    "estimate-email": {
      "url": "https://estimate-email-mcp-638331849453.asia-northeast3.run.app/mcp"
    }
  }
}
```

## 📋 지원 도구

### `send_estimate_email`
견적서를 이메일로 전송합니다.

**매개변수:**
- `email`: 수신자 이메일 주소
- `address`: 견적서 주소  
- `process_data`: 공정 데이터 리스트
- `notes`: 견적서 메모 (선택사항)
- `hidden_processes`: 숨김 공정 설정 (선택사항)
- `corporate_profit`: 기업이윤 설정 (선택사항)
- `subject`: 이메일 제목 (선택사항)
- `template_content`: 이메일 본문 (선택사항)

### `test_connection`
MCP 서버 연결 상태를 테스트합니다.

### `get_server_info`
서버 정보 및 설정을 조회합니다.

## ⚙️ 설정

`src/config.ts`에서 설정 관리:

- **서버 설정**: 호스트, 포트, 이름, 버전
- **Cloud Functions**: API URL
- **이메일 설정**: 타임아웃, 템플릿, 기본 기업이윤

## 🧪 테스트

### 헬스체크
```bash
curl https://estimate-email-mcp-638331849453.asia-northeast3.run.app/
```

### 로컬 테스트
```bash
npm run dev
curl http://localhost:8080/
```

## 🚀 실제 사용 예시

Cursor에서:

```
"gncloud86@naver.com에 월배아이파크 1차 109동 2401호_2차 견적서를 보내줘"
```

1. Firebase MCP가 견적서 데이터 조회
2. Estimate Email MCP가 Cloud Functions 직접 호출
3. PDF 생성 및 Gmail로 전송
4. 결과를 Claude에 반환

## 🔑 핵심 특징

- ✅ **Firebase-MCP 동일 구조**: 완벽한 호환성과 안정성
- ✅ **TypeScript**: 타입 안정성과 표준 Node.js 환경
- ✅ **StreamableHTTPServerTransport**: 세션 기반 통신
- ✅ **Cloud Run 최적화**: 컨테이너 기반 무상태 서비스
- ✅ **기존 코드 재사용**: PDF 생성 및 이메일 로직 보존
- ✅ **개선된 이메일 형식**: ▶ 기호 사용, 공정 간 줄바꿈

## 📞 문제 해결

### 포트 충돌
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID번호> /F
```

### Cloud Functions 연결 실패
- URL 확인: `https://us-central1-interior-one-click.cloudfunctions.net/sendEstimatePdfHttp`
- 네트워크 연결 상태 확인
- 타임아웃 설정 조정 (src/config.ts)

## 🔍 모니터링

### Cloud Run 로그
```bash
gcloud logs read --service estimate-email-mcp --limit 50
```

### 실시간 로그
```bash
gcloud logs tail --service estimate-email-mcp
```

## 📁 프로젝트 구조

```
estimate-email-mcp/
├── src/
│   ├── index.ts                 # 메인 서버
│   ├── config.ts               # 설정 관리
│   ├── utils/
│   │   └── logger.ts           # 로깅 유틸리티
│   └── transports/
│       ├── index.ts            # Transport 팩토리
│       └── http.ts             # HTTP transport
├── dist/                       # 빌드 결과물
├── package.json
├── tsconfig.json
├── Dockerfile
└── README.md
```

## 🎉 성공 요인

Firebase-MCP의 검증된 구조를 활용하여:
- 표준 MCP SDK 사용 (`@modelcontextprotocol/sdk`)
- TypeScript로 타입 안정성 확보
- Cloud Run에 최적화된 배포
- Claude와 완벽한 호환성 달성 