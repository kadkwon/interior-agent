"""
기본 도구 클래스 정의
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class Tool(ABC):
    """기본 도구 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """도구 실행"""
        pass

class ToolRegistry:
    """도구 레지스트리"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        
    def register(self, tool: Tool) -> None:
        """도구 등록"""
        self._tools[tool.name] = tool
        
    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """도구 실행"""
        if tool_name not in self._tools:
            raise ValueError(f"도구를 찾을 수 없음: {tool_name}")
        return await self._tools[tool_name].execute(params) 