import React, { useState, useRef, useEffect } from 'react';
import './Chat.css';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputMessage.trim()) return;

    // Add user message
    const userMessage = {
      type: 'user',
      content: inputMessage
    };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');

    try {
      // Add loading message
      setMessages(prev => [...prev, { type: 'loading', content: '...' }]);

      // Call Interior Agent
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          sessionId: 'user-123'  // 실제 구현시 사용자별 세션 ID 생성 필요
        })
      });

      const data = await response.json();

      // Remove loading message and add bot response
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.type !== 'loading');
        return [...filtered, {
          type: 'bot',
          content: data.error ? `오류: ${data.error}` : data.response,
          tools: data.toolsUsed
        }];
      });
    } catch (error) {
      // Remove loading message and add error message
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.type !== 'loading');
        return [...filtered, {
          type: 'error',
          content: '죄송합니다. 서버와 통신 중 오류가 발생했습니다.'
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

  return (
    <div className="chat-container" ref={chatContainerRef}>
      <div className="messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.type}`}>
            <div className="message-content">
              {message.content}
              {message.tools && (
                <div className="tools-used">
                  {message.tools.map((tool, i) => (
                    <span key={i} className="tool-tag">{tool}</span>
                  ))}
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
          placeholder="메시지를 입력하세요..."
          rows="1"
        />
        <button onClick={handleSend}>전송</button>
      </div>
    </div>
  );
};

export default Chat; 