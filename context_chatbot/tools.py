import json
import datetime
import requests
from typing import Dict, Any, List

def get_available_tools() -> List[Dict[str, Any]]:
    """사용 가능한 도구 목록을 반환합니다."""
    return [
        {
            "name": "calculator",
            "description": "수학 계산을 수행합니다",
            "parameters": {
                "expression": "계산할 수식 (예: 2+3*4)"
            }
        },
        {
            "name": "get_current_time",
            "description": "현재 시간을 조회합니다",
            "parameters": {}
        },
        {
            "name": "weather_info",
            "description": "날씨 정보를 조회합니다",
            "parameters": {
                "city": "도시명 (예: Seoul)"
            }
        }
    ]

def calculator(expression: str) -> Dict[str, Any]:
    """간단한 계산기 도구"""
    try:
        # 안전한 계산을 위해 허용된 문자만 사용
        allowed_chars = set('0123456789+-*/.()')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return {
                "success": False,
                "error": "허용되지 않은 문자가 포함되어 있습니다"
            }
        
        result = eval(expression)
        return {
            "success": True,
            "result": result,
            "expression": expression
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"계산 오류: {str(e)}"
        }

def get_current_time() -> Dict[str, Any]:
    """현재 시간을 반환하는 도구"""
    try:
        now = datetime.datetime.now()
        return {
            "success": True,
            "current_time": now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초"),
            "timestamp": now.isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"시간 조회 오류: {str(e)}"
        }

def weather_info(city: str) -> Dict[str, Any]:
    """날씨 정보 조회 도구 (시뮬레이션)"""
    # 실제 API 대신 시뮬레이션 데이터 반환
    weather_data = {
        "Seoul": {"temp": "15°C", "condition": "맑음", "humidity": "60%"},
        "Busan": {"temp": "18°C", "condition": "흐림", "humidity": "70%"},
        "Jeju": {"temp": "20°C", "condition": "비", "humidity": "85%"}
    }
    
    try:
        if city in weather_data:
            return {
                "success": True,
                "city": city,
                "weather": weather_data[city]
            }
        else:
            return {
                "success": True,
                "city": city,
                "weather": {"temp": "알 수 없음", "condition": "정보 없음", "humidity": "알 수 없음"},
                "note": "시뮬레이션 데이터입니다"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"날씨 조회 오류: {str(e)}"
        }

def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """도구를 실행하고 결과를 반환합니다."""
    tools = {
        "calculator": calculator,
        "get_current_time": get_current_time,
        "weather_info": weather_info
    }
    
    if tool_name not in tools:
        return {
            "success": False,
            "error": f"알 수 없는 도구: {tool_name}"
        }
    
    try:
        return tools[tool_name](**parameters)
    except Exception as e:
        return {
            "success": False,
            "error": f"도구 실행 오류: {str(e)}"
        } 