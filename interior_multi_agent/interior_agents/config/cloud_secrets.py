"""
Google Cloud Secret Manager를 활용한 보안 설정 관리
프로덕션 배포시 환경변수 대신 Secret Manager 사용 권장
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CloudSecretsManager:
    """
    Google Cloud Secret Manager 연동 클래스
    프로덕션 환경에서 민감한 정보 안전 관리
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Secret Manager 클라이언트 초기화
        
        Args:
            project_id: Google Cloud 프로젝트 ID
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.client = None
        
        # 프로덕션 환경에서만 Secret Manager 활성화
        self.use_secrets = os.getenv("DEPLOYMENT_ENVIRONMENT") == "production"
        
        if self.use_secrets:
            try:
                from google.cloud import secretmanager
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info("✅ Cloud Secret Manager 클라이언트 초기화됨")
            except ImportError:
                logger.warning("⚠️ google-cloud-secret-manager 패키지가 필요합니다")
                self.use_secrets = False
        else:
            logger.info("📝 개발 환경: 환경변수 사용")
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Secret Manager에서 비밀값 조회
        
        Args:
            secret_name: 시크릿 이름
            default: 기본값 (Secret Manager 사용 안 할 때)
        
        Returns:
            비밀값 또는 기본값
        """
        if not self.use_secrets or not self.client:
            # 개발 환경: 환경변수에서 조회
            return os.getenv(secret_name, default)
        
        try:
            secret_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.client.access_secret_version(request={"name": secret_path})
            secret_value = response.payload.data.decode('UTF-8')
            
            logger.debug(f"🔐 Secret 조회 성공: {secret_name}")
            return secret_value
        
        except Exception as e:
            logger.warning(f"⚠️ Secret 조회 실패 ({secret_name}): {e}")
            return os.getenv(secret_name, default)
    
    def get_firebase_config(self) -> Dict[str, Any]:
        """
        Firebase 설정 정보 조회 (Secret Manager 또는 환경변수)
        """
        config = {
            "project_id": self.get_secret("FIREBASE_PROJECT_ID"),
            "private_key_id": self.get_secret("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": self.get_secret("FIREBASE_PRIVATE_KEY"),
            "client_email": self.get_secret("FIREBASE_CLIENT_EMAIL"),
            "client_id": self.get_secret("FIREBASE_CLIENT_ID"),
            "auth_uri": self.get_secret("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": self.get_secret("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "type": "service_account"
        }
        
        # None 값 제거
        config = {k: v for k, v in config.items() if v is not None}
        
        if len(config) < 5:
            logger.warning("⚠️ Firebase 설정이 불완전합니다")
        else:
            logger.info("✅ Firebase 설정 로드 완료")
        
        return config
    
    def get_api_keys(self) -> Dict[str, str]:
        """
        API 키 정보 조회
        """
        return {
            "google_api_key": self.get_secret("GOOGLE_API_KEY"),
            "openai_api_key": self.get_secret("OPENAI_API_KEY"),  # 필요시
        }
    
    def create_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        새로운 Secret 생성 (관리자 도구)
        
        Args:
            secret_name: 시크릿 이름
            secret_value: 시크릿 값
        
        Returns:
            생성 성공 여부
        """
        if not self.use_secrets or not self.client:
            logger.info(f"📝 개발 환경: {secret_name} Secret 생성 스킵")
            return True
        
        try:
            parent = f"projects/{self.project_id}"
            
            # Secret 생성
            secret = {"replication": {"automatic": {}}}
            create_response = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_name,
                    "secret": secret
                }
            )
            
            # Secret 버전 추가
            self.client.add_secret_version(
                request={
                    "parent": create_response.name,
                    "payload": {"data": secret_value.encode('UTF-8')}
                }
            )
            
            logger.info(f"✅ Secret 생성 완료: {secret_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Secret 생성 실패 ({secret_name}): {e}")
            return False
    
    def setup_deployment_secrets(self) -> bool:
        """
        배포에 필요한 모든 Secret 설정 확인/생성
        """
        required_secrets = [
            "FIREBASE_PROJECT_ID",
            "FIREBASE_PRIVATE_KEY",
            "FIREBASE_CLIENT_EMAIL",
            "GOOGLE_API_KEY"
        ]
        
        missing_secrets = []
        
        for secret_name in required_secrets:
            value = self.get_secret(secret_name)
            if not value:
                missing_secrets.append(secret_name)
        
        if missing_secrets:
            logger.error(f"❌ 필수 Secret 누락: {missing_secrets}")
            logger.info("💡 다음 명령으로 Secret을 생성하세요:")
            for secret in missing_secrets:
                logger.info(f"   gcloud secrets create {secret} --data-file=-")
            return False
        
        logger.info("✅ 모든 필수 Secret 확인 완료")
        return True
    
    def export_to_env_file(self, output_file: str = ".env.production") -> bool:
        """
        Secret Manager의 값들을 환경변수 파일로 내보내기 (백업용)
        
        Args:
            output_file: 출력할 환경변수 파일명
        
        Returns:
            내보내기 성공 여부
        """
        if not self.use_secrets:
            logger.info("📝 개발 환경: Secret 내보내기 스킵")
            return True
        
        try:
            firebase_config = self.get_firebase_config()
            api_keys = self.get_api_keys()
            
            env_content = [
                "# Vertex AI Agent Engine 프로덕션 환경변수",
                "# Secret Manager에서 자동 생성됨",
                f"# 생성일시: {os.popen('date').read().strip()}",
                "",
                "# Google Cloud 설정",
                f"GOOGLE_CLOUD_PROJECT={self.project_id}",
                "",
                "# Firebase 설정",
            ]
            
            for key, value in firebase_config.items():
                if value:
                    env_content.append(f"FIREBASE_{key.upper()}={value}")
            
            env_content.extend([
                "",
                "# API 키",
            ])
            
            for key, value in api_keys.items():
                if value:
                    env_content.append(f"{key.upper()}={value}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_content))
            
            logger.info(f"✅ 환경변수 파일 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 환경변수 파일 생성 실패: {e}")
            return False
    
    def validate_secrets(self) -> Dict[str, bool]:
        """
        모든 필수 Secret 유효성 검증
        
        Returns:
            Secret별 유효성 검증 결과
        """
        validation_results = {}
        
        # Firebase 설정 검증
        firebase_config = self.get_firebase_config()
        validation_results["firebase_config"] = len(firebase_config) >= 5
        
        # API 키 검증
        api_keys = self.get_api_keys()
        validation_results["google_api_key"] = bool(api_keys.get("google_api_key"))
        
        # 전체 상태
        all_valid = all(validation_results.values())
        validation_results["all_secrets_valid"] = all_valid
        
        if all_valid:
            logger.info("✅ 모든 Secret 검증 통과")
        else:
            failed_secrets = [k for k, v in validation_results.items() if not v]
            logger.warning(f"⚠️ 검증 실패 Secret: {failed_secrets}")
        
        return validation_results 