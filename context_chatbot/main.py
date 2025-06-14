import streamlit as st
import datetime
from chat_manager import ChatManager

# 페이지 설정
st.set_page_config(
    page_title="맥락 인식 챗봇",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 커스텀 CSS - 미니멀한 화이트 배경과 정확한 테두리 디자인
st.markdown("""
<style>
    /* 전체 페이지 설정 */
    .stApp {
        background-color: white;
        max-width: 100% !important;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 8rem;
        max-width: 900px;
        width: 100%;
    }
    
    /* 헤더 - 미니멀하게 */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 2rem 0;
        border-bottom: 1px solid #e1e4e8;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: #24292f;
        font-weight: 400;
        margin: 0;
        font-size: 1.75rem;
        letter-spacing: -0.025em;
    }
    
    /* 채팅 메시지 영역 */
    .chat-messages {
        min-height: 400px;
        padding-bottom: 2rem;
    }
    
    /* 메시지 컨테이너 */
    .message-container {
        margin: 1.5rem 0;
        display: flex;
        width: 100%;
    }
    
    .user-message {
        justify-content: flex-end;
    }
    
    /* 메시지 말풍선 */
    .message-bubble {
        max-width: 75%;
        padding: 1rem 1.25rem;
        border-radius: 12px;
        border: 1px solid #d0d7de;
        background-color: #ffffff;
        word-wrap: break-word;
        line-height: 1.5;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .user-bubble {
        background-color: #f6f8fa;
        border-color: #d0d7de;
    }
    
    .assistant-bubble {
        background-color: #ffffff;
        border-color: #d0d7de;
    }
    
    .message-role {
        font-size: 0.75rem;
        color: #656d76;
        margin-bottom: 0.5rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    
    .message-content {
        color: #24292f;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    .message-time {
        font-size: 0.7rem;
        color: #8b949e;
        margin-top: 0.5rem;
        text-align: right;
    }
    
    /* 도구 호출 시각화 - 개선된 스타일 */
    .tool-execution {
        margin: 0.75rem 0;
        padding: 0.75rem;
        background-color: #f0f6ff;
        border: 1px solid #d0d7de;
        border-left: 3px solid #0969da;
        border-radius: 6px;
        font-size: 0.85rem;
    }
    
    .tool-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .tool-name {
        font-weight: 600;
        color: #0969da;
    }
    
    .tool-status {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        border: 1px solid;
    }
    
    .tool-success {
        background-color: #dafbe1;
        border-color: #1f883d;
        color: #1f883d;
    }
    
    .tool-error {
        background-color: #ffebe9;
        border-color: #da3633;
        color: #da3633;
    }
    
    .tool-details {
        font-size: 0.8rem;
        color: #656d76;
        margin-top: 0.25rem;
    }
    
    /* 환영 메시지 */
    .welcome-message {
        text-align: center;
        padding: 2rem;
        background-color: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 8px;
        margin: 2rem 0;
    }
    
    .welcome-content {
        color: #24292f;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    .tool-list {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin-top: 1rem;
    }
    
    .tool-item {
        text-align: center;
        padding: 0.75rem;
        background-color: white;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        min-width: 80px;
    }
    
    .tool-icon {
        font-size: 1.5rem;
        margin-bottom: 0.25rem;
    }
    
    .tool-label {
        font-size: 0.7rem;
        color: #656d76;
        font-weight: 500;
    }
    
    /* 입력 영역 - 하단 고정 */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: white;
        border-top: 1px solid #d0d7de;
        padding: 1rem;
        z-index: 1000;
        box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.08);
    }
    
    .input-wrapper {
        max-width: 900px;
        margin: 0 auto;
        display: flex;
        gap: 0.75rem;
        align-items: stretch;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background-color: #f6f8fa;
        border: 1px solid #d0d7de;
        color: #24292f;
        border-radius: 6px;
        padding: 0.75rem 1.25rem;
        font-weight: 500;
        height: 100%;
        transition: all 0.15s ease;
    }
    
    .stButton > button:hover {
        background-color: #f3f4f6;
        border-color: #afb8c1;
    }
    
    .stButton > button:active {
        background-color: #edeff2;
    }
    
    /* 텍스트 입력 */
    .stTextInput > div > div > input {
        border: 1px solid #d0d7de;
        border-radius: 6px;
        background-color: white;
        color: #24292f;
        padding: 0.75rem 1rem;
        font-size: 0.95rem;
        transition: border-color 0.15s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #0969da;
        box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.12);
        outline: none;
    }
    
    /* 초기화 버튼 */
    .clear-button {
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .clear-button button {
        background-color: white !important;
        border: 1px solid #d0d7de !important;
        color: #656d76 !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.8rem !important;
    }
    
    .clear-button button:hover {
        background-color: #f6f8fa !important;
    }
    
    /* 로딩 표시 */
    .loading-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        color: #656d76;
        font-size: 0.9rem;
        padding: 1rem;
        background-color: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        margin: 1rem 0;
    }
    
    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }
        
        .main-header h1 {
            font-size: 1.5rem;
        }
        
        .message-bubble {
            max-width: 85%;
            padding: 0.875rem 1rem;
        }
        
        .input-container {
            padding: 0.75rem;
        }
        
        .tool-list {
            flex-direction: column;
            gap: 0.75rem;
        }
        
        .tool-item {
            min-width: auto;
        }
    }
    
    @media (min-width: 1200px) {
        .main .block-container {
            max-width: 1100px;
        }
        
        .input-wrapper {
            max-width: 1100px;
        }
        
        .message-bubble {
            max-width: 70%;
        }
    }
    
    /* Streamlit 기본 요소 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 스크롤바 스타일 */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f3f4;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c8cd;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8b3ba;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'chat_manager' not in st.session_state:
    st.session_state.chat_manager = ChatManager()

if 'processing' not in st.session_state:
    st.session_state.processing = False

# 헤더 - 미니멀하게
st.markdown("""
<div class="main-header">
    <h1>🤖 맥락 인식 챗봇</h1>
</div>
""", unsafe_allow_html=True)

# 초기화 버튼
with st.container():
    st.markdown('<div class="clear-button">', unsafe_allow_html=True)
    if st.button("🗑️ 대화 초기화", key="clear_chat", use_container_width=False):
        st.session_state.chat_manager.clear_history()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 채팅 메시지 표시
st.markdown('<div class="chat-messages">', unsafe_allow_html=True)

messages = st.session_state.chat_manager.get_conversation_display()

if not messages:
    # 환영 메시지 - 미니멀하게
    st.markdown("""
    <div class="welcome-message">
        <div class="welcome-content">
            안녕하세요! 맥락을 기억하는 AI 챗봇입니다.
        </div>
        <div class="tool-list">
            <div class="tool-item">
                <div class="tool-icon">🧮</div>
                <div class="tool-label">계산기</div>
            </div>
            <div class="tool-item">
                <div class="tool-icon">⏰</div>
                <div class="tool-label">시간</div>
            </div>
            <div class="tool-item">
                <div class="tool-icon">🌤️</div>
                <div class="tool-label">날씨</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

for msg in messages:
    role_kr = "사용자" if msg["role"] == "user" else "어시스턴트"
    bubble_class = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
    container_class = "user-message" if msg["role"] == "user" else ""
    
    # 메시지 시간 포맷팅
    try:
        msg_time = datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M")
    except:
        msg_time = ""
    
    message_html = f"""
    <div class="message-container {container_class}">
        <div class="message-bubble {bubble_class}">
            <div class="message-role">{role_kr}</div>
            <div class="message-content">{msg["content"]}</div>
    """
    
    # 도구 호출 표시 - 개선된 시각화
    if msg.get("tool_calls"):
        for i, (tool_call, tool_result) in enumerate(zip(msg["tool_calls"], msg.get("tool_results", []))):
            tool_name_kr = {
                "calculator": "계산기",
                "get_current_time": "시간 조회",
                "weather_info": "날씨 조회"
            }.get(tool_call["name"], tool_call["name"])
            
            # 도구 실행 상태
            if tool_result and tool_result.get("success"):
                status_class = "tool-success"
                status_text = "완료"
                status_icon = "✅"
            else:
                status_class = "tool-error"
                status_text = "오류"
                status_icon = "❌"
            
            message_html += f"""
            <div class="tool-execution">
                <div class="tool-header">
                    <span class="tool-name">🔧 {tool_name_kr}</span>
                    <span class="tool-status {status_class}">{status_icon} {status_text}</span>
                </div>
            """
            
            # 도구 실행 세부 정보
            if tool_result:
                if tool_result.get("success"):
                    if tool_call["name"] == "calculator":
                        message_html += f'<div class="tool-details">수식: {tool_call["parameters"].get("expression", "")}</div>'
                    elif tool_call["name"] == "weather_info":
                        message_html += f'<div class="tool-details">도시: {tool_call["parameters"].get("city", "")}</div>'
                else:
                    message_html += f'<div class="tool-details">오류: {tool_result.get("error", "알 수 없는 오류")}</div>'
            
            message_html += "</div>"
    
    message_html += f"""
            <div class="message-time">{msg_time}</div>
        </div>
    </div>
    """
    
    st.markdown(message_html, unsafe_allow_html=True)

# 처리 중 표시
if st.session_state.processing:
    st.markdown("""
    <div class="loading-indicator">
        <span>🤖</span>
        <span>처리 중...</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 입력 영역 - 하단 고정
st.markdown("""
<div class="input-container">
    <div class="input-wrapper">
""", unsafe_allow_html=True)

# 사용자 입력
with st.container():
    col_input, col_send = st.columns([5, 1])
    
    with col_input:
        user_input = st.text_input(
            "",
            key="user_input",
            placeholder="메시지를 입력하세요...",
            label_visibility="collapsed"
        )
    
    with col_send:
        send_button = st.button("전송", key="send_button", use_container_width=True)

st.markdown("""
    </div>
</div>
""", unsafe_allow_html=True)

# 메시지 처리
if (send_button or user_input) and user_input and not st.session_state.processing:
    st.session_state.processing = True
    
    # 사용자 메시지 처리
    response_data = st.session_state.chat_manager.process_user_message(user_input)
    
    st.session_state.processing = False
    
    # 입력 필드 초기화
    st.session_state.user_input = ""
    
    # 페이지 새로고침
    st.rerun()

# JavaScript - 모바일 최적화 및 기능 개선
st.markdown("""
<script>
    // Enter 키로 전송
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey && !event.ctrlKey) {
            const inputField = document.querySelector('input[type="text"]');
            const sendButton = document.querySelector('[data-testid="stButton"] button');
            
            if (inputField === document.activeElement && sendButton && inputField.value.trim()) {
                event.preventDefault();
                sendButton.click();
            }
        }
    });
    
    // 자동 스크롤
    function scrollToBottom() {
        const chatMessages = document.querySelector('.chat-messages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: 'smooth'
            });
        }
    }
    
    // 페이지 로드 및 새 메시지 시 스크롤
    setTimeout(scrollToBottom, 100);
    
    // 모바일 키보드 대응
    window.addEventListener('resize', function() {
        setTimeout(scrollToBottom, 150);
    });
    
    // 입력 포커스 시 스크롤 조정
    const inputField = document.querySelector('input[type="text"]');
    if (inputField) {
        inputField.addEventListener('focus', function() {
            setTimeout(scrollToBottom, 300);
        });
    }
</script>
""", unsafe_allow_html=True) 