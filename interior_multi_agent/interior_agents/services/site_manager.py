from datetime import datetime

# 전역 데이터 저장소 (실제 프로젝트에서는 데이터베이스 사용)
project_data = {
    "sites": {}
}

# 1. 현장주소 관리 에이전트
def register_site(site_id: str, address: str, area_sqm: float) -> dict:
    """현장 정보를 등록합니다.
    
    Args:
        site_id: 현장 고유 식별자
        address: 현장 주소
        area_sqm: 현장 면적 (제곱미터)
    
    Returns:
        dict: 등록 결과와 현장 정보
    """
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
    """현장 정보를 조회합니다.
    
    Args:
        site_id: 현장 고유 식별자
        
    Returns:
        dict: 현장 정보 또는 에러 메시지
    """
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
    """등록된 모든 현장 목록을 조회합니다.
    
    Returns:
        dict: 모든 현장 목록
    """
    return {
        "status": "success",
        "sites": project_data["sites"],
        "total_count": len(project_data["sites"])
    } 