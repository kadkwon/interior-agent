import json
import datetime
from typing import List, Dict, Any
from tools import get_available_tools, execute_tool

class ChatManager:
    def __init__(self):
        self.conversation_history: List[Dict[str, Any]] = []
        self.context_summary = ""
        self.max_history_length = 20
    
    def add_message(self, role: str, content: str, tool_calls: List[Dict] = None, tool_results: List[Dict] = None):
        """대화 기록에 메시지를 추가합니다."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat(),
            "tool_calls": tool_calls or [],
            "tool_results": tool_results or []
        }
        
        self.conversation_history.append(message)
        
        # 대화 기록이 너무 길어지면 요약
        if len(self.conversation_history) > self.max_history_length:
            self._summarize_old_messages()
    
    def _summarize_old_messages(self):
        """오래된 메시지들을 요약합니다."""
        # 앞의 10개 메시지를 요약하고 제거
        old_messages = self.conversation_history[:10]
        self.conversation_history = self.conversation_history[10:]
        
        # 간단한 요약 생성
        summary_points = []
        for msg in old_messages:
            if msg["role"] == "user":
                summary_points.append(f"사용자: {msg['content'][:50]}...")
            elif msg["role"] == "assistant":
                summary_points.append(f"AI: {msg['content'][:50]}...")
        
        self.context_summary = " | ".join(summary_points)
    
    def get_context_for_ai(self) -> str:
        """AI에게 전달할 컨텍스트를 생성합니다."""
        context = ""
        
        if self.context_summary:
            context += f"이전 대화 요약: {self.context_summary}\n\n"
        
        context += "최근 대화:\n"
        for msg in self.conversation_history[-5:]:  # 최근 5개 메시지만
            role_kr = "사용자" if msg["role"] == "user" else "AI"
            context += f"{role_kr}: {msg['content']}\n"
            
            if msg.get("tool_calls"):
                context += f"도구 사용: {[tool['name'] for tool in msg['tool_calls']]}\n"
        
        return context
    
    def process_user_message(self, user_input: str) -> Dict[str, Any]:
        """사용자 메시지를 처리하고 AI 응답을 생성합니다."""
        # 사용자 메시지 추가
        self.add_message("user", user_input)
        
        # 도구 사용이 필요한지 판단
        tool_calls, tool_results = self._check_and_execute_tools(user_input)
        
        # AI 응답 생성
        ai_response = self._generate_ai_response(user_input, tool_calls, tool_results)
        
        # AI 응답 추가
        self.add_message("assistant", ai_response, tool_calls, tool_results)
        
        return {
            "response": ai_response,
            "tool_calls": tool_calls,
            "tool_results": tool_results
        }
    
    def _check_and_execute_tools(self, user_input: str) -> tuple:
        """사용자 입력에서 도구 사용이 필요한지 확인하고 실행합니다."""
        tool_calls = []
        tool_results = []
        
        user_lower = user_input.lower()
        
        # 계산 요청 감지
        if any(word in user_lower for word in ['계산', '더하기', '빼기', '곱하기', '나누기', '+', '-', '*', '/']):
            # 수식 추출 시도
            import re
            math_pattern = r'[\d+\-*/().\s]+'
            matches = re.findall(math_pattern, user_input)
            if matches:
                expression = max(matches, key=len).strip()
                if len(expression) > 1:
                    tool_calls.append({
                        "name": "calculator",
                        "parameters": {"expression": expression}
                    })
                    result = execute_tool("calculator", {"expression": expression})
                    tool_results.append(result)
        
        # 시간 요청 감지
        if any(word in user_lower for word in ['시간', '몇시', '지금', '현재']):
            tool_calls.append({
                "name": "get_current_time",
                "parameters": {}
            })
            result = execute_tool("get_current_time", {})
            tool_results.append(result)
        
        # 날씨 요청 감지
        if any(word in user_lower for word in ['날씨', '기온', '온도']):
            # 도시명 추출 시도
            cities = ['서울', 'seoul', '부산', 'busan', '제주', 'jeju']
            city = 'Seoul'  # 기본값
            for c in cities:
                if c in user_lower:
                    if c in ['서울', 'seoul']:
                        city = 'Seoul'
                    elif c in ['부산', 'busan']:
                        city = 'Busan'
                    elif c in ['제주', 'jeju']:
                        city = 'Jeju'
                    break
            
            tool_calls.append({
                "name": "weather_info",
                "parameters": {"city": city}
            })
            result = execute_tool("weather_info", {"city": city})
            tool_results.append(result)
        
        return tool_calls, tool_results
    
    def _generate_ai_response(self, user_input: str, tool_calls: List[Dict], tool_results: List[Dict]) -> str:
        """AI 응답을 생성합니다."""
        # 도구 실행 결과가 있으면 그것을 포함해서 응답
        if tool_results:
            response_parts = []
            
            for i, (tool_call, result) in enumerate(zip(tool_calls, tool_results)):
                tool_name = tool_call["name"]
                
                if tool_name == "calculator" and result["success"]:
                    response_parts.append(f"계산 결과: {result['expression']} = {result['result']}")
                
                elif tool_name == "get_current_time" and result["success"]:
                    response_parts.append(f"현재 시간: {result['current_time']}")
                
                elif tool_name == "weather_info" and result["success"]:
                    weather = result["weather"]
                    response_parts.append(
                        f"{result['city']} 날씨: {weather['condition']}, "
                        f"기온 {weather['temp']}, 습도 {weather['humidity']}"
                    )
                
                elif not result["success"]:
                    response_parts.append(f"오류가 발생했습니다: {result['error']}")
            
            if response_parts:
                base_response = " | ".join(response_parts)
                return f"{base_response}\n\n다른 궁금한 것이 있으시면 언제든 말씀해주세요!"
        
        # 일반적인 대화 응답
        context = self.get_context_for_ai()
        
        # 간단한 응답 생성 로직
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['안녕', '하이', '헬로']):
            return "안녕하세요! 저는 맥락을 기억하는 AI 챗봇입니다. 계산, 시간 조회, 날씨 정보 등을 도와드릴 수 있어요. 무엇을 도와드릴까요?"
        
        elif any(word in user_lower for word in ['도움', '뭐할수있어', '기능']):
            tools = get_available_tools()
            tool_descriptions = [f"• {tool['name']}: {tool['description']}" for tool in tools]
            return f"제가 도와드릴 수 있는 것들:\n" + "\n".join(tool_descriptions) + "\n\n무엇을 도와드릴까요?"
        
        elif '?' in user_input or '궁금' in user_lower:
            return "좋은 질문이네요! 계산이나 시간, 날씨 관련 질문이라면 정확한 정보를 제공해드릴 수 있습니다. 구체적으로 무엇이 궁금하신가요?"
        
        else:
            return f"말씀하신 '{user_input}'에 대해 생각해보니, 더 구체적인 정보가 있으면 좋겠어요. 계산이나 시간, 날씨 같은 정보가 필요하시면 언제든 말씀해주세요!"
    
    def clear_history(self):
        """대화 기록을 초기화합니다."""
        self.conversation_history = []
        self.context_summary = ""
    
    def get_conversation_display(self) -> List[Dict[str, Any]]:
        """화면에 표시할 대화 기록을 반환합니다."""
        display_messages = []
        
        for msg in self.conversation_history:
            display_msg = {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"],
                "tool_calls": msg.get("tool_calls", []),
                "tool_results": msg.get("tool_results", [])
            }
            display_messages.append(display_msg)
        
        return display_messages 