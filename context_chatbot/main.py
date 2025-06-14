import streamlit as st
import datetime
from chat_manager import ChatManager

# 페이지 설정
st.set_page_config(
    page_title="인테리어 프로젝트 AI 어시스턴트",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "message_count" not in st.session_state:
    st.session_state.message_count = 0

# 사이드바 - 에이전트 상태 정보
with st.sidebar:
    st.title("🤖 시스템 상태")
    
    # 에이전트 상태 가져오기
    agent_status = st.session_state.chat_manager.get_agent_status()
    
    # 현재 사용 중인 에이전트
    st.subheader("현재 에이전트")
    agent_type = agent_status.get("agent_type", "NONE")
    
    if agent_type == "ADK_API":
        st.success("🚀 ADK API 에이전트")
        st.info("실제 agent_main.py와 HTTP API로 연동")
    elif agent_type == "REAL_AGENT":
        st.success("🔧 실제 에이전트")
        st.info("개별 도구를 직접 사용")
    elif agent_type == "FALLBACK":
        st.warning("🛡️ Fallback 에이전트")
        st.info("기본 응답 시스템")
    else:
        st.error("❌ 에이전트 없음")
    
    # ADK API 서버 연결 상태
    st.subheader("🔗 ADK API 서버 연결")
    adk_status = agent_status.get("adk_api_status", "unknown")
    
    if adk_status == "healthy":
        st.success("✅ 완전 연결됨 (정상 작동)")
        st.info("🟢 서버 및 에이전트 모두 정상")
    elif adk_status == "partial":
        st.warning("⚠️ 부분 연결됨 (에이전트 문제)")
        st.info("🟡 서버는 연결되지만 에이전트 오류")
        error_msg = agent_status.get("adk_api_error", "에이전트 사용 불가")
        st.error(f"문제: {error_msg}")
    elif agent_status.get("adk_api_connected"):
        st.warning("⚠️ 연결됨 (상태 불명)")
        st.info("🟡 서버 연결은 되지만 상태 확인 필요")
    else:
        st.error("❌ 연결 실패")
        error_msg = agent_status.get("adk_api_error", "알 수 없는 오류")
        st.warning(f"오류: {error_msg}")
    
    # 에이전트 가용성 상태
    st.subheader("에이전트 가용성")
    if agent_status.get("adk_api_available"):
        st.success("✅ ADK API 모듈 로드됨")
    else:
        st.error("❌ ADK API 모듈 로드 실패")
        
    if agent_status.get("real_agent_available"):
        st.success("✅ 실제 에이전트 사용 가능")
    else:
        st.error("❌ 실제 에이전트 사용 불가")
        
    if agent_status.get("fallback_available"):
        st.success("✅ Fallback 사용 가능")
    else:
        st.error("❌ Fallback 사용 불가")
    
    # 대화 통계
    st.subheader("대화 통계")
    st.metric("대화 횟수", agent_status.get("conversation_count", 0))
    
    # 연결 테스트 버튼
    if st.button("🔄 연결 상태 새로고침"):
        st.rerun()
    
    # ADK API 서버 직접 테스트 버튼
    if st.button("🧪 ADK API 기본 테스트"):
        connection_status = st.session_state.chat_manager.check_adk_api_connection(test_chat=False)
        if connection_status["status"] == "healthy":
            st.success("✅ ADK API 서버 연결 성공!")
        elif connection_status["status"] == "partial":
            st.warning("⚠️ 부분 연결 - 에이전트 문제 있음")
        else:
            st.error("❌ ADK API 서버 연결 실패")
        st.json(connection_status)
    
    # 완전한 채팅 테스트 버튼
    if st.button("🚀 ADK API 완전 테스트"):
        with st.spinner("채팅 테스트 중..."):
            connection_status = st.session_state.chat_manager.check_adk_api_connection(test_chat=True)
            
            if connection_status["status"] == "healthy" and connection_status.get("chat_test"):
                st.success("✅ 완전 테스트 성공! 모든 기능 정상")
            elif connection_status["status"] == "partial":
                st.error("❌ 채팅 테스트 실패")
                st.warning(f"오류: {connection_status.get('chat_error', '알 수 없는 오류')}")
            else:
                st.error("❌ 서버 연결 실패")
            
            st.json(connection_status)
    
    # 기록 초기화 버튼
    if st.button("🗑️ 대화 기록 초기화"):
        st.session_state.chat_manager.clear_history()
        st.session_state.messages = []
        st.session_state.message_count = 0
        st.success("대화 기록이 초기화되었습니다!")
        st.rerun()

# 메인 화면
st.title("🏠 인테리어 프로젝트 AI 어시스턴트")
st.markdown("### 인테리어 공사 관리를 위한 전문 AI 어시스턴트입니다")

# 에이전트 상태 표시
col1, col2, col3 = st.columns(3)
with col1:
    if agent_status.get("agent_available"):
        st.success(f"🤖 {agent_status.get('agent_name', 'Unknown')} 연결됨")
    else:
        st.error("🤖 에이전트 연결 안됨")

with col2:
    st.info(f"💬 대화 수: {len(st.session_state.messages)}")

with col3:
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    st.info(f"🕐 현재 시간: {current_time}")

# 사용 가능한 명령어 안내
with st.expander("📋 사용 가능한 명령어", expanded=False):
    st.markdown("""
    **주소 관리:**
    - "주소 리스트 보여줘" - 등록된 모든 주소 조회
    - "주소 상세 목록 보여줘" - 상세 정보 포함 조회
    - "강남 주소 검색해줘" - 키워드로 주소 검색
    
    **프로젝트 관리:**
    - "새로운 인테리어 프로젝트를 시작하고 싶어요"
    - "프로젝트 진행 상황을 알려주세요"
    - "공사 일정을 관리하고 싶어요"
    
    **지급 관리:**
    - "3000만원 예산으로 지급 계획을 세워주세요"
    - "분할 지급 방식을 설명해주세요"
    - "지급 내역을 확인하고 싶어요"
    """)

# 대화 기록 표시
st.subheader("💬 대화 기록")

# 기존 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
user_input = st.chat_input(
    "인테리어 프로젝트에 대해 질문하세요...",
    key=f"chat_input_{st.session_state.message_count}"
)

if user_input:
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("응답 생성 중..."):
            try:
                # ChatManager를 통해 응답 생성
                response = st.session_state.chat_manager.get_response(user_input)
                
                # 응답 표시
                st.markdown(response)
                
                # 응답을 세션에 저장
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_message = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
    
    # 메시지 카운트 증가
    st.session_state.message_count += 1
    
    # 자동 스크롤을 위한 리런
    st.rerun()

# 페이지 하단 정보
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    🏠 인테리어 프로젝트 AI 어시스턴트 | 
    📍 주소 관리 | 💰 지급 계획 | 📅 일정 관리 | 
    🔧 Firebase 연동
</div>
""", unsafe_allow_html=True) 