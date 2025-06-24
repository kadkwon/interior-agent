#!/bin/bash
# 🚀 Estimate Email MCP 서버 시작 스크립트

echo "🔧 Estimate Email MCP 서버 시작 준비..."

# 현재 디렉토리를 스크립트 위치로 변경
cd "$(dirname "$0")"

# Python 가상환경 확인
if [ ! -d "venv" ]; then
    echo "📦 Python 가상환경을 생성합니다..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔌 가상환경을 활성화합니다..."
source venv/bin/activate

# 의존성 패키지 설치
echo "📋 의존성 패키지를 설치/업데이트합니다..."
pip install -r requirements.txt

# 설정 확인
echo "⚙️ 서버 설정을 확인합니다..."
python config.py

# MCP 서버 시작
echo ""
echo "🚀 Estimate Email MCP 서버를 시작합니다..."
echo "📡 서버 주소: http://localhost:8001"
echo "🔧 지원 도구: send_estimate_email, test_connection"
echo ""
echo "⏹️  서버를 중지하려면 Ctrl+C를 누르세요."
echo ""

python server.py 