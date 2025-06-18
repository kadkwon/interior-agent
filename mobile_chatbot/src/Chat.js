import React, { useState, useRef, useEffect } from 'react';
import './Chat.css';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [serverStatus, setServerStatus] = useState('checking');
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // API 설정
  const API_BASE_URL = "http://localhost:8505";
  const CHAT_ENDPOINT = `${API_BASE_URL}/chat`;
  const HEALTH_ENDPOINT = `${API_BASE_URL}/health`;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 서버 상태 확인
  const checkServerHealth = async () => {
    try {
      const response = await fetch(HEALTH_ENDPOINT, {
        method: 'GET',
        timeout: 5000
      });
      
      if (response.ok) {
        const data = await response.json();
        setServerStatus(data.firebase_connected ? 'connected' : 'loading');
      } else {
        setServerStatus('error');
      }
    } catch (error) {
      setServerStatus('disconnected');
    }
  };

  // 컴포넌트 마운트 시 서버 상태 확인
  useEffect(() => {
    checkServerHealth();
    const interval = setInterval(checkServerHealth, 30000); // 30초마다 체크
    return () => clearInterval(interval);
  }, []);

  const handleSend = async () => {
    if (!inputMessage.trim()) return;

    // 서버 연결 상태 확인
    if (serverStatus !== 'connected') {
      setMessages(prev => [...prev, {
        type: 'error',
        content: '서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.'
      }]);
      return;
    }

    // Add user message
    const userMessage = {
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');

    try {
      // Add loading message
      setMessages(prev => [...prev, { type: 'loading', content: '🤔 생각 중...' }]);

      // Call Firebase MCP Interior Agent
      const response = await fetch(CHAT_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          session_id: `react-session-${Date.now()}`  // React 세션 ID
        })
      });

      const data = await response.json();

      // Remove loading message and add bot response
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.type !== 'loading');
        return [...filtered, {
          type: 'bot',
          content: data.response || '응답을 받을 수 없습니다.',
          timestamp: data.timestamp || new Date().toISOString(),
          agent_status: data.agent_status,
          firebase_tools_used: data.firebase_tools_used || []
        }];
      });
    } catch (error) {
      // Remove loading message and add error message
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.type !== 'loading');
        return [...filtered, {
          type: 'error',
          content: '죄송합니다. 서버와 통신 중 오류가 발생했습니다.',
          timestamp: new Date().toISOString()
        }];
      });
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 서버 상태 표시 컴포넌트
  const ServerStatusIndicator = () => {
    const statusConfig = {
      'connected': { icon: '🟢', text: 'Firebase 연결됨', class: 'status-connected' },
      'loading': { icon: '🟡', text: '로딩 중', class: 'status-loading' },
      'error': { icon: '🔴', text: '서버 오류', class: 'status-error' },
      'disconnected': { icon: '🔴', text: '연결 실패', class: 'status-disconnected' },
      'checking': { icon: '🔄', text: '상태 확인 중', class: 'status-checking' }
    };

    const config = statusConfig[serverStatus] || statusConfig['checking'];

    return (
      <div className={`server-status ${config.class}`}>
        <span className="status-icon">{config.icon}</span>
        <span className="status-text">{config.text}</span>
      </div>
    );
  };

  return (
    <div className="chat-container" ref={chatContainerRef}>
      <div className="chat-header">
        <h1 className="chat-title">🏠 인테리어 에이전트</h1>
        <ServerStatusIndicator />
      </div>
      
      <div className="messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>안녕하세요! 인테리어 전문 에이전트입니다.</p>
            <p>인테리어 디자인, 시공, 예산 등 무엇이든 물어보세요!</p>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.type}`}>
            <div className="message-content">
              {message.content}
              {message.firebase_tools_used && message.firebase_tools_used.length > 0 && (
                <div className="tools-used">
                  <span className="tools-label">🔧 사용된 도구:</span>
                  {message.firebase_tools_used.map((tool, i) => (
                    <span key={i} className="tool-tag">{tool}</span>
                  ))}
                </div>
              )}
              {message.timestamp && (
                <div className="message-timestamp">
                  {new Date(message.timestamp).toLocaleTimeString('ko-KR')}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-container">
        <textarea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="인테리어에 대해 무엇이든 물어보세요..."
          rows="1"
          disabled={serverStatus !== 'connected'}
        />
        <button 
          onClick={handleSend}
          disabled={serverStatus !== 'connected' || !inputMessage.trim()}
        >
          전송
        </button>
      </div>
    </div>
  );
};

export default Chat; 