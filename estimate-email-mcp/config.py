#!/usr/bin/env python3
"""
⚙️ Estimate Email MCP 서버 설정 파일
"""

import os
from typing import Dict, Any

# 서버 기본 설정 (Remote MCP for Claude Web)
SERVER_CONFIG = {
    "name": "estimate-email-mcp",
    "version": "1.0.0",
    "description": "견적서 이메일 전송 전용 MCP 서버",
    "host": "localhost",
    "port": 8001
}

# Cloud Functions API 설정 (React 앱 우회, 직접 호출)
CLOUD_FUNCTIONS_CONFIG = {
    "send_estimate_email": "https://us-central1-interior-one-click.cloudfunctions.net/sendEstimatePdfHttp"
}

# 이메일 전송 설정
EMAIL_CONFIG = {
    "timeout": 60,  # 초
    "subject_template": "아마레디자인 견적서 - {address}",
    "content_template": """안녕하세요, 아마레디자인입니다.

{address} 프로젝트의 견적서를 보내드립니다.

📋 견적 요약:
- 총 공정 수: {process_count}개
- 기본 공사비: {basic_total:,}원
- 기업이윤 ({corporate_profit_percentage}%): {corporate_profit_amount:,}원
- 총 견적 금액: {total_amount:,}원

자세한 내역은 첨부된 견적서를 확인해주시고, 궁금한 점이 있으시면 언제든지 연락주세요.

감사합니다.

아마레디자인 드림
전화: 010-0000-0000
이메일: design@amare.co.kr""",
    "default_corporate_profit": {
        "percentage": 10,
        "isVisible": True
    }
}

# 통합 설정
CONFIG = {
    "server": SERVER_CONFIG,
    "cloud_functions": CLOUD_FUNCTIONS_CONFIG,
    "email": EMAIL_CONFIG
}

# 설정 검증 함수
def validate_config():
    """설정값 유효성 검사"""
    required_keys = [
        ("server", "name"),
        ("server", "host"), 
        ("server", "port"),
        ("cloud_functions", "send_estimate_email"),
        ("email", "timeout"),
        ("email", "subject_template"),
        ("email", "content_template")
    ]
    
    for section, key in required_keys:
        if section not in CONFIG or key not in CONFIG[section]:
            raise ValueError(f"설정 누락: {section}.{key}")
    
    # Cloud Functions URL 검증
    cloud_url = CONFIG["cloud_functions"]["send_estimate_email"]
    if not cloud_url.startswith("https://"):
        raise ValueError("Cloud Functions URL은 HTTPS여야 합니다")
    
    print("✅ 설정 검증 완료")
    return True

if __name__ == "__main__":
    # 설정 테스트
    print("🔧 Estimate Email MCP 서버 설정")
    print("=" * 50)
    
    # 설정 검증
    try:
        validate_config()
        
        print(f"📊 서버: {CONFIG['server']['name']} v{CONFIG['server']['version']}")
        print(f"📡 주소: http://{CONFIG['server']['host']}:{CONFIG['server']['port']}/sse")
        print(f"☁️  Cloud Functions: {CONFIG['cloud_functions']['send_estimate_email']}")
        print(f"⏱️  타임아웃: {CONFIG['email']['timeout']}초")
        print(f"💰 기본 기업이윤: {CONFIG['email']['default_corporate_profit']['percentage']}%")
        print()
        print("✅ 모든 설정이 올바릅니다!")
        
    except Exception as e:
        print(f"❌ 설정 오류: {e}")
        exit(1) 