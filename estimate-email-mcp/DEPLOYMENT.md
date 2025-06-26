# 🚀 Estimate Email MCP 서버 클라우드런 배포 가이드

## 📋 개요

이 가이드는 Estimate Email MCP 서버를 Google Cloud Run에 배포하는 방법을 설명합니다.

## 🎯 배포 목표

- **Firebase MCP**: `https://firebase-mcp-xxxxx.asia-northeast3.run.app/mcp` ✅
- **Estimate Email MCP**: `https://estimate-email-mcp-xxxxx.asia-northeast3.run.app/mcp` 🎯

## 📦 배포 준비 사항

### 1. 필수 도구 설치
```bash
# Google Cloud SDK 설치 확인
gcloud --version

# Docker 설치 확인
docker --version

# 프로젝트 설정
gcloud config set project interior-one-click
gcloud auth configure-docker
```

### 2. 환경 설정
```bash
# 환경 변수 설정
export PROJECT_ID="interior-one-click"
export REGION="asia-northeast3"
export SERVICE_NAME="estimate-email-mcp"
```

## 🚀 배포 방법

### 방법 1: 자동 배포 스크립트 (권장)

```bash
# 배포 스크립트 실행
./deploy.sh
```

### 방법 2: 수동 배포

```bash
# 1. Docker 이미지 빌드
docker build -t gcr.io/$PROJECT_ID/estimate-email-mcp:latest .

# 2. 이미지 푸시
docker push gcr.io/$PROJECT_ID/estimate-email-mcp:latest

# 3. Cloud Run 배포
gcloud run deploy estimate-email-mcp \
  --image gcr.io/$PROJECT_ID/estimate-email-mcp:latest \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 10 \
  --set-env-vars "MCP_TRANSPORT=http,PYTHONUNBUFFERED=1"
```

### 방법 3: Cloud Build 자동화

```bash
# Cloud Build 트리거 생성
gcloud builds submit --config cloudbuild.yaml .
```

## 🔧 배포 후 확인

### 1. Health Check
```bash
curl https://estimate-email-mcp-xxxxx.asia-northeast3.run.app/health
```

예상 응답:
```json
{
  "status": "healthy",
  "service": "estimate-email-mcp",
  "version": "1.0.0",
  "transport": "http",
  "cloud_run": true
}
```

### 2. 서비스 정보 확인
```bash
curl https://estimate-email-mcp-xxxxx.asia-northeast3.run.app/
```

### 3. MCP 엔드포인트 확인
```bash
# MCP 엔드포인트 (실제 MCP 클라이언트에서 사용할 URL)
https://estimate-email-mcp-xxxxx.asia-northeast3.run.app/mcp
```

## 🔗 MCP 클라이언트 연결

### Claude Desktop 설정 예시
```json
{
  "mcpServers": {
    "firebase-mcp": {
      "command": "npx",
      "args": ["-y", "@gannonh/firebase-mcp"],
      "env": {
        "MCP_TRANSPORT": "http",
        "MCP_SERVER_URL": "https://firebase-mcp-xxxxx.asia-northeast3.run.app/mcp"
      }
    },
    "estimate-email-mcp": {
      "command": "python",
      "args": ["-m", "mcp_client"],
      "env": {
        "MCP_TRANSPORT": "http", 
        "MCP_SERVER_URL": "https://estimate-email-mcp-xxxxx.asia-northeast3.run.app/mcp"
      }
    }
  }
}
```

### ADK Agent 연결 예시
```python
from google.adk.tools import MCPToolset

# Firebase MCP 연결
firebase_tools = MCPToolset(
    name="firebase_mcp",
    connection_params={
        "transport": "http",
        "url": "https://firebase-mcp-xxxxx.asia-northeast3.run.app/mcp"
    }
)

# Email MCP 연결  
email_tools = MCPToolset(
    name="email_mcp",
    connection_params={
        "transport": "http",
        "url": "https://estimate-email-mcp-xxxxx.asia-northeast3.run.app/mcp"
    }
)
```

## 🛠️ 지원 도구

배포된 서버에서 사용 가능한 MCP 도구:

1. **send_estimate_email**: 견적서 이메일 전송
2. **test_connection**: MCP 서버 연결 테스트  
3. **get_server_info**: 서버 정보 조회

## 📊 모니터링

### Cloud Run 로그 확인
```bash
gcloud logs read --service estimate-email-mcp --limit 50
```

### 실시간 로그 스트리밍
```bash
gcloud logs tail --service estimate-email-mcp
```

### 메트릭 확인
```bash
# 서비스 상태 확인
gcloud run services describe estimate-email-mcp --region asia-northeast3
```

## 🔄 업데이트 배포

코드 변경 후 재배포:

```bash
# 새 버전 배포
./deploy.sh

# 또는 수동으로
docker build -t gcr.io/$PROJECT_ID/estimate-email-mcp:latest .
docker push gcr.io/$PROJECT_ID/estimate-email-mcp:latest
gcloud run deploy estimate-email-mcp --image gcr.io/$PROJECT_ID/estimate-email-mcp:latest
```

## ⚠️ 트러블슈팅

### 1. 배포 실패
```bash
# 로그 확인
gcloud run services describe estimate-email-mcp --region asia-northeast3

# 이전 버전으로 롤백
gcloud run services update-traffic estimate-email-mcp --to-revisions=REVISION-NAME=100
```

### 2. Health Check 실패
- `requirements.txt`에 `requests` 패키지 포함 확인
- Dockerfile의 health check 명령어 확인
- 포트 8080 바인딩 확인

### 3. MCP 연결 실패
- `MCP_TRANSPORT=http` 환경변수 설정 확인
- 방화벽 및 인증 설정 확인
- 엔드포인트 URL 정확성 확인

## 🎉 배포 완료

배포가 성공하면 다음과 같은 구조로 두 개의 MCP 서버가 운영됩니다:

```
📡 Firebase MCP Server
├── 🔗 https://firebase-mcp-xxxxx.asia-northeast3.run.app/mcp
└── 🛠️ Firestore, Auth, Storage 도구

📧 Estimate Email MCP Server  
├── 🔗 https://estimate-email-mcp-xxxxx.asia-northeast3.run.app/mcp
└── 🛠️ 견적서 이메일 전송 도구
```

이제 Claude Web이나 ADK Agent에서 두 서버를 모두 활용할 수 있습니다! 🚀 