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
    "content_template": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px; 
            text-align: center;
        }
        .header h2 {
            margin: 0 0 10px 0;
            font-size: 24px;
            font-weight: 600;
        }
        .header p {
            margin: 5px 0;
            opacity: 0.9;
        }
        .content { 
            padding: 30px;
        }
        .process-section { 
            background-color: #ffffff; 
            margin: 20px 0;
        }
        .process-title { 
            font-size: 18px;
            font-weight: bold; 
            color: #495057; 
            margin-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }
        .summary { 
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px; 
            border-radius: 8px; 
            margin: 25px 0;
        }
        .summary h3 {
            margin: 0 0 15px 0;
            font-size: 20px;
        }
        .summary ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .summary li {
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        .summary li:last-child {
            border-bottom: none;
        }
        .footer { 
            background-color: #f8f9fa;
            padding: 20px 30px; 
            text-align: center;
            border-top: 1px solid #dee2e6;
        }
        .contact { 
            background-color: #ffffff; 
            padding: 20px; 
            border-radius: 8px;
            border: 1px solid #e9ecef;
            margin-top: 15px;
        }
        .contact p {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🏠 아마레디자인 견적서</h2>
            <p>안녕하세요! 견적요청 주셔서 대단히 감사합니다.</p>
            <p><strong>{address}</strong> 프로젝트 견적서를 보내드립니다.</p>
        </div>

        <div class="content">
            <div class="process-section">
                <div class="process-title">📋 견적 상세</div>
                {process_details}
            </div>

            <div class="summary">
                <h3>💰 견적 요약</h3>
                <ul>
                    <li><strong>총 공정 수:</strong> {process_count}개</li>
                    <li><strong>기본 공사비:</strong> {basic_total:,}원</li>
                    <li><strong>기업이윤 ({corporate_profit_percentage}%):</strong> {corporate_profit_amount:,}원</li>
                    <li><strong>총 견적 금액:</strong> {total_amount:,}원</li>
                </ul>
            </div>
        </div>

        <div class="footer">
            <p>궁금한 점이 있으시면 언제든지 연락주세요!</p>
            
            <div class="contact">
                <p><strong>🏢 아마레디자인</strong></p>
                <p>📞 전화: 010-8694-4078</p>
                <p>📧 이메일: amaredesign@amaredesign.kr</p>
            </div>
        </div>
    </div>
</body>
</html>
""",
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