#!/bin/bash

# 🧪 Interior Agent FastAPI - 로컬 Docker 테스트 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 설정값
IMAGE_NAME="interior-agent-api"
CONTAINER_NAME="interior-agent-test"
PORT="8506"

echo -e "${BLUE}🧪 로컬 Docker 테스트 시작${NC}"

# 1. 기존 컨테이너 정리
echo -e "\n${BLUE}1️⃣ 기존 컨테이너 정리${NC}"
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

# 2. Docker 이미지 빌드
echo -e "\n${BLUE}2️⃣ Docker 이미지 빌드${NC}"
docker build -t ${IMAGE_NAME} .

# 3. 컨테이너 실행
echo -e "\n${BLUE}3️⃣ 컨테이너 실행${NC}"
docker run -d \
  --name ${CONTAINER_NAME} \
  -p ${PORT}:8080 \
  --env-file .env \
  ${IMAGE_NAME}

# 4. 서비스 시작 대기
echo -e "\n${BLUE}4️⃣ 서비스 시작 대기 (10초)${NC}"
sleep 10

# 5. 테스트 수행
echo -e "\n${BLUE}5️⃣ 서비스 테스트${NC}"

echo "Health Check..."
curl -s http://localhost:${PORT}/health | python -m json.tool

echo -e "\nStatus Check..."
curl -s http://localhost:${PORT}/status | python -m json.tool

echo -e "\nChat 테스트..."
curl -X POST http://localhost:${PORT}/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요!", "session_id": "test-session"}' | python -m json.tool

# 6. 로그 확인 (선택사항)
echo -e "\n${BLUE}6️⃣ 컨테이너 로그 (최근 20줄)${NC}"
docker logs --tail 20 ${CONTAINER_NAME}

echo -e "\n${GREEN}✅ 로컬 테스트 완료!${NC}"
echo -e "${GREEN}서비스 URL: http://localhost:${PORT}${NC}"
echo -e "${GREEN}Health Check: http://localhost:${PORT}/health${NC}"
echo -e "${GREEN}Status Check: http://localhost:${PORT}/status${NC}"
echo -e "\n${YELLOW}컨테이너 중지: docker stop ${CONTAINER_NAME}${NC}"
echo -e "${YELLOW}컨테이너 제거: docker rm ${CONTAINER_NAME}${NC}" 