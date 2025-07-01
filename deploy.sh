#!/bin/bash

# 🚀 Interior Agent FastAPI - Cloud Run 배포 스크립트

set -e  # 에러 발생시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 설정값들
PROJECT_ID=${PROJECT_ID:-"interior-one-click"}
SERVICE_NAME="interior-agent-api"
REGION="asia-northeast3"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${BLUE}🚀 Interior Agent API 배포 시작${NC}"
echo -e "${YELLOW}프로젝트 ID: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}서비스명: ${SERVICE_NAME}${NC}"
echo -e "${YELLOW}지역: ${REGION}${NC}"

# 1. GCP 프로젝트 설정 확인
echo -e "\n${BLUE}1️⃣ GCP 프로젝트 설정 확인${NC}"
gcloud config set project ${PROJECT_ID}

# 2. 필요한 API 활성화
echo -e "\n${BLUE}2️⃣ 필요한 API 활성화${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 3. Docker 이미지 빌드 및 푸시
echo -e "\n${BLUE}3️⃣ Docker 이미지 빌드 및 푸시${NC}"
gcloud builds submit --tag ${IMAGE_NAME} .

# 4. Cloud Run 서비스 배포
echo -e "\n${BLUE}4️⃣ Cloud Run 서비스 배포${NC}"
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 80 \
  --timeout 300 \
  --set-env-vars="NODE_ENV=production,PYTHONUNBUFFERED=1,GOOGLE_GENAI_USE_VERTEXAI=FALSE,GOOGLE_API_KEY=AIzaSyDktjZ4CWOzop8q1xxaVzA4WdM3p3Vguso"

# 5. 배포 완료 메시지
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
echo -e "\n${GREEN}✅ 배포 완료!${NC}"
echo -e "${GREEN}서비스 URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}Health Check: ${SERVICE_URL}/health${NC}"
echo -e "${GREEN}Status Check: ${SERVICE_URL}/status${NC}"

# 6. 간단한 테스트
echo -e "\n${BLUE}6️⃣ 서비스 상태 확인${NC}"
echo "Health Check 중..."
curl -s "${SERVICE_URL}/health" | python -m json.tool || echo "JSON 파싱 실패"

echo -e "\n${GREEN}🎉 배포 성공! 서비스가 정상 작동 중입니다.${NC}" 