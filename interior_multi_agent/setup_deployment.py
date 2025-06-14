#!/usr/bin/env python3
"""
🔧 Vertex AI Agent Engine 배포 환경 설정 스크립트
초기 배포 환경 구성 및 필수 리소스 생성
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def print_header(title: str):
    """제목 출력"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print('='*60)

def run_command(cmd: str, check: bool = True) -> tuple:
    """명령어 실행"""
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            check=check
        )
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_prerequisites():
    """사전 요구사항 확인"""
    print_header("사전 요구사항 확인")
    
    # Python 버전 확인
    python_version = sys.version_info
    if python_version.major != 3 or python_version.minor < 9 or python_version.minor > 12:
        print(f"❌ Python 버전 오류: {python_version.major}.{python_version.minor}")
        print("💡 Python 3.9-3.12 버전이 필요합니다")
        return False
    else:
        print(f"✅ Python 버전: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # gcloud CLI 확인
    success, stdout, stderr = run_command("gcloud --version", check=False)
    if success:
        print("✅ Google Cloud CLI 설치됨")
    else:
        print("❌ Google Cloud CLI 필요")
        print("💡 설치 방법: https://cloud.google.com/sdk/docs/install")
        return False
    
    # 현재 프로젝트 확인
    success, stdout, stderr = run_command("gcloud config get-value project", check=False)
    if success and stdout.strip():
        project_id = stdout.strip()
        print(f"✅ 현재 프로젝트: {project_id}")
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    else:
        print("❌ Google Cloud 프로젝트 설정 필요")
        print("💡 설정 방법: gcloud config set project YOUR_PROJECT_ID")
        return False
    
    return True

def enable_apis():
    """필수 API 활성화"""
    print_header("Google Cloud API 활성화")
    
    required_apis = [
        "aiplatform.googleapis.com",
        "storage.googleapis.com",
        "secretmanager.googleapis.com",
        "cloudtrace.googleapis.com",
        "logging.googleapis.com"
    ]
    
    for api in required_apis:
        print(f"🔄 {api} 활성화 중...")
        success, stdout, stderr = run_command(f"gcloud services enable {api}")
        if success:
            print(f"✅ {api} 활성화 완료")
        else:
            print(f"❌ {api} 활성화 실패: {stderr}")
            return False
    
    return True

def create_staging_bucket():
    """스테이징 버킷 생성"""
    print_header("Cloud Storage 스테이징 버킷 생성")
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    bucket_name = f"{project_id}-agent-staging"
    
    # 버킷 존재 확인
    success, stdout, stderr = run_command(f"gsutil ls gs://{bucket_name}", check=False)
    if success:
        print(f"✅ 스테이징 버킷 이미 존재: gs://{bucket_name}")
        return True
    
    # 버킷 생성
    print(f"🔄 스테이징 버킷 생성 중: gs://{bucket_name}")
    success, stdout, stderr = run_command(f"gsutil mb gs://{bucket_name}")
    if success:
        print(f"✅ 스테이징 버킷 생성 완료: gs://{bucket_name}")
        
        # 버킷 레이블 설정
        labels = {
            "purpose": "agent-engine-staging",
            "environment": "multi-env",
            "project": "interior-agent"
        }
        
        label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        run_command(f"gsutil label set {label_str} gs://{bucket_name}", check=False)
        
        return True
    else:
        print(f"❌ 스테이징 버킷 생성 실패: {stderr}")
        return False

def setup_service_account():
    """서비스 계정 설정"""
    print_header("서비스 계정 설정")
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    sa_name = "agent-engine-deployer"
    sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
    
    # 서비스 계정 존재 확인
    success, stdout, stderr = run_command(f"gcloud iam service-accounts describe {sa_email}", check=False)
    if success:
        print(f"✅ 서비스 계정 이미 존재: {sa_email}")
    else:
        # 서비스 계정 생성
        print(f"🔄 서비스 계정 생성 중: {sa_email}")
        success, stdout, stderr = run_command(
            f"gcloud iam service-accounts create {sa_name} "
            f"--display-name='Agent Engine Deployer' "
            f"--description='Vertex AI Agent Engine 배포용 서비스 계정'"
        )
        if success:
            print(f"✅ 서비스 계정 생성 완료: {sa_email}")
        else:
            print(f"❌ 서비스 계정 생성 실패: {stderr}")
            return False
    
    # 필수 역할 부여
    required_roles = [
        "roles/aiplatform.user",
        "roles/storage.admin",
        "roles/secretmanager.admin",
        "roles/logging.writer",
        "roles/cloudtrace.agent"
    ]
    
    for role in required_roles:
        print(f"🔄 역할 부여 중: {role}")
        success, stdout, stderr = run_command(
            f"gcloud projects add-iam-policy-binding {project_id} "
            f"--member='serviceAccount:{sa_email}' "
            f"--role='{role}'"
        )
        if success:
            print(f"✅ 역할 부여 완료: {role}")
        else:
            print(f"⚠️ 역할 부여 실패: {role} - {stderr}")
    
    # 서비스 계정 키 생성
    key_file = f"{sa_name}-key.json"
    if not os.path.exists(key_file):
        print(f"🔄 서비스 계정 키 생성 중: {key_file}")
        success, stdout, stderr = run_command(
            f"gcloud iam service-accounts keys create {key_file} "
            f"--iam-account={sa_email}"
        )
        if success:
            print(f"✅ 서비스 계정 키 생성 완료: {key_file}")
            print(f"🔐 GOOGLE_APPLICATION_CREDENTIALS={os.path.abspath(key_file)}")
        else:
            print(f"❌ 서비스 계정 키 생성 실패: {stderr}")
            return False
    else:
        print(f"✅ 서비스 계정 키 이미 존재: {key_file}")
    
    return True

def install_dependencies():
    """의존성 패키지 설치"""
    print_header("의존성 패키지 설치")
    
    # requirements.txt 확인
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt 파일이 없습니다")
        return False
    
    # 가상환경 확인
    if not os.getenv("VIRTUAL_ENV"):
        print("⚠️ 가상환경이 활성화되지 않았습니다")
        print("💡 다음 명령으로 가상환경을 생성하고 활성화하세요:")
        print("   python -m venv .venv")
        print("   source .venv/bin/activate  # Linux/Mac")
        print("   .venv\\Scripts\\activate   # Windows")
        
        # 계속 진행할지 확인
        response = input("계속 진행하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # pip 업그레이드
    print("🔄 pip 업그레이드 중...")
    success, stdout, stderr = run_command("pip install --upgrade pip")
    if success:
        print("✅ pip 업그레이드 완료")
    
    # 의존성 설치
    print("🔄 의존성 패키지 설치 중...")
    success, stdout, stderr = run_command("pip install -r requirements.txt")
    if success:
        print("✅ 의존성 패키지 설치 완료")
    else:
        print(f"❌ 의존성 패키지 설치 실패: {stderr}")
        return False
    
    return True

def create_env_file():
    """환경설정 파일 생성"""
    print_header("환경설정 파일 생성")
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    # 템플릿에서 .env 파일 생성
    template_file = "deployment.env.template"
    env_file = ".env"
    
    if os.path.exists(env_file):
        print(f"✅ 환경설정 파일 이미 존재: {env_file}")
        return True
    
    if not os.path.exists(template_file):
        print(f"❌ 템플릿 파일 없음: {template_file}")
        return False
    
    # 템플릿 읽기
    with open(template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # 값 치환
    env_content = template_content.replace(
        "your-project-id", project_id
    ).replace(
        "your-project-id-agent-staging", f"{project_id}-agent-staging"
    )
    
    # .env 파일 생성
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ 환경설정 파일 생성 완료: {env_file}")
    print("💡 실제 API 키와 Firebase 설정을 입력하세요")
    
    return True

def validate_setup():
    """설정 검증"""
    print_header("설정 검증")
    
    # Python 모듈 import 테스트
    try:
        import vertexai
        from vertexai import agent_engines
        print("✅ Vertex AI SDK 설치 확인")
    except ImportError as e:
        print(f"❌ Vertex AI SDK 설치 오류: {e}")
        return False
    
    try:
        from interior_agents import root_agent
        print("✅ 프로젝트 에이전트 로드 확인")
    except ImportError as e:
        print(f"❌ 프로젝트 에이전트 로드 오류: {e}")
        return False
    
    # 환경변수 확인
    required_env_vars = [
        "GOOGLE_CLOUD_PROJECT"
    ]
    
    for var in required_env_vars:
        if os.getenv(var):
            print(f"✅ 환경변수 설정: {var}")
        else:
            print(f"❌ 환경변수 누락: {var}")
            return False
    
    print("✅ 모든 설정 검증 완료")
    return True

def print_next_steps():
    """다음 단계 안내"""
    print_header("배포 준비 완료")
    
    print("🎉 Vertex AI Agent Engine 배포 환경 설정이 완료되었습니다!")
    print()
    print("📋 다음 단계:")
    print("1. .env 파일을 편집하여 실제 API 키와 Firebase 설정을 입력하세요")
    print("2. 배포 스크립트를 실행하세요:")
    print("   python deploy.py --environment development")
    print()
    print("🔧 개발 환경 배포:")
    print("   python deploy.py --environment development")
    print()
    print("🚀 프로덕션 환경 배포:")
    print("   python deploy.py --environment production --region asia-northeast1")
    print()
    print("📚 관련 문서:")
    print("   - Agent Engine 문서: https://cloud.google.com/vertex-ai/docs/agent-engine")
    print("   - 배포 가이드: https://cloud.google.com/vertex-ai/docs/agent-engine/deploy")
    print()

def main():
    """메인 실행 함수"""
    print("🚀 Vertex AI Agent Engine 배포 환경 설정 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    setup_steps = [
        ("사전 요구사항 확인", check_prerequisites),
        ("Google Cloud API 활성화", enable_apis),
        ("Cloud Storage 스테이징 버킷 생성", create_staging_bucket),
        ("서비스 계정 설정", setup_service_account),
        ("의존성 패키지 설치", install_dependencies),
        ("환경설정 파일 생성", create_env_file),
        ("설정 검증", validate_setup),
    ]
    
    for i, (step_name, step_func) in enumerate(setup_steps, 1):
        print(f"\n{'='*50}")
        print(f"📋 {i}단계: {step_name}")
        print('='*50)
        
        if not step_func():
            print(f"❌ {i}단계 실패: {step_name}")
            print("💡 오류를 해결한 후 다시 실행하세요")
            return False
        
        print(f"✅ {i}단계 완료: {step_name}")
    
    print_next_steps()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 