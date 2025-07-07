# Interior Agent FastAPI Server - Cloud Run 배포용
FROM python:3.11-slim

WORKDIR /app

# 🔧 UTF-8 로케일 설정 추가 (한글 깨짐 방지)
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    git \
    locales \
    && rm -rf /var/lib/apt/lists/*

# UTF-8 로케일 생성 및 설정
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=en_US.UTF-8

# Python 의존성 파일들 복사 (캐시 최적화)
COPY requirements_fastapi.txt ./
COPY interior_agent/requirements.txt ./interior_requirements.txt

# Python 의존성 설치
RUN pip install --no-cache-dir -r requirements_fastapi.txt
RUN pip install --no-cache-dir -r interior_requirements.txt

# 애플리케이션 코드 복사
COPY interior_agent/ ./interior_agent/
COPY simple_api_server.py ./
COPY firebase.json ./

# 환경변수는 Cloud Run에서 설정

# 비root 사용자 생성 (보안)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run 포트    
EXPOSE 8000

# 환경변수 설정
ENV PORT=8000
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 서버 실행
CMD ["python", "-m", "uvicorn", "simple_api_server:app", "--host", "0.0.0.0", "--port", "8000"] 