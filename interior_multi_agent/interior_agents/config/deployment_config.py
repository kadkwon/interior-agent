"""
Vertex AI Agent Engine 배포 설정 관리
문서 요구사항에 따른 배포 옵션 구현
"""

import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DeploymentConfig:
    """
    Agent Engine 배포 설정 관리 클래스
    문서 단계별 요구사항 구현:
    1. 패키지 요구사항 정의
    2. 추가 패키지 설정
    3. Cloud Storage 디렉터리 구성
    4. 리소스 메타데이터 정의
    """
    
    def __init__(self, environment: str = "development"):
        """
        배조 환경 초기화
        
        Args:
            environment: 배포 환경 (development, staging, production)
        """
        self.environment = environment
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # 환경변수에서 설정 로드
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = self._get_optimal_location()
        self.staging_bucket = self._get_staging_bucket()
        
        # 배포 메타데이터
        self.display_name = os.getenv("AGENT_DISPLAY_NAME", "인테리어 멀티 에이전트")
        self.description = os.getenv("AGENT_DESCRIPTION", "Firebase 연동 인테리어 프로젝트 관리 AI")
        self.version = os.getenv("AGENT_VERSION", "1.0.0")
        
        logger.info(f"✅ 배포 설정 초기화 완료: {self.environment} 환경")
    
    def _get_optimal_location(self) -> str:
        """
        문서 권장사항에 따른 최적 지역 선택
        """
        env_location = os.getenv("AGENT_ENGINE_LOCATION")
        if env_location:
            return env_location
            
        # 환경별 기본 위치 매핑
        location_map = {
            "development": "us-central1",
            "staging": "us-central1",
            "production": "asia-northeast1"  # 한국 사용자에게 최적
        }
        
        selected_location = location_map.get(self.environment, "us-central1")
        logger.info(f"📍 배포 지역 선택: {selected_location}")
        return selected_location
    
    def _get_staging_bucket(self) -> str:
        """
        Cloud Storage 스테이징 버킷 URI 생성
        """
        bucket_name = os.getenv("STAGING_BUCKET_NAME", f"{self.project_id}-agent-staging")
        return f"gs://{bucket_name}"
    
    # ========================================
    # 1단계: 패키지 요구사항 정의
    # ========================================
    def get_requirements(self) -> List[str]:
        """
        문서 모범 사례에 따른 패키지 요구사항 반환
        - 버전 고정 (재현 가능한 빌드)
        - 최소 의존성 원칙
        """
        base_requirements = [
            "google-cloud-aiplatform[adk,agent_engines]",
            "google-adk",
            "python-dotenv",
            "requests",
            "aiohttp"
        ]
        
        # 환경별 버전 정책
        if self.environment == "production":
            # 프로덕션: 정확한 버전 고정
            return [
                "google-cloud-aiplatform[adk,agent_engines]==1.50.0",
                "google-adk==0.1.0",
                "google-cloud-secret-manager==2.18.0",
                "google-cloud-storage==2.10.0",
                "python-dotenv==1.0.0",
                "requests==2.31.0",
                "aiohttp==3.8.6",
                "cloudpickle==2.2.1",
                "pydantic==2.5.3"
            ]
        else:
            # 개발/스테이징: 유연한 버전
            return [
                "google-cloud-aiplatform[adk,agent_engines]>=1.50.0",
                "google-adk>=0.1.0",
                "google-cloud-secret-manager>=2.18.0",
                "python-dotenv>=1.0.0",
                "requests>=2.31.0",
                "aiohttp>=3.8.0",
                "cloudpickle>=2.2.1",
                "pydantic>=2.5.0"
            ]
    
    # ========================================
    # 2단계: 추가 패키지 설정
    # ========================================
    def get_extra_packages(self) -> Optional[List[str]]:
        """
        문서 요구사항: 추가 패키지 정의
        - 로컬 파일 및 디렉터리 포함
        - 비공개 유틸리티 지원
        """
        extra_packages = []
        
        # 현재 프로젝트의 모든 소스 디렉터리 포함
        source_dirs = [
            "interior_agents",  # 메인 에이전트 패키지
        ]
        
        # 추가 파일이 있는지 확인
        additional_files = []
        if os.path.exists("deployment_requirements.txt"):
            additional_files.append("deployment_requirements.txt")
        
        all_packages = source_dirs + additional_files
        
        logger.info(f"📦 추가 패키지 포함: {all_packages}")
        return all_packages if all_packages else None
    
    # ========================================
    # 3단계: Cloud Storage 디렉터리 구성
    # ========================================
    def get_gcs_directory_name(self) -> str:
        """
        문서 요구사항: Cloud Storage 하위 버킷 구성
        - 환경별 분리로 충돌 방지
        - UUID 사용으로 고유성 보장
        """
        allow_overwrite = os.getenv("ALLOW_OVERWRITE_DEPLOYMENT", "false").lower() == "true"
        
        if allow_overwrite:
            # 환경별 고정 디렉터리 (덮어쓰기 허용)
            return f"{self.environment}"
        else:
            # UUID 사용으로 충돌 방지
            unique_id = str(uuid.uuid4())[:8]
            return f"{self.environment}-{self.timestamp}-{unique_id}"
    
    # ========================================
    # 4단계: 리소스 메타데이터 정의
    # ========================================
    def get_resource_metadata(self) -> Dict[str, Any]:
        """
        문서 요구사항: ReasoningEngine 리소스 메타데이터
        """
        return {
            "display_name": f"{self.display_name} ({self.environment})",
            "description": f"{self.description} - v{self.version} [{self.environment}]",
            "labels": {
                "environment": self.environment,
                "version": self.version.replace(".", "-"),
                "deployed_at": self.timestamp,
                "project_type": "interior-agent"
            }
        }
    
    # ========================================
    # 5단계: AgentEngine 생성 설정
    # ========================================
    def get_agent_engine_config(self) -> Dict[str, Any]:
        """
        문서 요구사항: agent_engines.create() 파라미터 구성
        """
        config = {
            "requirements": self.get_requirements(),
            "extra_packages": self.get_extra_packages(),
            "gcs_dir_name": self.get_gcs_directory_name(),
        }
        
        # 메타데이터 추가
        config.update(self.get_resource_metadata())
        
        logger.info(f"🚀 Agent Engine 설정 완료:")
        logger.info(f"   - 환경: {self.environment}")
        logger.info(f"   - 지역: {self.location}")
        logger.info(f"   - 스테이징 버킷: {self.staging_bucket}")
        logger.info(f"   - GCS 디렉터리: {config['gcs_dir_name']}")
        
        return config
    
    def get_vertex_ai_init_config(self) -> Dict[str, Any]:
        """
        Vertex AI 초기화 설정
        """
        return {
            "project": self.project_id,
            "location": self.location,
            "staging_bucket": self.staging_bucket
        }
    
    def validate_environment(self) -> bool:
        """
        배포 환경 검증
        """
        required_vars = [
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_APPLICATION_CREDENTIALS"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ 필수 환경변수 누락: {missing_vars}")
            return False
        
        logger.info("✅ 환경변수 검증 완료")
        return True
    
    def get_deployment_summary(self) -> Dict[str, Any]:
        """
        배포 요약 정보
        """
        return {
            "environment": self.environment,
            "project_id": self.project_id,
            "location": self.location,
            "staging_bucket": self.staging_bucket,
            "display_name": self.display_name,
            "version": self.version,
            "timestamp": self.timestamp,
            "requirements_count": len(self.get_requirements()),
            "extra_packages": self.get_extra_packages(),
            "gcs_directory": self.get_gcs_directory_name()
        } 