import streamlit as st
import requests
import json
from datetime import datetime
import time

# 페이지 설정 (모바일 최적화)
st.set_page_config(
    page_title="인테리어 에이전트",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API 설정
API_BASE_URL = "http://localhost:8505"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

# CSS 스타일 (모바일 최적화)
def load_css():
    st.markdown("""
    <style>
    /* main 클래스 - 메인 컨테이너 스타일 */
    .main-container {
        max-width: 100%;
        padding: 1rem;
        margin: 0 auto;
    }
    
    /* main 클래스 - 모바일 우선 설계 */
    @media (max-width: 768px) {
        .main-chat-area {
            height: 70vh;
            overflow-y: auto;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        
        .main-input-area {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            padding: 1rem;
            border-top: 1px solid #ddd;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        }
        
        .main-status-indicator {
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            z-index: 1000;
        }
    }
    
    /* main 클래스 - 데스크톱 스타일 */
    @media (min-width: 769px) {
        .main-container {
            max-width: 1200px;
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 2rem;
            height: 100vh;
        }
        
        .main-sidebar {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
        }
        
        .main-chat-area {
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        
        .main-messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background: white;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        
        .main-input-area {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #ddd;
        }
    }
    
    /* main 클래스 - 공통 스타일 */
    .main-message {
        margin-bottom: 1rem;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        max-width: 80%;
    }
    
    .main-user-message {
        background: #007bff;
        color: white;
        margin-left: auto;
        text-align: right;
    }
    
    .main-bot-message {
        background: #e9ecef;
        color: #333;
        margin-right: auto;
    }
    
    .main-status-connected {
        background: #28a745;
        color: white;
    }
    
    .main-status-disconnected {
        background: #dc3545;
        color: white;
    }
    
    .main-status-loading {
        background: #ffc107;
        color: black;
    }
    
    /* 스크롤바 스타일 */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {  
        background: #a8a8a8;
    }
    
    /* 입력 영역 스타일링 */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #007bff;
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }
    
    .stButton > button {
        border-radius: 25px;
        background: #007bff;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: bold;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: #0056b3;
    }
    
    /* 반응형 텍스트 */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.5rem;
            text-align: center;
            margin-bottom: 1rem;
        }
    }
    
    @media (min-width: 769px) {
        .main-title {
            font-size: 2rem;
            margin-bottom: 2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# API 클라이언트 함수들
def check_api_health():
    """API 서버 상태 확인"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "connected",
                "agent_available": data.get("agent_available", False),
                "message": "서버 연결됨"
            }
        else:
            return {
                "status": "error",
                "agent_available": False,
                "message": f"서버 오류: {response.status_code}"
            }
    except requests.exceptions.RequestException as e:
        return {
            "status": "disconnected",
            "agent_available": False,
            "message": "서버 연결 실패"
        }

def send_message(message, session_id="default"):
    """메시지 전송"""
    try:
        payload = {
            "message": message,
            "session_id": session_id
        }
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "response": f"오류가 발생했습니다: {response.status_code}",
                "agent_status": "error"
            }
    except requests.exceptions.RequestException as e:
        return {
            "response": f"통신 오류: {str(e)}",
            "agent_status": "error"
        }

# 상태 표시 컴포넌트
def display_status(health_info):
    """연결 상태 표시"""
    if health_info["status"] == "connected" and health_info["agent_available"]:
        status_class = "main-status-connected"
        icon = "🟢"
        message = "연결됨"
    elif health_info["status"] == "connected":
        status_class = "main-status-loading"
        icon = "🟡"
        message = "에이전트 로딩 중"
    else:
        status_class = "main-status-disconnected"
        icon = "🔴"
        message = "연결 실패"
    
    st.markdown(f"""
    <div class="main-status-indicator {status_class}">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)

# 메인 앱
def main():
    load_css()
    
    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    
    # 제목
    st.markdown('<h1 class="main-title">🏠 인테리어 에이전트</h1>', unsafe_allow_html=True)
    
    # API 상태 확인
    health_info = check_api_health()
    display_status(health_info)
    
    # 메시지 표시 영역
    st.markdown('<div class="main-messages">', unsafe_allow_html=True)
    
    # 대화 기록 표시
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="main-message main-user-message">
                <strong>나:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="main-message main-bot-message">
                <strong>🏠 에이전트:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 입력 영역
    st.markdown('<div class="main-input-area">', unsafe_allow_html=True)
    
    # 입력 폼
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "메시지를 입력하세요...",
                placeholder="인테리어에 대해 무엇이든 물어보세요!",
                label_visibility="collapsed"
            )
        
        with col2:
            submit_button = st.form_submit_button("전송")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 메시지 처리
    if submit_button and user_input:
        if health_info["status"] != "connected" or not health_info["agent_available"]:
            st.error("❌ 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.")
            return
        
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # 로딩 표시
        with st.spinner("🤔 생각 중..."):
            # API 호출
            response_data = send_message(user_input, st.session_state.session_id)
            
            # 에이전트 응답 추가
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_data.get("response", "응답을 받을 수 없습니다."),
                "timestamp": response_data.get("timestamp", datetime.now().isoformat())
            })
        
        # 페이지 새로고침하여 새 메시지 표시
        st.rerun()
    
    # 하단 정보
    st.markdown("---")
    st.markdown("💡 **사용 팁**: 인테리어 디자인, 시공 일정, 예산 계획 등 무엇이든 물어보세요!")

if __name__ == "__main__":
    main() 