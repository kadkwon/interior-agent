#!/bin/bash

# 🚀 통합 서버 빠른 배포 스크립트

echo "=== 🏠 인테리어 에이전트 통합 서버 배포 시작 ==="

# 현재 디렉토리 확인
echo "📂 현재 디렉토리: $(pwd)"

# 1️⃣ 필수 파일들 존재 확인
echo "🔍 필수 파일들 확인 중..."

required_files=(
    "firebase-mcp/package.json"
    "interior_multi_agent"
    "simple_api_server.py"
    "requirements_fastapi.txt"
    "Dockerfile.integrated"
    "supervisord.conf"
    "nginx.conf"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -e "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ 누락된 필수 파일들:"
    printf '%s\n' "${missing_files[@]}"
    echo "위 파일들을 먼저 생성해주세요."
    exit 1
fi

echo "✅ 모든 필수 파일이 존재합니다."

# 2️⃣ Firebase MCP 빌드
echo "🔧 Firebase MCP 서버 빌드 중..."
cd firebase-mcp
if [ ! -d "node_modules" ]; then
    echo "📦 npm install 실행 중..."
    npm install --ignore-scripts
fi

echo "🏗️ npm run build 실행 중..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Firebase MCP 빌드 실패"
    exit 1
fi

cd ..
echo "✅ Firebase MCP 빌드 완료"

# 3️⃣ simple_api_server.py URL 확인 및 수정
echo "🔍 FastAPI 서버 설정 확인 중..."

if grep -q "localhost:3000/mcp" simple_api_server.py; then
    echo "✅ FastAPI 서버 URL이 이미 올바르게 설정되어 있습니다."
else
    echo "⚠️ FastAPI 서버 URL을 내부 통신용으로 수정 중..."
    
    # 백업 생성
    cp simple_api_server.py simple_api_server.py.backup
    
    # URL 수정
    sed -i 's|FIREBASE_MCP_URL = "https://firebase-mcp-[^"]*"|FIREBASE_MCP_URL = "http://localhost:3000/mcp"|g' simple_api_server.py
    
    if grep -q "localhost:3000/mcp" simple_api_server.py; then
        echo "✅ FastAPI 서버 URL 수정 완료"
    else
        echo "❌ URL 수정 실패. 수동으로 simple_api_server.py의 FIREBASE_MCP_URL을 'http://localhost:3000/mcp'로 변경해주세요."
        exit 1
    fi
fi

# 4️⃣ Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드 중..."
docker build -f Dockerfile.integrated -t interior-integrated .

if [ $? -ne 0 ]; then
    echo "❌ Docker 빌드 실패"
    exit 1
fi

echo "✅ Docker 이미지 빌드 완료"

# 5️⃣ 로컬 테스트 (선택사항)
read -p "🧪 로컬에서 테스트하시겠습니까? (y/N): " test_locally

if [[ $test_locally =~ ^[Yy]$ ]]; then
    echo "🚀 로컬 테스트 시작..."
    
    # 기존 컨테이너 정리
    docker stop interior-integrated-test 2>/dev/null || true
    docker rm interior-integrated-test 2>/dev/null || true
    
    # 컨테이너 실행
    docker run -d --name interior-integrated-test -p 8080:8080 interior-integrated
    
    echo "⏳ 서비스 시작 대기 중... (30초)"
    sleep 30
    
    # 헬스체크 테스트
    echo "🏥 헬스체크 테스트 중..."
    response=$(curl -s http://localhost:8080/health || echo "failed")
    
    if [[ $response == *"healthy"* ]]; then
        echo "✅ 로컬 테스트 성공!"
        echo "📊 응답: $response"
        
        # 채팅 API 테스트
        echo "💬 채팅 API 테스트 중..."
        chat_response=$(curl -s -X POST http://localhost:8080/chat \
            -H "Content-Type: application/json" \
            -d '{"message": "안녕하세요"}' || echo "failed")
        
        if [[ $chat_response == *"response"* ]]; then
            echo "✅ 채팅 API 테스트 성공!"
        else
            echo "⚠️ 채팅 API 테스트 실패: $chat_response"
        fi
    else
        echo "❌ 로컬 테스트 실패: $response"
        echo "🔍 컨테이너 로그 확인:"
        docker logs interior-integrated-test --tail 20
    fi
    
    # 컨테이너 정리
    docker stop interior-integrated-test
    docker rm interior-integrated-test
fi

# 6️⃣ Cloud Run 배포
read -p "☁️ Cloud Run에 배포하시겠습니까? (y/N): " deploy_cloud_run

if [[ $deploy_cloud_run =~ ^[Yy]$ ]]; then
    echo "☁️ Cloud Run 배포 시작..."
    
    # Google Cloud 프로젝트 확인
    current_project=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$current_project" ]; then
        read -p "📝 Google Cloud 프로젝트 ID를 입력해주세요: " project_id
        gcloud config set project $project_id
    else
        echo "📋 현재 프로젝트: $current_project"
        read -p "이 프로젝트에 배포하시겠습니까? (Y/n): " confirm_project
        if [[ $confirm_project =~ ^[Nn]$ ]]; then
            read -p "📝 새 프로젝트 ID를 입력해주세요: " project_id
            gcloud config set project $project_id
        fi
    fi
    
    # 리전 설정
    gcloud config set run/region asia-northeast3
    
    # Cloud Run 배포
    echo "🚀 Cloud Run 배포 실행 중..."
    gcloud run deploy interior-integrated \
        --source . \
        --dockerfile Dockerfile.integrated \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --timeout 300 \
        --concurrency 80 \
        --max-instances 10 \
        --region asia-northeast3
    
    if [ $? -eq 0 ]; then
        echo "✅ Cloud Run 배포 성공!"
        
        # 서비스 URL 가져오기
        service_url=$(gcloud run services describe interior-integrated \
            --region asia-northeast3 \
            --format 'value(status.url)')
        
        echo "🌐 서비스 URL: $service_url"
        echo "🏥 헬스체크: $service_url/health"
        echo "💬 채팅 API: $service_url/chat"
        
        # 배포 후 테스트
        read -p "🧪 배포된 서비스를 테스트하시겠습니까? (y/N): " test_deployed
        
        if [[ $test_deployed =~ ^[Yy]$ ]]; then
            echo "⏳ 서비스 시작 대기 중... (30초)"
            sleep 30
            
            echo "🏥 배포된 서비스 헬스체크 중..."
            deployed_response=$(curl -s $service_url/health || echo "failed")
            
            if [[ $deployed_response == *"healthy"* ]]; then
                echo "✅ 배포된 서비스 테스트 성공!"
                echo "📊 응답: $deployed_response"
            else
                echo "❌ 배포된 서비스 테스트 실패: $deployed_response"
                echo "🔍 로그 확인을 위해 다음 명령어를 실행하세요:"
                echo "gcloud logs read --service interior-integrated --region asia-northeast3"
            fi
        fi
        
    else
        echo "❌ Cloud Run 배포 실패"
        exit 1
    fi
fi

echo ""
echo "🎉 통합 서버 배포 스크립트 완료!"
echo ""
echo "📚 추가 정보:"
echo "- 문서: 통합_서버_배포_가이드.md"
echo "- 로그 확인: gcloud logs read --service interior-integrated --region asia-northeast3"
echo "- 서비스 관리: Google Cloud Console > Cloud Run"
echo ""
echo "❓ 문제가 있으면 통합_서버_배포_가이드.md의 트러블슈팅 섹션을 확인하세요." 