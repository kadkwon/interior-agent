#!/bin/bash
# 🚀 Estimate Email MCP 서버 클라우드런 배포 스크립트

set -e  # 에러 발생 시 중단

echo "🚀 Estimate Email MCP 서버 클라우드런 배포 시작..."

# 프로젝트 설정
PROJECT_ID="interior-one-click"
REGION="asia-northeast3"
SERVICE_NAME="estimate-email-mcp"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "📋 배포 설정:"
echo "  - 프로젝트: $PROJECT_ID"
echo "  - 리전: $REGION"
echo "  - 서비스명: $SERVICE_NAME"
echo "  - 이미지: $IMAGE_NAME"
echo ""

# 1. Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker build -t $IMAGE_NAME:latest .

# 2. 이미지를 Container Registry에 푸시
echo "📤 Container Registry에 이미지 푸시 중..."
docker push $IMAGE_NAME:latest

# 3. Cloud Run에 배포
echo "🚀 Cloud Run에 배포 중..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 10 \
  --set-env-vars "MCP_TRANSPORT=http,PYTHONUNBUFFERED=1" \
  --project $PROJECT_ID

# 4. 서비스 URL 가져오기
echo "🔗 배포된 서비스 URL 확인 중..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID)

echo ""
echo "✅ 배포 완료!"
echo "🌐 서비스 URL: $SERVICE_URL"
echo "🏥 Health Check: $SERVICE_URL/health"
echo "🔗 MCP 엔드포인트: $SERVICE_URL/mcp"
echo "📊 서비스 정보: $SERVICE_URL/"
echo ""
echo "🧪 테스트 명령:"
echo "  curl $SERVICE_URL/health"
echo "  curl $SERVICE_URL/"
echo ""
echo "🔧 MCP 클라이언트에서 사용할 URL:"
echo "  $SERVICE_URL/mcp" 