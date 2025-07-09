# -*- coding: utf-8 -*-
"""
📊 견적 상담 전문 에이전트 - ADK 표준 LlmAgent 구현

🎯 견적 관련 모든 요청을 전문적으로 처리
- 친절한 고객 상담
- Firebase 자동 저장 기능
- 견적 요청 관리
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional

# 🔧 런타임 인코딩 보정 (한글 깨짐 방지)
if sys.version_info >= (3, 7):
    if not os.environ.get('PYTHONUTF8'):
        os.environ['PYTHONUTF8'] = '1'
        os.environ['PYTHONIOENCODING'] = 'utf-8'

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from ..tools.mcp_client import firebase_client

# ========================================
# 🔧 견적 요청 Firebase 저장 도구
# ========================================

async def save_estimate_request(content: str, contact: str = "", address: str = "", session_id: Optional[str] = None):
    """견적 요청을 Firebase에 저장"""
    try:
        # 현재 날짜시간 기반 문서명 생성
        now = datetime.now()
        doc_name = f"estimate_{now.strftime('%Y%m%d_%H%M%S_%f')[:19]}"  # estimate_20250106_022015_001
        
        # 저장할 데이터 (1행 JSON 문자열 형태)
        estimate_data = {
            "content": content,
            "contact": contact,
            "address": address,
            "createdAt": now.isoformat(),
            "sessionId": session_id or "unknown"
        }
        
        # Firebase에 저장
        result = await firebase_client.call_tool("firestore_add_document", {
            "collection": "estimateRequests",
            "data": {"content": json.dumps(estimate_data, ensure_ascii=False)}
        }, session_id)
        
        print(f"✅ 견적 요청 저장 완료: {doc_name}")
        return f"견적 요청이 저장되었습니다. (접수번호: {doc_name})"
        
    except Exception as e:
        print(f"❌ 견적 요청 저장 실패: {str(e)}")
        return "견적 요청 저장 중 오류가 발생했습니다."

# ========================================
# 🤖 견적 상담 전문 LlmAgent 정의
# ========================================

estimate_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='estimate_agent',
    
    # 견적 저장 도구 추가
    tools=[
        FunctionTool(save_estimate_request),
    ],
    
    # 견적 상담 전문 Instructions (비어둠)
    instruction='''
# 📊 아마레 디자인 견적 상담 에이전트

견적 상담을 도와드리는 전문 에이전트입니다.
''',
    
    description="견적 상담 전문 에이전트"
)

# ========================================
# 📤 모듈 Export
# ========================================

__all__ = [
    'estimate_agent',
    'save_estimate_request'
]

# ========================================
# 🚀 초기화 로그
# ========================================

print("="*50)
print("📊 견적 상담 전문 에이전트 초기화 완료!")
print(f"🤖 에이전트명: {estimate_agent.name}")
print(f"🔧 도구 개수: {len(estimate_agent.tools)}개")
print("="*50) 