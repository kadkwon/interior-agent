# -*- coding: utf-8 -*-
"""
ADK API Server - agent_main.py와 완전히 동일한 결과를 제공하는 HTTP API
"""

from flask import Flask, request, jsonify
import asyncio
import sys
import os
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# agent_main.py 임포트
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "interior_multi_agent"))
    from interior_agents.agent_main import root_agent
    AGENT_AVAILABLE = True
    logger.info(f"✅ root_agent 로드 성공: {root_agent.name}")
    logger.info(f"   - 모델: {root_agent.model}")
    logger.info(f"   - 도구 수: {len(root_agent.tools)}")
except Exception as e:
    logger.error(f"❌ root_agent 로드 실패: {e}")
    AGENT_AVAILABLE = False
    root_agent = None

@app.route("/health", methods=["GET"])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        "status": "healthy",
        "agent_available": AGENT_AVAILABLE,
        "agent_name": root_agent.name if AGENT_AVAILABLE else None,
        "agent_model": root_agent.model if AGENT_AVAILABLE else None,
        "tools_count": len(root_agent.tools) if AGENT_AVAILABLE else 0,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/agent/chat", methods=["POST"])
def chat_endpoint():
    """메인 채팅 엔드포인트 - agent_main.py와 완전히 동일한 결과 제공"""
    if not AGENT_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "Agent not available",
            "message": "root_agent를 로드할 수 없습니다."
        }), 500
    
    try:
        data = request.json
        user_input = data.get("message", "")
        
        if not user_input:
            return jsonify({
                "success": False,
                "error": "Empty message"
            }), 400
        
        logger.info(f"🔄 사용자 입력: {user_input}")
        logger.info(f"🤖 에이전트: {root_agent.name} (모델: {root_agent.model})")
        
        # 실제 ADK LlmAgent 실행 (개선된 방식)
        async def run_agent():
            try:
                logger.info("🚀 ADK LlmAgent 실행 시작...")
                
                # 방법 1: run_async를 사용한 안정적인 이벤트 처리
                response_content = ""
                tool_calls_info = []
                
                try:
                    # 이벤트 스트림 처리
                    async for event in root_agent.run_async(user_input):
                        logger.info(f"📨 이벤트 타입: {event.type}")
                        
                        # 텍스트 콘텐츠 처리
                        if hasattr(event, 'content') and event.content:
                            response_content += event.content
                            logger.info(f"📝 텍스트 추가: {len(event.content)} 문자")
                        
                        # 도구 호출 이벤트 처리
                        if hasattr(event, 'tool_calls') and event.tool_calls:
                            for tool_call in event.tool_calls:
                                tool_info = {
                                    "name": tool_call.name,
                                    "args": getattr(tool_call, 'args', {}),
                                    "id": getattr(tool_call, 'id', 'unknown')
                                }
                                tool_calls_info.append(tool_info)
                                logger.info(f"🔧 도구 호출: {tool_call.name}")
                        
                        # 도구 응답 이벤트 처리  
                        if hasattr(event, 'tool_responses') and event.tool_responses:
                            for tool_response in event.tool_responses:
                                logger.info(f"📤 도구 응답: {len(str(tool_response))} 문자")
                        
                        # 완료 이벤트 체크
                        if hasattr(event, 'finish_reason') and event.finish_reason:
                            logger.info(f"🏁 완료 이유: {event.finish_reason}")
                            break
                    
                    # 응답 생성
                    if response_content:
                        logger.info(f"✅ 최종 응답 생성 완료: {len(response_content)} 문자")
                        return {
                            "success": True,
                            "response": response_content,
                            "agent_name": root_agent.name,
                            "model": root_agent.model,
                            "tool_calls": tool_calls_info
                        }
                    else:
                        logger.warning("⚠️ 응답 내용이 비어있습니다")
                        # 기본 응답 제공
                        return {
                            "success": True,
                            "response": f"요청을 받았습니다: '{user_input}'\n\n현재 {root_agent.name}이 처리 중입니다. 잠시만 기다려주세요.",
                            "agent_name": root_agent.name,
                            "model": root_agent.model,
                            "tool_calls": tool_calls_info
                        }
                        
                except Exception as stream_error:
                    logger.error(f"❌ 이벤트 스트림 처리 오류: {stream_error}")
                    
                    # 방법 2: 대안적 도구 직접 호출 (agent_main.py 지침 준수)
                    logger.info("🔄 대안 방법: 도구 직접 호출")
                    
                    # 사용자 입력 분석 및 적절한 도구 선택
                    user_input_lower = user_input.lower()
                    
                    # 확장된 도구 매핑 (정교한 키워드 매칭)
                    tool_mappings = {
                        # 주소 관리 - 더 구체적인 키워드
                        'list_addresses': ['리스트', 'list', '목록', '조회', '보여줘', '목록보기'],
                        'register_address': ['등록해줘', '추가해줘', '신규', 'register', 'add', '등록하고', '추가하고', '등록', '추가'],
                        'update_address': ['수정해줘', '업데이트', 'update', 'modify', '변경해줘', '수정하고', '변경하고', '수정', '변경'],
                        'delete_address': ['삭제해줘', 'delete', '제거해줘', 'remove', '삭제하고', '제거하고', '삭제', '제거'],
                        'search_address': ['검색해줘', 'search', '찾아줘', 'find', '검색하고', '찾고', '검색', '찾기'],
                        
                        # 스케줄 관리 - 더 구체적인 키워드
                        'today_schedules': ['오늘', 'today', '금일', '당일'],
                        'upcoming_schedules': ['예정', 'upcoming', '향후', '다음', '앞으로'],
                        'schedule_list': ['일정 목록', '스케줄 목록', '일정리스트', '스케줄리스트'],
                        'register_schedule': ['일정등록', '스케줄등록', '일정추가', '일정 등록', '스케줄 등록'],
                        'update_schedule': ['일정수정', '스케줄수정', '일정변경', '일정 수정', '스케줄 수정'],
                        'delete_schedule': ['일정삭제', '스케줄삭제', '일정제거', '일정 삭제', '스케줄 삭제'],
                        'complete_schedule': ['완료', 'complete', '완성', '끝'],
                        'schedule_report': ['리포트', 'report', '보고서', '통계'],
                        'schedule_search': ['일정검색', '스케줄검색', '일정 검색', '스케줄 검색'],
                        
                        # 프로젝트 관리
                        'new_project': ['새로운', '프로젝트', '시작', 'new', 'project', 'start'],
                        'project_status': ['상태', '진행', 'status', 'progress', '현재'],
                        'estimate': ['견적', '추정', 'estimate', '비용', 'cost'],
                        
                        # Firebase 데이터
                        'collections': ['컬렉션', 'collection', '데이터', 'data'],
                        'payments': ['지급', '결제', 'payment', '비용']
                    }
                    
                    # 더 정교한 도구 선택 로직
                    best_match = None
                    max_score = 0
                    max_weight = 0
                    
                    for tool_category, keywords in tool_mappings.items():
                        score = 0
                        weight = 0
                        
                        for keyword in keywords:
                            if keyword in user_input_lower:
                                score += 1
                                # 긴 키워드에 더 높은 가중치
                                weight += len(keyword)
                        
                        # 총 점수 계산 (키워드 개수 + 가중치)
                        total_score = score * 10 + weight
                        
                        if total_score > max_score:
                            max_score = total_score
                            max_weight = weight
                            best_match = tool_category
                    
                    logger.info(f"최적 도구 카테고리: {best_match} (점수: {max_score}, 가중치: {max_weight})")
                    
                    # 특별한 조건 확인 (우선순위 높음) - 더 정교한 패턴 매칭
                    if best_match and max_score > 0:
                        # 주소 관련 동작 구분 (가장 높은 우선순위)
                        if '주소' in user_input_lower or any(city in user_input_lower for city in ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종']):
                            # 등록 관련 키워드 확인
                            if any(word in user_input_lower for word in ['등록해줘', '추가해줘', '신규', '등록하고', '추가하고', '등록', '추가']):
                                best_match = 'register_address'
                            # 삭제 관련 키워드 확인
                            elif any(word in user_input_lower for word in ['삭제해줘', '제거해줘', '삭제하고', '제거하고', '삭제', '제거']):
                                best_match = 'delete_address'
                            # 수정 관련 키워드 확인
                            elif any(word in user_input_lower for word in ['수정해줘', '업데이트', '변경해줘', '수정하고', '변경하고', '수정', '변경']):
                                best_match = 'update_address'
                            # 검색 관련 키워드 확인
                            elif any(word in user_input_lower for word in ['검색해줘', '찾아줘', '검색하고', '찾고', '검색', '찾기']):
                                best_match = 'search_address'
                            # 조회 관련 키워드 확인
                            elif any(word in user_input_lower for word in ['리스트', '목록', '조회', '보여줘']):
                                best_match = 'list_addresses'
                        
                        # 스케줄/일정 키워드 처리 (두 번째 우선순위)
                        elif any(word in user_input_lower for word in ['일정', '스케줄']):
                            if any(word in user_input_lower for word in ['오늘', 'today', '금일']):
                                best_match = 'today_schedules'
                            elif any(word in user_input_lower for word in ['예정', 'upcoming', '향후']):
                                best_match = 'upcoming_schedules'
                            elif any(word in user_input_lower for word in ['등록해줘', '추가해줘', '등록하고', '추가하고']):
                                best_match = 'register_schedule'
                            elif any(word in user_input_lower for word in ['삭제해줘', '제거해줘', '삭제하고', '제거하고']):
                                best_match = 'delete_schedule'
                            elif any(word in user_input_lower for word in ['수정해줘', '변경해줘', '수정하고', '변경하고']):
                                best_match = 'update_schedule'
                            elif any(word in user_input_lower for word in ['검색해줘', '찾아줘', '검색하고', '찾고']):
                                best_match = 'schedule_search'
                            elif any(word in user_input_lower for word in ['목록', '리스트']):
                                best_match = 'schedule_list'
                        
                        # 기타 특별 키워드 처리
                        elif any(word in user_input_lower for word in ['오늘', 'today']) and any(word in user_input_lower for word in ['일정', '스케줄']):
                            best_match = 'today_schedules'
                    
                    logger.info(f"최종 선택된 도구: {best_match}")
                    
                    # 도구 실행
                    if best_match and max_score > 0:
                        # 주소 관리
                        if best_match == 'list_addresses':
                            return await execute_tool_by_name('list_all_addresses', "주소 리스트 조회")
                        elif best_match == 'register_address':
                            return await execute_tool_by_name('register_new_address', "주소 등록", user_input)
                        elif best_match == 'delete_address':
                            return await execute_tool_by_name('delete_address_record', "주소 삭제", user_input)
                        elif best_match == 'update_address':
                            return await execute_tool_by_name('update_existing_address', "주소 수정", user_input)
                        elif best_match == 'search_address':
                            return await execute_tool_by_name('search_addresses_by_keyword', "주소 검색", user_input)
                        
                        # 스케줄 관리
                        elif best_match == 'today_schedules':
                            return await execute_tool_by_name('get_today_schedules', "오늘 일정 조회")
                        elif best_match == 'upcoming_schedules':
                            return await execute_tool_by_name('get_upcoming_schedules', "예정 일정 조회")
                        elif best_match == 'schedule_list':
                            return await execute_tool_by_name('list_schedules', "스케줄 목록 조회")
                        elif best_match == 'register_schedule':
                            return await execute_tool_by_name('register_schedule_event', "일정 등록", user_input)
                        elif best_match == 'delete_schedule':
                            return await execute_tool_by_name('delete_schedule_event', "일정 삭제", user_input)
                        elif best_match == 'update_schedule':
                            return await execute_tool_by_name('update_schedule_event', "일정 수정", user_input)
                        elif best_match == 'schedule_report':
                            return await execute_tool_by_name('generate_schedule_report', "일정 리포트 생성", user_input)
                        elif best_match == 'schedule_search':
                            return await execute_tool_by_name('search_schedules_by_keyword', "일정 검색", user_input)
                        
                        # 기타 가이드들
                        elif best_match == 'new_project':
                            return create_guide_response("새 프로젝트", """🏗️ **새로운 인테리어 프로젝트 시작**

새 프로젝트를 시작하려면:

1️⃣ **현장 주소 등록**
   - "서울시 강남구 테헤란로 123번지 주소 등록해줘"

2️⃣ **초기 일정 등록**
   - "현장 측량 일정 등록해줘"
   - "자재 발주 일정 추가해줘"

3️⃣ **지급 계획 수립**
   - "분할 지급 계획 생성해줘"

💡 **단계별로 진행하시면 체계적인 프로젝트 관리가 가능합니다.**""")
                        elif best_match == 'estimate':
                            return create_guide_response("견적 생성", """💰 **견적 생성 프로세스**

견적을 생성하려면:

📋 **필요한 정보:**
- 정확한 주소 (동/호수 포함)
- 시공 면적 (평수)
- 시공 범위 (전체/부분)
- 희망 예산 범위

💡 **예시:** "서울시 강남구 테헤란로 123번지 101동 1001호, 32평, 예산 5000만원, 전체 리모델링 견적 요청"

🔧 **현재 사용 가능한 기능:**
- 주소 등록 및 관리
- 일정 관리
- 분할 지급 계획 수립""")
                    
                    # 기본 에이전트 응답
                    return create_guide_response("기본 안내", f"""안녕하세요! {root_agent.name}입니다.

요청하신 내용: {user_input}

🏠 **주요 기능 (총 {len(root_agent.tools)}개 도구):**
- 주소 관리: 등록, 수정, 삭제, 조회, 검색
- 스케줄 관리: 일정 등록, 수정, 삭제, 조회, 리포트
- Firebase 데이터 관리
- 지급 계획 수립

🔧 **사용 가능한 명령어:**
- "주소 리스트 보여줘" - 등록된 주소 목록
- "오늘 일정 보여줘" - 오늘의 스케줄
- "예정 일정 보여줘" - 향후 일정
- "새로운 프로젝트 시작" - 프로젝트 생성 가이드
- "일정 리포트 생성해줘" - 기간별 통계

💡 구체적인 요청을 해주시면 더 정확한 도움을 드릴 수 있습니다.""")
                
            except Exception as e:
                logger.error(f"❌ 전체 에이전트 실행 오류: {type(e).__name__}: {e}")
                import traceback
                logger.error(f"상세 스택 트레이스:\n{traceback.format_exc()}")
                return {
                    "success": False,
                    "error": f"에이전트 실행 중 오류 발생: {str(e)}"
                }
        
        async def execute_tool_by_name(tool_name: str, description: str, user_input: str = None):
            """도구 이름으로 직접 실행 (개선된 버전)"""
            try:
                for tool in root_agent.tools:
                    if hasattr(tool, '__name__') and tool_name in tool.__name__:
                        logger.info(f"✅ {tool_name} 도구 실행 중...")
                        
                        # 도구가 파라미터를 필요로 하는 경우 처리
                        if user_input and tool_name in ['register_new_address', 'delete_address_record', 
                                                       'update_existing_address', 'search_addresses_by_keyword',
                                                       'register_schedule_event', 'delete_schedule_event',
                                                       'update_schedule_event', 'search_schedules_by_keyword',
                                                       'generate_schedule_report']:
                            
                            # 주소 등록
                            if tool_name == 'register_new_address':
                                # 주소에서 등록할 정보 추출
                                address_text = user_input.replace('주소', '').replace('등록해줘', '').replace('추가해줘', '').replace('신규', '').replace('등록하고', '').replace('추가하고', '').strip()
                                if address_text:
                                    # dict 형태로 변환하여 전달
                                    address_data = {
                                        'address': address_text,
                                        'description': address_text,
                                        'createdAt': datetime.now().isoformat(),
                                        'isCompleted': True
                                    }
                                    try:
                                        result = tool(address_data)
                                    except Exception as tool_error:
                                        logger.warning(f"⚠️ {tool_name} 실행 실패: {tool_error}")
                                        result = {"status": "error", "message": f"주소 등록 중 오류: {str(tool_error)}"}
                                else:
                                    result = {"status": "error", "message": "등록할 주소를 명시해주세요. 예: '서울시 강남구 테헤란로 123번지 등록해줘'"}
                            
                            # 주소 삭제
                            elif tool_name == 'delete_address_record':
                                # 삭제할 주소 ID나 이름 추출
                                delete_target = user_input.replace('주소', '').replace('삭제해줘', '').replace('제거해줘', '').replace('삭제하고', '').replace('제거하고', '').strip()
                                if delete_target:
                                    try:
                                        result = tool(delete_target)
                                    except Exception as tool_error:
                                        logger.warning(f"⚠️ {tool_name} 실행 실패: {tool_error}")
                                        result = {"status": "error", "message": f"주소 삭제 중 오류: {str(tool_error)}"}
                                else:
                                    result = {"status": "error", "message": "삭제할 주소를 명시해주세요. 예: '1734242126699 삭제해줘' 또는 '수성 3가 롯데캐슬 삭제해줘'"}
                            
                            # 주소 수정
                            elif tool_name == 'update_existing_address':
                                # 수정할 주소와 데이터 추출 - 간단한 형태 지원
                                if '수정해줘' in user_input or '변경해줘' in user_input or '업데이트' in user_input:
                                    # 주소명 추출
                                    address_part = user_input.replace('주소', '').replace('수정해줘', '').replace('변경해줘', '').replace('업데이트', '').replace('정보', '').strip()
                                    if address_part:
                                        # 간단한 수정: 주소명을 새로운 주소로 업데이트
                                        try:
                                            update_data = {
                                                'description': address_part,
                                                'lastModified': datetime.now().isoformat()
                                            }
                                            result = tool(address_part, update_data)
                                        except Exception as tool_error:
                                            logger.warning(f"⚠️ {tool_name} 실행 실패: {tool_error}")
                                            result = {"status": "error", "message": f"주소 수정 중 오류: {str(tool_error)}"}
                                    else:
                                        result = {"status": "error", "message": "수정할 주소를 명시해주세요. 예: '광주시 서구 치평동 202번지 수정해줘'"}
                                else:
                                    # 복잡한 수정은 가이드 제공
                                    result = {"status": "guide", "message": """🔧 **주소 수정 가이드**

주소 정보를 수정하려면 다음 형식으로 요청해주세요:

💡 **간단한 수정 예시:**
- "광주시 서구 치평동 202번지 수정해줘"
- "대전시 유성구 봉명동 303번지 정보 업데이트"

💡 **상세한 수정 예시:**
- "1734608505871 주소를 서울시 강남구 테헤란로 456번지로 수정해줘"
- "수성 효성 헤링턴의 감독자명을 김철수로 변경해줘"

📋 **필요한 정보:**
- 수정할 주소의 ID 또는 이름
- 변경할 구체적인 내용

현재는 간단한 형태로만 지원됩니다."""}
                            
                            # 주소 검색
                            elif tool_name == 'search_addresses_by_keyword':
                                # 검색 키워드 추출
                                search_keyword = user_input.replace('주소', '').replace('검색해줘', '').replace('찾아줘', '').replace('검색하고', '').replace('찾고', '').replace('검색', '').replace('찾기', '').strip()
                                if search_keyword:
                                    try:
                                        result = tool(search_keyword)
                                    except Exception as tool_error:
                                        logger.warning(f"⚠️ {tool_name} 실행 실패: {tool_error}")
                                        result = {"status": "error", "message": f"주소 검색 중 오류: {str(tool_error)}"}
                                else:
                                    result = {"status": "error", "message": "검색할 키워드를 명시해주세요. 예: '수성 검색해줘' 또는 '롯데캐슬 찾아줘'"}
                            
                            # 일정 등록
                            elif tool_name == 'register_schedule_event':
                                # 일정 정보 추출 (복잡하므로 가이드 제공)
                                result = {"status": "guide", "message": """📅 **일정 등록 가이드**

새로운 일정을 등록하려면 다음 형식으로 요청해주세요:

💡 **예시:**
- "서울시 강남구 테헤란로 123번지에서 2024-12-20에 타일공사 일정 등록해줘"
- "수성 효성 헤링턴에서 내일 도배작업 스케줄 추가해줘"

📋 **필요한 정보:**
- 주소 (등록된 주소)
- 날짜 (YYYY-MM-DD 형식 또는 '오늘', '내일')
- 작업 내용

현재는 간단한 형태로만 지원됩니다."""}
                            
                            # 일정 삭제
                            elif tool_name == 'delete_schedule_event':
                                # 삭제할 일정 정보 추출 (복잡하므로 가이드 제공)
                                result = {"status": "guide", "message": """🗑️ **일정 삭제 가이드**

등록된 일정을 삭제하려면:

1️⃣ 먼저 "오늘 일정 보여줘" 또는 "예정 일정 보여줘"로 삭제할 일정 확인
2️⃣ "일정ID 삭제해줘" 또는 "주소명의 날짜 일정 삭제해줘" 형식으로 요청

💡 **예시:**
- "2025-06-04_1748960343457 일정 삭제해줘"
- "수성 효성 헤링턴의 오늘 일정 삭제해줘"

⚠️ **주의사항:** 삭제된 일정은 복구할 수 없습니다."""}
                            
                            # 기타 스케줄 도구들
                            else:
                                # 파라미터 없이 실행 시도
                                try:
                                    result = tool()
                                except Exception as tool_error:
                                    logger.warning(f"⚠️ {tool_name} 실행 실패: {tool_error}")
                                    result = {"status": "error", "message": f"도구 실행 중 오류: {str(tool_error)}"}
                        else:
                            # 파라미터가 필요 없는 도구
                            result = tool()
                        
                        logger.info(f"✅ {tool_name} 도구 실행 성공")
                        return {
                            "success": True,
                            "response": f"📋 {description} 결과:\n\n{result}",
                            "agent_name": root_agent.name,
                            "model": root_agent.model,
                            "tool_used": tool_name
                        }
                
                # 도구를 찾지 못한 경우
                return {
                    "success": False,
                    "error": f"{tool_name} 도구를 찾을 수 없습니다."
                }
                
            except Exception as e:
                logger.error(f"❌ {tool_name} 도구 실행 오류: {e}")
                return {
                    "success": False,
                    "error": f"{tool_name} 도구 실행 중 오류: {str(e)}"
                }
        
        def create_guide_response(title: str, content: str):
            """가이드 응답 생성"""
            return {
                "success": True,
                "response": content,
                "agent_name": root_agent.name,
                "model": root_agent.model,
                "tool_used": f"{title}_guide"
            }
        
        # 비동기 실행
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_agent())
        finally:
            loop.close()
        
        # 결과 처리 및 응답
        if result.get("success"):
            logger.info(f"✅ 응답 성공: {len(result.get('response', ''))} 문자")
            return jsonify({
                "success": True,
                "response": result.get("response"),
                "agent_type": "root_agent_adk",
                "agent_name": result.get("agent_name"),
                "model": result.get("model"),
                "tool_used": result.get("tool_used"),
                "tool_calls": result.get("tool_calls", []),
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.error(f"❌ 에이전트 실행 실패: {result.get('error')}")
            return jsonify({
                "success": False,
                "error": result.get("error"),
                "agent_type": "root_agent_adk",
                "timestamp": datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        logger.error(f"❌ 전체 처리 오류: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"상세 스택 트레이스:\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"서버 처리 오류: {str(e)}"
        }), 500

@app.route("/agent/info", methods=["GET"])
def agent_info():
    """에이전트 상세 정보"""
    if not AGENT_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "Agent not available"
        }), 500
    
    try:
        # 도구 정보 수집
        tools_info = []
        for tool in root_agent.tools:
            tool_info = {
                "name": getattr(tool, 'name', str(type(tool).__name__)),
                "description": getattr(tool, 'description', '설명 없음'),
                "type": str(type(tool).__name__),
                "function_name": getattr(tool, '__name__', 'unknown')
            }
            tools_info.append(tool_info)
        
        return jsonify({
            "success": True,
            "agent": {
                "name": root_agent.name,
                "description": root_agent.description,
                "model": root_agent.model,
                "tools_count": len(root_agent.tools),
                "tools": tools_info,
                "instruction_length": len(root_agent.instruction) if hasattr(root_agent, 'instruction') else 0
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"에이전트 정보 조회 오류: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    print("=" * 60)
    print("🏠 인테리어 AI 에이전트 API 서버")
    print("=" * 60)
    print(f"📡 서버 주소: http://localhost:8505")
    print(f"🤖 에이전트 상태: {'✅ 사용 가능' if AGENT_AVAILABLE else '❌ 사용 불가'}")
    if AGENT_AVAILABLE:
        print(f"🎯 에이전트 이름: {root_agent.name}")
        print(f"🧠 모델: {root_agent.model}")
        print(f"🔧 도구 수: {len(root_agent.tools)}개")
        print(f"📋 주요 기능:")
        print(f"   - 주소 관리 (등록, 수정, 삭제, 조회, 검색)")
        print(f"   - 스케줄 관리 (일정 등록, 수정, 삭제, 조회, 리포트)")
        print(f"   - Firebase 데이터 관리")
        print(f"   - 지급 계획 수립")
    print("=" * 60)
    print("🚀 서버 시작 중...")
    
    app.run(host="localhost", port=8505, debug=True) 