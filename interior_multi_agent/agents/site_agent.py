from datetime import datetime
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from ..config.settings import project_data, LLM_MODEL

def register_site(site_id: str, address: str, area_sqm: float) -> dict:
    """현장 정보를 등록합니다."""
    project_data["sites"][site_id] = {
        "address": address,
        "area_sqm": area_sqm,
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return {
        "status": "success",
        "message": f"현장 {site_id}가 등록되었습니다.",
        "site_info": project_data["sites"][site_id]
    }

def get_site_info(site_id: str) -> dict:
    """현장 정보를 조회합니다."""
    if site_id in project_data["sites"]:
        return {
            "status": "success",
            "site_info": project_data["sites"][site_id]
        }
    else:
        return {
            "status": "error",
            "message": f"현장 {site_id}를 찾을 수 없습니다."
        }

def list_all_sites() -> dict:
    """등록된 모든 현장 목록을 조회합니다."""
    return {
        "status": "success",
        "sites": project_data["sites"],
        "total_count": len(project_data["sites"])
    }

# Site Agent 초기화
site_agent = LlmAgent(
    name="site_manager",
    model=LLM_MODEL,
    description="현장 관리를 담당하는 Site Agent",
    instruction="""
    당신은 인테리어 현장 관리를 담당하는 전문 Agent입니다.
    
    주요 기능:
    1. 현장 등록 및 정보 관리
    2. 현장 정보 조회
    3. 현장 목록 관리
    """,
    tools=[
        FunctionTool(register_site),
        FunctionTool(get_site_info),
        FunctionTool(list_all_sites)
    ]
) 