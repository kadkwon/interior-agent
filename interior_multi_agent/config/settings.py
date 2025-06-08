from datetime import datetime
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 앱 설정
APP_TITLE = "Interior Management System"
APP_DESCRIPTION = "인테리어 프로젝트 관리 시스템"
APP_VERSION = "1.0.0"

# 서버 설정
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# ADK 설정
ADK_API_KEY = os.getenv("ADK_API_KEY")
ADK_PROJECT_ID = os.getenv("ADK_PROJECT_ID")

# Agent 설정
LLM_MODEL = "gemini-2.0-flash"

# 데이터 저장소
project_data = {
    "sites": {}
} 