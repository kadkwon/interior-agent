# 🚀 Vertex AI Agent Engine 배포 가이드

**인테리어 멀티 에이전트**를 Vertex AI Agent Engine에 배포하는 완전 가이드입니다.

## 📋 목차

1. [배포 개요](#배포-개요)
2. [사전 요구사항](#사전-요구사항)
3. [환경 설정](#환경-설정)
4. [배포 단계](#배포-단계)
5. [배포 확인](#배포-확인)
6. [문제 해결](#문제-해결)
7. [모니터링](#모니터링)

## 🎯 배포 개요

### Vertex AI Agent Engine이란?

**Vertex AI Agent Engine**은 Google Cloud의 완전 관리형 AI 에이전트 배포 서비스입니다.

#### 주요 특징:
- ✅ **완전 관리형**: 인프라 관리 없이 자동 확장
- 🔒 **보안**: VPC-SC 준수, IAM 통합
- 🌐 **다중 프레임워크**: LangGraph, LangChain, AG2, CrewAI 지원
- 📊 **모니터링**: Cloud Trace, Cloud Logging 통합

### 현재 프로젝트 배포 준비도

```
✅ Google ADK 기반 에이전트      (완료)
✅ 모듈화된 구조               (완료)  
✅ Firebase 연동 기능          (완료)
✅ 패키지 구조 적합성          (완료)
🔧 Agent Engine 호환 설정      (이 가이드에서 완료)
```

## 🔧 사전 요구사항

### 시스템 요구사항

| 항목 | 요구사항 | 확인 방법 |
|------|----------|-----------|
| Python | 3.9 - 3.12 | `python --version` |
| Google Cloud CLI | 최신버전 | `gcloud --version` |
| Git | 최신버전 | `git --version` |

### Google Cloud 설정

1. **Google Cloud 프로젝트**
   ```bash
   # 프로젝트 생성 (신규 프로젝트인 경우)
   gcloud projects create YOUR_PROJECT_ID
   
   # 프로젝트 설정
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **결제 계정 연결**
   - Google Cloud Console에서 결제 계정 연결 필수

3. **필수 API 활성화**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   gcloud services enable cloudtrace.googleapis.com
   gcloud services enable logging.googleapis.com
   ```

## ⚙️ 환경 설정

### 1단계: 자동 환경 설정 (권장)

가장 빠른 방법으로 모든 환경을 자동 설정합니다:

```bash
# 저장소 클론 (필요시)
git clone <repository-url>
cd interior_multi_agent

# 자동 환경 설정 실행
python setup_deployment.py
```

이 스크립트는 다음을 자동으로 수행합니다:
- ✅ Python 버전 확인
- ✅ Google Cloud CLI 설정 확인
- ✅ 필수 API 활성화
- ✅ Cloud Storage 스테이징 버킷 생성
- ✅ 서비스 계정 설정
- ✅ 의존성 패키지 설치
- ✅ 환경설정 파일 생성

### 2단계: 수동 환경 설정 (고급 사용자)

자동 설정이 실패하거나 커스터마이징이 필요한 경우:

#### 가상환경 생성
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate     # Windows
```

#### 의존성 설치
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 환경설정 파일 생성
```bash
cp deployment.env.template .env
# .env 파일을 편집하여 실제 값 입력
```

## 🚀 배포 단계

### 문서 요구사항에 따른 5단계 배포 프로세스

Vertex AI Agent Engine 문서의 배포 단계를 정확히 구현했습니다:

#### 1단계: 패키지 요구사항 정의 ✅
```python
# deployment_requirements.txt에 정의됨
google-cloud-aiplatform[adk,agent_engines]==1.50.0
google-adk==0.1.0
# ...기타 패키지들
```

#### 2단계: 추가 패키지 설정 ✅
```python
# 프로젝트 소스 디렉터리 자동 포함
extra_packages = ["interior_agents"]
```

#### 3단계: Cloud Storage 디렉터리 구성 ✅
```python
# 환경별 고유 디렉터리 생성
gcs_dir_name = f"{environment}-{timestamp}-{uuid}"
```

#### 4단계: 리소스 메타데이터 정의 ✅
```python
# 배포 환경별 메타데이터
display_name = "인테리어 멀티 에이전트 (production)"
description = "Firebase 연동 인테리어 프로젝트 관리 AI - v1.0.0 [production]"
labels = {"environment": "production", "version": "1-0-0"}
```

#### 5단계: AgentEngine 인스턴스 만들기 ✅
```python
remote_agent = agent_engines.create(
    root_agent,                          # 필수 로컬 에이전트
    requirements=agent_config['requirements'],     # 1단계
    extra_packages=agent_config['extra_packages'], # 2단계  
    gcs_dir_name=agent_config['gcs_dir_name'],    # 3단계
    display_name=agent_config['display_name'],     # 4단계
    description=agent_config['description'],
    labels=agent_config['labels']
)
```

### 실제 배포 실행

#### 개발 환경 배포
```bash
# 기본 개발 환경 배포
python deploy.py --environment development

# 검증만 수행 (dry-run)
python deploy.py --environment development --dry-run

# 자세한 로그와 함께
python deploy.py --environment development --verbose
```

#### 스테이징 환경 배포
```bash
python deploy.py --environment staging --region us-central1
```

#### 프로덕션 환경 배포
```bash
# 아시아 지역 배포 (한국 사용자 최적)
python deploy.py --environment production --region asia-northeast1

# 유럽 지역 배포
python deploy.py --environment production --region europe-west1
```

## ✅ 배포 확인

### 배포 성공 확인

배포가 성공하면 다음과 같은 출력을 볼 수 있습니다:

```
🎉 Vertex AI Agent Engine 배포 완료!
============================================================
📍 리소스 ID: projects/12345/locations/asia-northeast1/reasoningEngines/67890
🌍 배포 환경: production
📦 프로젝트: your-project-id
🌐 지역: asia-northeast1
🗄️ 스테이징 버킷: gs://your-project-id-agent-staging
📂 GCS 디렉터리: production-20241215-143022-a1b2c3d4
📅 배포 시간: 20241215-143022
📋 패키지 개수: 9
============================================================
```

### 배포된 에이전트 테스트

#### Python 코드로 테스트
```python
# 배포된 에이전트 조회
from vertexai import agent_engines

# 모든 배포된 에이전트 목록
agents = agent_engines.list()
print("배포된 에이전트들:", agents)

# 특정 에이전트 조회
resource_name = "projects/.../reasoningEngines/..."
remote_agent = agent_engines.get(resource_name)

# 에이전트 쿼리 테스트
response = remote_agent.query("안녕하세요! 인테리어 프로젝트 도움이 필요합니다.")
print("응답:", response)
```

#### gcloud CLI로 확인
```bash
# Vertex AI 리소스 목록 조회
gcloud ai endpoints list --region=asia-northeast1

# Agent Engine 상태 확인
gcloud ai models list --region=asia-northeast1
```

## 🛠️ 문제 해결

### 일반적인 문제와 해결책

#### 1. 패키지 설치 오류
```bash
❌ ERROR: Could not find a version that satisfies the requirement google-cloud-aiplatform[adk,agent_engines]
```
**해결책:**
```bash
# pip 업그레이드
pip install --upgrade pip

# 캐시 클리어 후 재설치
pip cache purge
pip install -r requirements.txt
```

#### 2. 권한 오류
```bash
❌ ERROR: User does not have permission to access project
```
**해결책:**
```bash
# 인증 다시 설정
gcloud auth application-default login
gcloud auth login

# 프로젝트 확인
gcloud config get-value project
```

#### 3. API 활성화 오류
```bash
❌ ERROR: API [aiplatform.googleapis.com] not enabled
```
**해결책:**
```bash
# 필수 API 활성화
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

#### 4. Agent Engine 배포 실패
```bash
❌ Agent Engine 배포 실패: Invalid agent configuration
```
**해결책:**
1. 에이전트 코드 검증
2. requirements.txt 패키지 버전 확인
3. 환경변수 설정 확인
4. Firebase 연결 상태 확인

### 로그 파일 확인

배포 실행 시 자동으로 생성되는 로그 파일을 확인하세요:
```bash
# 최신 배포 로그 확인
ls -la deployment_*.log
cat deployment_20241215_143022.log
```

## 📊 모니터링

### Cloud Console에서 모니터링

1. **Vertex AI Console**
   - https://console.cloud.google.com/vertex-ai
   - Agent Engine 섹션에서 배포된 에이전트 확인

2. **Cloud Trace**
   - https://console.cloud.google.com/traces
   - 에이전트 성능 및 응답 시간 모니터링

3. **Cloud Logging**
   - https://console.cloud.google.com/logs
   - 에이전트 실행 로그 및 오류 확인

### 성능 모니터링

```python
# 에이전트 성능 메트릭 수집
import time

start_time = time.time()
response = remote_agent.query("테스트 쿼리")
end_time = time.time()

print(f"응답 시간: {end_time - start_time:.2f}초")
print(f"응답 길이: {len(response)} 문자")
```

### 비용 모니터링

- **Vertex AI 요금**: https://console.cloud.google.com/billing
- **Agent Engine 사용량**: Vertex AI Console에서 확인
- **예상 월간 비용**: Cloud Billing에서 예산 알림 설정 권장

## 🔄 업데이트 및 관리

### 에이전트 업데이트

```bash
# 코드 수정 후 재배포
python deploy.py --environment staging

# 프로덕션 업데이트 (신중하게)
python deploy.py --environment production --region asia-northeast1
```

### 배포된 에이전트 삭제

```python
# Python 코드로 삭제
remote_agent.delete()

# 또는 gcloud CLI로 삭제
gcloud ai models delete REASONING_ENGINE_ID --region=asia-northeast1
```

## 📚 추가 자료

### 공식 문서
- [Vertex AI Agent Engine 개요](https://cloud.google.com/vertex-ai/docs/agent-engine/overview)
- [Agent Engine 배포 가이드](https://cloud.google.com/vertex-ai/docs/agent-engine/deploy)
- [Agent Engine 사용법](https://cloud.google.com/vertex-ai/docs/agent-engine/use)

### 커뮤니티 자료
- [Google Cloud 공식 GitHub](https://github.com/GoogleCloudPlatform/generative-ai)
- [Agent Development Kit (ADK) 문서](https://google.github.io/adk-docs/)

## 🆘 지원

### 문제 신고
1. GitHub Issues에 문제 등록
2. 로그 파일 첨부
3. 환경 정보 포함 (OS, Python 버전, etc.)

### 연락처
- 📧 이메일: support@your-domain.com
- 💬 Slack: #interior-agent-support
- 🐛 GitHub Issues: [Repository Issues](https://github.com/your-repo/issues)

---

**🎉 축하합니다! Vertex AI Agent Engine 배포가 완료되었습니다.**

이제 **클라우드에서 실행되는 AI 에이전트**를 통해 인테리어 프로젝트를 효율적으로 관리할 수 있습니다! 