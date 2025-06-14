#!/usr/bin/env python3
"""
🚀 Vertex AI Agent Engine 배포 스크립트
문서 요구사항에 따른 5단계 배포 프로세스 구현

사용법:
    python deploy.py --environment development
    python deploy.py --environment production --region asia-northeast1
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# 현재 디렉터리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

try:
    import vertexai
    from vertexai import agent_engines
    from dotenv import load_dotenv
    
    # 프로젝트 모듈 import
    from interior_agents import root_agent
    from interior_agents.config import DeploymentConfig, CloudSecretsManager
    
except ImportError as e:
    print(f"❌ 필수 패키지 누락: {e}")
    print("💡 다음 명령으로 설치하세요:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class AgentDeployer:
    """
    Vertex AI Agent Engine 배포 담당 클래스
    문서의 5단계 배포 프로세스 구현
    """
    
    def __init__(self, environment: str = "development", region: str = None):
        """
        배포자 초기화
        
        Args:
            environment: 배포 환경 (development/staging/production)
            region: 배포 지역 (선택사항)
        """
        self.environment = environment
        self.region = region
        self.deployment_config = None
        self.secrets_manager = None
        self.remote_agent = None
        
        logger.info(f"🎯 Agent Engine 배포 시작: {environment} 환경")
    
    def step_0_load_environment(self):
        """
        0단계: 환경설정 로드 및 검증
        """
        logger.info("📋 0단계: 환경설정 로드 중...")
        
        # .env 파일 로드
        env_files = ['.env', 'deployment.env.template']
        for env_file in env_files:
            if os.path.exists(env_file):
                load_dotenv(env_file)
                logger.info(f"✅ 환경설정 로드: {env_file}")
                break
        else:
            logger.warning("⚠️ .env 파일을 찾을 수 없습니다")
        
        # 배포 설정 초기화
        self.deployment_config = DeploymentConfig(self.environment)
        if self.region:
            self.deployment_config.location = self.region
        
        # Secret Manager 초기화
        self.secrets_manager = CloudSecretsManager(self.deployment_config.project_id)
        
        # 환경 검증
        if not self.deployment_config.validate_environment():
            logger.error("❌ 환경 검증 실패")
            return False
        
        logger.info("✅ 0단계 완료: 환경설정 로드")
        return True
    
    def step_1_setup_vertex_ai(self):
        """
        1단계: Vertex AI 초기화 (문서 요구사항)
        """
        logger.info("📋 1단계: Vertex AI 초기화 중...")
        
        try:
            # Vertex AI 초기화
            init_config = self.deployment_config.get_vertex_ai_init_config()
            vertexai.init(**init_config)
            
            logger.info(f"✅ Vertex AI 초기화 완료:")
            logger.info(f"   - 프로젝트: {init_config['project']}")
            logger.info(f"   - 지역: {init_config['location']}")
            logger.info(f"   - 스테이징 버킷: {init_config['staging_bucket']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Vertex AI 초기화 실패: {e}")
            return False
    
    def step_2_validate_agent(self):
        """
        2단계: 에이전트 검증 (문서 요구사항)
        """
        logger.info("📋 2단계: 에이전트 검증 중...")
        
        try:
            # 에이전트 로드 확인
            if not root_agent:
                logger.error("❌ root_agent를 로드할 수 없습니다")
                return False
            
            # 에이전트 속성 확인
            required_attrs = ['name', 'description', 'tools']
            for attr in required_attrs:
                if not hasattr(root_agent, attr):
                    logger.warning(f"⚠️ 에이전트에 {attr} 속성이 없습니다")
            
            logger.info(f"✅ 에이전트 검증 완료:")
            logger.info(f"   - 이름: {getattr(root_agent, 'name', 'N/A')}")
            logger.info(f"   - 설명: {getattr(root_agent, 'description', 'N/A')[:50]}...")
            logger.info(f"   - 도구 개수: {len(getattr(root_agent, 'tools', []))}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 에이전트 검증 실패: {e}")
            return False
    
    def step_3_check_cloud_storage(self):
        """
        3단계: Cloud Storage 버킷 확인/생성 (문서 요구사항)
        """
        logger.info("📋 3단계: Cloud Storage 버킷 확인 중...")
        
        try:
            from google.cloud import storage
            
            # Application Default Credentials 사용 (서비스 계정 키 파일 무시)
            import os
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
            
            client = storage.Client(project=self.deployment_config.project_id)
            bucket_name = self.deployment_config.staging_bucket.replace('gs://', '')
            
            try:
                bucket = client.bucket(bucket_name)
                if not bucket.exists():
                    # 버킷 생성
                    bucket = client.create_bucket(
                        bucket_name, 
                        location=self.deployment_config.location
                    )
                    logger.info(f"✅ 스테이징 버킷 생성: {bucket_name}")
                else:
                    logger.info(f"✅ 스테이징 버킷 확인: {bucket_name}")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ 버킷 처리 실패: {e}")
                return False
                
        except ImportError:
            logger.warning("⚠️ google-cloud-storage 패키지 필요")
            return True  # 선택사항이므로 계속 진행
        except Exception as e:
            logger.error(f"❌ Cloud Storage 확인 실패: {e}")
            return False
    
    def step_4_validate_secrets(self):
        """
        4단계: Secret 및 보안 설정 검증
        """
        logger.info("📋 4단계: 보안 설정 검증 중...")
        
        try:
            # Secret 검증
            validation_results = self.secrets_manager.validate_secrets()
            
            if validation_results.get("all_secrets_valid", False):
                logger.info("✅ 모든 보안 설정 검증 통과")
                return True
            else:
                logger.warning("⚠️ 일부 보안 설정 누락 - 계속 진행")
                return True  # 개발 환경에서는 계속 진행
                
        except Exception as e:
            logger.error(f"❌ 보안 설정 검증 실패: {e}")
            return self.environment != "production"  # 프로덕션에서는 중단
    
    def step_5_deploy_agent(self):
        """
        5단계: AgentEngine 인스턴스 생성 (문서 핵심 요구사항)
        """
        logger.info("📋 5단계: Agent Engine 배포 실행 중...")
        
        try:
            # 배포 설정 가져오기
            agent_config = self.deployment_config.get_agent_engine_config()
            
            logger.info("🚀 배포 시작...")
            logger.info(f"   - 요구사항 패키지: {len(agent_config['requirements'])}개")
            logger.info(f"   - 추가 패키지: {agent_config['extra_packages']}")
            logger.info(f"   - GCS 디렉터리: {agent_config['gcs_dir_name']}")
            logger.info(f"   - 표시 이름: {agent_config['display_name']}")
            
            # 문서 요구사항에 따른 agent_engines.create() 호출
            self.remote_agent = agent_engines.create(
                root_agent,  # local_agent (필수)
                requirements=agent_config['requirements'],  # 1단계
                extra_packages=agent_config['extra_packages'],  # 2단계
                gcs_dir_name=agent_config['gcs_dir_name'],  # 3단계
                display_name=agent_config['display_name'],  # 4단계
                description=agent_config['description']
                # labels 매개변수는 현재 버전에서 지원되지 않음
            )
            
            logger.info("⏳ 배포 진행 중... (몇 분 소요될 수 있습니다)")
            
            # 배포 완료 대기 (필요시)
            if hasattr(self.remote_agent, 'resource_name'):
                resource_name = self.remote_agent.resource_name
                logger.info(f"✅ 배포 완료!")
                logger.info(f"🔗 리소스 ID: {resource_name}")
                
                # 배포 요약 출력
                self._print_deployment_summary(resource_name)
                return True
            else:
                logger.warning("⚠️ 리소스 이름을 가져올 수 없습니다")
                return False
                
        except Exception as e:
            logger.error(f"❌ Agent Engine 배포 실패: {e}")
            logger.error("💡 가능한 해결책:")
            logger.error("   1. 패키지 버전 확인")
            logger.error("   2. Google Cloud 권한 확인")
            logger.error("   3. 네트워크 연결 확인")
            return False
    
    def _print_deployment_summary(self, resource_name: str):
        """
        배포 완료 요약 정보 출력
        """
        summary = self.deployment_config.get_deployment_summary()
        
        print("\n" + "="*60)
        print("🎉 Vertex AI Agent Engine 배포 완료!")
        print("="*60)
        print(f"📍 리소스 ID: {resource_name}")
        print(f"🌍 배포 환경: {summary['environment']}")
        print(f"📦 프로젝트: {summary['project_id']}")
        print(f"🌐 지역: {summary['location']}")
        print(f"🗄️ 스테이징 버킷: {summary['staging_bucket']}")
        print(f"📂 GCS 디렉터리: {summary['gcs_directory']}")
        print(f"📅 배포 시간: {summary['timestamp']}")
        print(f"📋 패키지 개수: {summary['requirements_count']}")
        print("="*60)
        print("\n💡 다음 단계:")
        print("   1. 배포된 에이전트 테스트")
        print("   2. API 엔드포인트 활용")
        print("   3. 모니터링 설정")
        print("\n📚 관련 문서:")
        print("   - 에이전트 사용: https://cloud.google.com/vertex-ai/docs/agent-engine/use")
        print("   - 배포 관리: https://cloud.google.com/vertex-ai/docs/agent-engine/manage")
        print()
    
    def deploy(self):
        """
        전체 배포 프로세스 실행
        """
        logger.info("🎯 Vertex AI Agent Engine 배포 프로세스 시작")
        logger.info(f"   환경: {self.environment}")
        logger.info(f"   지역: {self.region or '자동 선택'}")
        
        steps = [
            ("환경설정 로드", self.step_0_load_environment),
            ("Vertex AI 초기화", self.step_1_setup_vertex_ai),
            ("에이전트 검증", self.step_2_validate_agent),
            ("Cloud Storage 확인", self.step_3_check_cloud_storage),
            ("보안 설정 검증", self.step_4_validate_secrets),
            ("Agent Engine 배포", self.step_5_deploy_agent),
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"📋 {i}단계: {step_name}")
            logger.info('='*50)
            
            if not step_func():
                logger.error(f"❌ {i}단계 실패: {step_name}")
                return False
            
            logger.info(f"✅ {i}단계 완료: {step_name}")
        
        logger.info("\n🎉 전체 배포 프로세스 완료!")
        return True

def main():
    """
    메인 실행 함수
    """
    parser = argparse.ArgumentParser(
        description="Vertex AI Agent Engine 배포 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
    # 개발 환경 배포
    python deploy.py --environment development
    
    # 프로덕션 환경 배포 (아시아 지역)
    python deploy.py --environment production --region asia-northeast1
    
    # 스테이징 환경 배포 (유럽 지역)
    python deploy.py --environment staging --region europe-west1
        """
    )
    
    parser.add_argument(
        '--environment', '-e',
        choices=['development', 'staging', 'production'],
        default='development',
        help='배포 환경 선택 (기본값: development)'
    )
    
    parser.add_argument(
        '--region', '-r',
        help='배포 지역 (예: us-central1, asia-northeast1)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 배포 없이 검증만 수행'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='자세한 로그 출력'
    )
    
    args = parser.parse_args()
    
    # 로그 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 배포 실행
    deployer = AgentDeployer(args.environment, args.region)
    
    if args.dry_run:
        logger.info("🔍 Dry-run 모드: 검증만 수행합니다")
        # 배포 전 단계까지만 실행
        success = (
            deployer.step_0_load_environment() and
            deployer.step_1_setup_vertex_ai() and
            deployer.step_2_validate_agent() and
            deployer.step_3_check_cloud_storage() and
            deployer.step_4_validate_secrets()
        )
        
        if success:
            logger.info("✅ 모든 검증 통과 - 실제 배포 준비됨")
            return 0
        else:
            logger.error("❌ 검증 실패 - 설정 확인 필요")
            return 1
    else:
        success = deployer.deploy()
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 