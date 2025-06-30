# 🚀 Interior Agent API - Cloud Run 배포 가이드

## 📋 필수 준비사항

### 1. Google Cloud 설정
```bash
# gcloud CLI 설치 및 로그인
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 필수 API 활성화
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. 환경변수 설정
```bash
# .env 파일 생성 (실제 값으로 변경)
cp .env_backup.txt .env
# .env 파일 편집하여 실제 API 키들 입력
```

## 🏃‍♂️ 빠른 배포 (자동화)

### Linux/Mac에서
```bash
# 프로젝트 ID 설정
export PROJECT_ID="your-gcp-project-id"

# 배포 실행
chmod +x deploy.sh
./deploy.sh
```

### Windows PowerShell에서
```powershell
# 환경변수 설정
$env:PROJECT_ID = "your-gcp-project-id"

# 배포 명령어 직접 실행
gcloud builds submit --tag gcr.io/$env:PROJECT_ID/interior-agent-api .
gcloud run deploy interior-agent-api --image gcr.io/$env:PROJECT_ID/interior-agent-api --platform managed --region asia-northeast3 --allow-unauthenticated --port 8080 --memory 2Gi --cpu 1 --max-instances 10
```

## 🧪 로컬 테스트

### Docker로 로컬 테스트
```bash
# 이미지 빌드
docker build -t interior-agent-api .

# 컨테이너 실행
docker run -p 8506:8080 --env-file .env interior-agent-api

# 테스트
curl http://localhost:8506/health
curl http://localhost:8506/status
```

### 자동 테스트 스크립트 (Linux/Mac)
```bash
chmod +x local-test.sh
./local-test.sh
```

## 📦 수동 배포 단계

### 1. Docker 이미지 빌드
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/interior-agent-api .
```

### 2. Cloud Run 배포
```bash
gcloud run deploy interior-agent-api \
  --image gcr.io/YOUR_PROJECT_ID/interior-agent-api \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 80 \
  --timeout 300 \
  --set-env-vars="NODE_ENV=production,PYTHONUNBUFFERED=1"
```

### 3. 환경변수 추가 (필요시)
```bash
# Secret Manager 사용
gcloud secrets create interior-env-vars --data-file=.env
gcloud run services update interior-agent-api \
  --region asia-northeast3 \
  --update-secrets="/app/.env=interior-env-vars:latest"
```

## 🔍 배포 후 확인

### 서비스 URL 확인
```bash
gcloud run services describe interior-agent-api \
  --region=asia-northeast3 \
  --format="value(status.url)"
```

### Health Check
```bash
curl https://YOUR_SERVICE_URL/health
curl https://YOUR_SERVICE_URL/status
```

### Chat API 테스트
```bash
curl -X POST https://YOUR_SERVICE_URL/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요!", "session_id": "test"}'
```

## 🛠️ 트러블슈팅

### 자주 발생하는 문제들

#### 1. ADK 로드 실패
- **증상**: "ADK 루트에이전트 로드 실패" 에러
- **해결**: 환경변수 확인, google-adk 패키지 설치 확인

#### 2. 메모리 부족
- **증상**: 컨테이너 재시작 반복
- **해결**: `--memory 4Gi`로 메모리 증가

#### 3. 타임아웃 에러
- **증상**: 응답 시간 초과
- **해결**: `--timeout 600`으로 타임아웃 증가

### 로그 확인
```bash
# Cloud Run 로그 확인
gcloud logs read --service=interior-agent-api --region=asia-northeast3 --limit=50

# 실시간 로그 모니터링
gcloud logs tail --service=interior-agent-api --region=asia-northeast3
```

## 🔄 업데이트 배포

### 코드 변경 후 재배포
```bash
# 새 이미지 빌드 및 배포
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/interior-agent-api .
gcloud run services update interior-agent-api \
  --region asia-northeast3 \
  --image gcr.io/YOUR_PROJECT_ID/interior-agent-api
```

### 트래픽 점진적 배포
```bash
# 새 버전을 50%만 배포
gcloud run services update-traffic interior-agent-api \
  --region asia-northeast3 \
  --to-revisions=LATEST=50
```

## 💰 비용 최적화

### 최소 인스턴스 0으로 설정
```bash
gcloud run services update interior-agent-api \
  --region asia-northeast3 \
  --min-instances 0
```

### 요청당 과금을 위한 concurrency 조정
```bash
gcloud run services update interior-agent-api \
  --region asia-northeast3 \
  --concurrency 100
```

## 🔐 보안 설정

### 인증 필요 설정
```bash
gcloud run services remove-iam-policy-binding interior-agent-api \
  --region asia-northeast3 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

### VPC 연결 (필요시)
```bash
gcloud run services update interior-agent-api \
  --region asia-northeast3 \
  --vpc-connector YOUR_VPC_CONNECTOR
``` 