from google.adk.agents import Agent
import json
from datetime import datetime
from .firebase_client import firebase_client, schedule_formatter

# 전역 데이터 저장소 (실제 프로젝트에서는 데이터베이스 사용)
project_data = {
    "sites": {},
    "costs": {},
    "payments": {}
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

# 2. 원가 계산 에이전트  
def calculate_material_cost(site_id: str, material_type: str, quantity: float) -> dict:
    """자재 원가를 계산합니다.
    
    Args:
        site_id: 현장 고유 식별자
        material_type: 자재 종류 (paint, tile, wallpaper, flooring)
        quantity: 수량 (제곱미터)
        
    Returns:
        dict: 계산된 원가 정보
    """
    # 기본 자재 단가 (원/단위)
    material_prices = {
        "paint": 15000,      # 원/㎡ - 페인트
        "tile": 30000,       # 원/㎡ - 타일
        "wallpaper": 20000,  # 원/㎡ - 벽지
        "flooring": 50000,   # 원/㎡ - 바닥재
        "lighting": 100000,  # 원/개 - 조명
        "cabinet": 200000    # 원/㎡ - 수납장
    }
    
    if material_type not in material_prices:
        available_materials = ", ".join(material_prices.keys())
        return {
            "status": "error", 
            "message": f"지원하지 않는 자재 종류: {material_type}. 사용 가능한 자재: {available_materials}"
        }
    
    unit_price = material_prices[material_type]
    total_cost = unit_price * quantity
    
    # 현장별 원가 데이터 저장
    if site_id not in project_data["costs"]:
        project_data["costs"][site_id] = {}
    
    project_data["costs"][site_id][material_type] = {
        "quantity": quantity,
        "unit_price": unit_price,
        "total_cost": total_cost,
        "calculated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return {
        "status": "success",
        "site_id": site_id,
        "material": material_type,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_cost": total_cost,
        "message": f"{material_type} {quantity}㎡의 원가가 계산되었습니다: {total_cost:,}원"
    }

def get_total_cost(site_id: str) -> dict:
    """현장의 총 원가를 계산합니다.
    
    Args:
        site_id: 현장 고유 식별자
        
    Returns:
        dict: 총 원가와 상세 내역
    """
    if site_id not in project_data["costs"]:
        return {
            "status": "error",
            "message": f"현장 {site_id}의 원가 데이터가 없습니다."
        }
    
    total = 0
    details = []
    
    for material, cost_info in project_data["costs"][site_id].items():
        total += cost_info["total_cost"]
        details.append({
            "material": material,
            "quantity": cost_info["quantity"],
            "unit_price": cost_info["unit_price"],
            "cost": cost_info["total_cost"]
        })
    
    return {
        "status": "success",
        "site_id": site_id,
        "total_cost": total,
        "cost_breakdown": details,
        "message": f"현장 {site_id}의 총 원가: {total:,}원"
    }

def estimate_labor_cost(site_id: str, work_type: str, days: int) -> dict:
    """인건비를 추정합니다.
    
    Args:
        site_id: 현장 고유 식별자
        work_type: 작업 종류 (painting, tiling, general)
        days: 작업 일수
        
    Returns:
        dict: 추정된 인건비
    """
    # 작업별 일당 (원/일)
    daily_rates = {
        "painting": 150000,   # 페인트 작업
        "tiling": 200000,     # 타일 작업
        "flooring": 180000,   # 바닥재 작업
        "general": 120000     # 일반 작업
    }
    
    if work_type not in daily_rates:
        available_types = ", ".join(daily_rates.keys())
        return {
            "status": "error",
            "message": f"지원하지 않는 작업 종류: {work_type}. 사용 가능한 작업: {available_types}"
        }
    
    daily_rate = daily_rates[work_type]
    total_labor_cost = daily_rate * days
    
    # 인건비 데이터 저장
    if site_id not in project_data["costs"]:
        project_data["costs"][site_id] = {}
    
    labor_key = f"labor_{work_type}"
    project_data["costs"][site_id][labor_key] = {
        "work_type": work_type,
        "days": days,
        "daily_rate": daily_rate,
        "total_cost": total_labor_cost,
        "calculated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return {
        "status": "success",
        "site_id": site_id,
        "work_type": work_type,
        "days": days,
        "daily_rate": daily_rate,
        "total_labor_cost": total_labor_cost,
        "message": f"{work_type} 작업 {days}일의 인건비: {total_labor_cost:,}원"
    }

# 3. 결제 관리 에이전트
def create_payment_invoice(site_id: str, description: str) -> dict:
    """결제 내역서를 생성합니다.
    
    Args:
        site_id: 현장 고유 식별자
        description: 결제 내역 설명
        
    Returns:
        dict: 생성된 결제 내역서 정보
    """
    # 현장 정보 가져오기
    site_info = get_site_info(site_id)
    if site_info["status"] == "error":
        return site_info
    
    # 총 원가 가져오기  
    cost_info = get_total_cost(site_id)
    if cost_info["status"] == "error":
        return cost_info
    
    invoice_id = f"INV-{site_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    invoice = {
        "invoice_id": invoice_id,
        "site_id": site_id,
        "site_address": site_info["site_info"]["address"],
        "site_area": site_info["site_info"]["area_sqm"],
        "description": description,
        "total_amount": cost_info["total_cost"],
        "cost_breakdown": cost_info["cost_breakdown"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending"
    }
    
    project_data["payments"][invoice_id] = invoice
    
    return {
        "status": "success",
        "message": f"결제 내역서 {invoice_id}가 생성되었습니다.",
        "invoice": invoice
    }

def get_payment_status(invoice_id: str) -> dict:
    """결제 상태를 조회합니다.
    
    Args:
        invoice_id: 결제 내역서 ID
        
    Returns:
        dict: 결제 내역서 정보
    """
    if invoice_id in project_data["payments"]:
        return {
            "status": "success",
            "invoice": project_data["payments"][invoice_id]
        }
    else:
        return {
            "status": "error",
            "message": f"결제 내역서 {invoice_id}를 찾을 수 없습니다."
        }

def list_all_invoices() -> dict:
    """모든 결제 내역서를 조회합니다.
    
    Returns:
        dict: 모든 결제 내역서 목록
    """
    return {
        "status": "success",
        "invoices": project_data["payments"],
        "total_count": len(project_data["payments"])
    }

def update_payment_status(invoice_id: str, new_status: str) -> dict:
    """결제 상태를 업데이트합니다.
    
    Args:
        invoice_id: 결제 내역서 ID
        new_status: 새로운 상태 (pending, paid, cancelled)
        
    Returns:
        dict: 업데이트 결과
    """
    valid_statuses = ["pending", "paid", "cancelled"]
    
    if new_status not in valid_statuses:
        return {
            "status": "error",
            "message": f"올바르지 않은 상태: {new_status}. 사용 가능한 상태: {', '.join(valid_statuses)}"
        }
    
    if invoice_id not in project_data["payments"]:
        return {
            "status": "error",
            "message": f"결제 내역서 {invoice_id}를 찾을 수 없습니다."
        }
    
    old_status = project_data["payments"][invoice_id]["status"]
    project_data["payments"][invoice_id]["status"] = new_status
    project_data["payments"][invoice_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "status": "success",
        "message": f"결제 내역서 {invoice_id}의 상태가 {old_status} → {new_status}로 변경되었습니다.",
        "invoice_id": invoice_id,
        "old_status": old_status,
        "new_status": new_status
    }

# 4. 프로젝트 현황 관리
def get_project_summary() -> dict:
    """전체 프로젝트 현황을 요약합니다.
    
    Returns:
        dict: 프로젝트 전체 현황
    """
    total_sites = len(project_data["sites"])
    total_invoices = len(project_data["payments"])
    
    # 전체 매출 계산
    total_revenue = 0
    paid_revenue = 0
    
    for invoice in project_data["payments"].values():
        total_revenue += invoice["total_amount"]
        if invoice["status"] == "paid":
            paid_revenue += invoice["total_amount"]
    
    # 현장별 상태
    sites_with_costs = len(project_data["costs"])
    
    return {
        "status": "success",
        "summary": {
            "total_sites": total_sites,
            "sites_with_cost_calculation": sites_with_costs,
            "total_invoices": total_invoices,
            "total_revenue": total_revenue,
            "paid_revenue": paid_revenue,
            "pending_revenue": total_revenue - paid_revenue,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

# =================
# 🔥 FIREBASE 연동 도구들
# =================

def query_schedule_collection(limit: int = 50) -> dict:
    """
    Firebase Firestore의 schedule 컬렉션을 조회합니다.
    
    Args:
        limit: 조회할 일정 수 제한 (기본값: 50)
        
    Returns:
        dict: 일정 목록과 포맷팅된 결과
    """
    try:
        # Firebase Cloud Functions API 호출
        response = firebase_client.query_collection("schedule", limit=limit)
        
        # 포맷팅된 결과 생성
        formatted_result = schedule_formatter.format_schedule_data(response)
        
        return {
            "status": "success",
            "formatted_result": formatted_result,
            "raw_data": response,
            "message": f"schedule 컬렉션에서 {limit}개까지 조회했습니다."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"schedule 컬렉션 조회 중 오류 발생: {str(e)}"
        }

def get_firebase_project_info() -> dict:
    """
    Firebase 프로젝트 정보를 조회합니다.
    
    Returns:
        dict: 프로젝트 정보
    """
    try:
        response = firebase_client.get_project_info()
        
        if response.get("success"):
            project_data = response.get("data", {})
            return {
                "status": "success",
                "project_info": project_data,
                "message": f"프로젝트 '{project_data.get('projectId', 'Unknown')}'에 연결되었습니다."
            }
        else:
            return {
                "status": "error",
                "message": f"프로젝트 정보 조회 실패: {response.get('message', '알 수 없는 오류')}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Firebase 프로젝트 정보 조회 중 오류: {str(e)}"
        }

def list_firestore_collections() -> dict:
    """
    Firestore의 모든 컬렉션 목록을 조회합니다.
    
    Returns:
        dict: 컬렉션 목록
    """
    try:
        response = firebase_client.list_collections()
        
        if response.get("success"):
            collections = response.get("data", {}).get("collections", [])
            
            formatted_list = "📋 Firestore 컬렉션 목록:\n"
            for i, collection in enumerate(collections, 1):
                formatted_list += f"{i}. {collection}\n"
            
            return {
                "status": "success",
                "collections": collections,
                "formatted_list": formatted_list,
                "total_count": len(collections),
                "message": f"총 {len(collections)}개의 컬렉션이 있습니다."
            }
        else:
            return {
                "status": "error",
                "message": f"컬렉션 목록 조회 실패: {response.get('message', '알 수 없는 오류')}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"컬렉션 목록 조회 중 오류: {str(e)}"
        }

def query_any_collection(collection_name: str, limit: int = 50) -> dict:
    """
    지정된 Firestore 컬렉션을 조회합니다.
    
    Args:
        collection_name: 컬렉션 이름 (예: 'schedule', 'projects', 'users')
        limit: 조회할 문서 수 제한
        
    Returns:
        dict: 컬렉션 데이터
    """
    try:
        response = firebase_client.query_collection(collection_name, limit=limit)
        
        if response.get("success"):
            documents = response.get("data", {}).get("documents", [])
            
            # 기본 포맷팅
            formatted_result = f"📋 {collection_name} 컬렉션 조회 결과:\n"
            formatted_result += f"총 {len(documents)}개의 문서가 있습니다.\n\n"
            
            for i, doc in enumerate(documents, 1):
                doc_data = doc.get("data", {})
                doc_id = doc.get("id", "Unknown ID")
                
                formatted_result += f"{i}. 문서 ID: {doc_id}\n"
                
                # 주요 필드들 표시
                for key, value in doc_data.items():
                    if key in ['title', 'name', 'date', 'status', 'description']:
                        formatted_result += f"   {key}: {value}\n"
                
                formatted_result += f"   {'-' * 30}\n\n"
            
            return {
                "status": "success",
                "formatted_result": formatted_result,
                "raw_data": response,
                "collection_name": collection_name,
                "document_count": len(documents),
                "message": f"{collection_name} 컬렉션에서 {len(documents)}개 문서를 조회했습니다."
            }
        else:
            return {
                "status": "error",
                "message": f"{collection_name} 컬렉션 조회 실패: {response.get('message', '알 수 없는 오류')}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"{collection_name} 컬렉션 조회 중 오류: {str(e)}"
        }

def list_storage_files(prefix: str = "") -> dict:
    """
    Firebase Storage의 파일 목록을 조회합니다.
    
    Args:
        prefix: 파일 경로 접두사 (폴더 지정용)
        
    Returns:
        dict: 파일 목록
    """
    try:
        response = firebase_client.list_files(prefix=prefix)
        
        if response.get("success"):
            files = response.get("data", {}).get("files", [])
            
            formatted_list = f"📁 Firebase Storage 파일 목록 (prefix: '{prefix}'):\n"
            formatted_list += f"총 {len(files)}개의 파일이 있습니다.\n\n"
            
            for i, file_info in enumerate(files, 1):
                name = file_info.get("name", "Unknown")
                size = file_info.get("size", "Unknown")
                updated = file_info.get("updated", "Unknown")
                
                formatted_list += f"{i}. {name}\n"
                formatted_list += f"   크기: {size} bytes\n"
                formatted_list += f"   수정일: {updated}\n"
                formatted_list += f"   {'-' * 30}\n\n"
            
            return {
                "status": "success",
                "files": files,
                "formatted_list": formatted_list,
                "total_count": len(files),
                "message": f"Storage에서 {len(files)}개 파일을 조회했습니다."
            }
        else:
            return {
                "status": "error",
                "message": f"Storage 파일 목록 조회 실패: {response.get('message', '알 수 없는 오류')}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Storage 파일 목록 조회 중 오류: {str(e)}"
        }

# 5. 메인 인테리어 매니저 에이전트 (Root Agent)
root_agent = Agent(
    name="interior_manager",
    model="gemini-2.0-flash",
    description="인테리어 프로젝트의 현장관리, 원가계산, 결제를 통합 관리하는 매니저",
    instruction="""
    당신은 인테리어 프로젝트 전체를 관리하는 전문 매니저입니다.
    
    주요 기능:
    1. 현장 관리: 현장 등록, 정보 조회, 목록 관리
    2. 원가 계산: 자재비, 인건비 계산 및 총 원가 산출  
    3. 결제 관리: 결제 내역서 생성, 상태 관리, 목록 조회
    4. 프로젝트 현황: 전체 프로젝트 요약 및 통계
    5. 🔥 Firebase 연동: 온라인 데이터베이스와 스토리지 관리
    
    Firebase 기능:
    - "schedule 컬렉션을 조회해서" → query_schedule_collection() 사용
    - "컬렉션 목록을 보여줘" → list_firestore_collections() 사용
    - "프로젝트 정보 확인해줘" → get_firebase_project_info() 사용
    - "파일 목록을 보여줘" → list_storage_files() 사용
    - 특정 컬렉션 조회 → query_any_collection(collection_name) 사용
    
    사용자가 Firebase 관련 요청을 하면:
    1. 적절한 Firebase 도구를 사용하여 온라인 데이터를 조회
    2. 결과를 읽기 쉽게 포맷팅하여 제공
    3. 추가적인 분석이나 작업이 필요한지 확인
    
    작업 순서:
    1. 먼저 현장 정보를 등록해주세요
    2. 필요한 자재와 작업의 원가를 계산해주세요
    3. 최종적으로 결제 내역서를 생성해주세요
    4. Firebase에서 관련 데이터를 조회하거나 저장할 수 있습니다
    
    각 단계에서 관련 도구를 사용하여 전문 에이전트들과 협력하고,
    고객에게 진행 상황을 단계별로 자세히 설명해주세요.
    
    모든 금액은 원화(₩)로 표시하고, 천 단위마다 쉼표를 사용해주세요.
    """,
    tools=[
        # 현장 관리 도구
        register_site, 
        get_site_info, 
        list_all_sites,
        
        # 원가 계산 도구
        calculate_material_cost, 
        get_total_cost,
        estimate_labor_cost,
        
        # 결제 관리 도구
        create_payment_invoice, 
        get_payment_status,
        list_all_invoices,
        update_payment_status,
        
        # 프로젝트 현황 도구
        get_project_summary,
        
        # 🔥 Firebase 연동 도구
        query_schedule_collection,
        get_firebase_project_info,
        list_firestore_collections,
        query_any_collection,
        list_storage_files
    ]
) 