# ADK Root Agent - Interior Multi-Agent 시스템
# Firebase Cloud Functions 연동 버전 (통합)

from google.adk.agents import Agent
import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

# =================================================================================
# 🔥 FIREBASE CLOUD FUNCTIONS CLIENT
# =================================================================================

class FirebaseCloudFunctionsClient:
    """Firebase Cloud Functions HTTP API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://us-central1-interior-one-click.cloudfunctions.net"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict[str, Any]:
        """Firebase Cloud Functions에 HTTP 요청을 보냅니다."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data if data else None)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data if data else {})
            else:
                raise ValueError(f"지원하지 않는 HTTP 메소드: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"HTTP 요청 실패: {str(e)}",
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON 파싱 실패: {str(e)}",
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_project_info(self) -> Dict[str, Any]:
        """Firebase 프로젝트 정보를 조회합니다."""
        return self._make_request('/firebaseGetProject', 'GET')
    
    def list_collections(self) -> Dict[str, Any]:
        """Firestore 컬렉션 목록을 조회합니다."""
        return self._make_request('/firestoreListCollections', 'POST', {})
    
    def query_collection(self, collection_path: str, limit: int = 50) -> Dict[str, Any]:
        """Firestore 컬렉션을 쿼리합니다."""
        data = {"collection": collection_path, "limit": limit}
        return self._make_request('/firestoreQueryCollection', 'POST', data)
    
    def list_files(self, prefix: str = "") -> Dict[str, Any]:
        """Firebase Storage 파일 목록을 조회합니다."""
        data = {"prefix": prefix}
        return self._make_request('/storageListFiles', 'POST', data)

# 전역 클라이언트 인스턴스
firebase_client = FirebaseCloudFunctionsClient()

# =================================================================================
# 📋 DATA STORAGE
# =================================================================================

project_data = {
    "sites": {},
    "costs": {},
    "payments": {}
}

# =================================================================================
# 🏢 SITE MANAGEMENT FUNCTIONS
# =================================================================================

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
        return {"status": "success", "site_info": project_data["sites"][site_id]}
    else:
        return {"status": "error", "message": f"현장 {site_id}를 찾을 수 없습니다."}

def list_all_sites() -> dict:
    """등록된 모든 현장 목록을 조회합니다."""
    return {
        "status": "success",
        "sites": project_data["sites"],
        "total_count": len(project_data["sites"])
    }

# =================================================================================
# 💰 COST CALCULATION FUNCTIONS
# =================================================================================

def calculate_material_cost(site_id: str, material_type: str, quantity: float) -> dict:
    """자재 원가를 계산합니다."""
    material_prices = {
        "paint": 15000, "tile": 30000, "wallpaper": 20000, 
        "flooring": 50000, "lighting": 100000, "cabinet": 200000
    }
    
    if material_type not in material_prices:
        return {
            "status": "error", 
            "message": f"지원하지 않는 자재 종류: {material_type}"
        }
    
    unit_price = material_prices[material_type]
    total_cost = unit_price * quantity
    
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
        "message": f"{material_type} {quantity}㎡의 원가: {total_cost:,}원"
    }

def get_total_cost(site_id: str) -> dict:
    """현장의 총 원가를 계산합니다."""
    if site_id not in project_data["costs"]:
        return {"status": "error", "message": f"현장 {site_id}의 원가 데이터가 없습니다."}
    
    total = sum(cost_info["total_cost"] for cost_info in project_data["costs"][site_id].values())
    details = [
        {
            "material": material,
            "quantity": cost_info["quantity"],
            "unit_price": cost_info["unit_price"],
            "cost": cost_info["total_cost"]
        }
        for material, cost_info in project_data["costs"][site_id].items()
    ]
    
    return {
        "status": "success",
        "site_id": site_id,
        "total_cost": total,
        "cost_breakdown": details,
        "message": f"현장 {site_id}의 총 원가: {total:,}원"
    }

# =================================================================================
# 💳 PAYMENT MANAGEMENT FUNCTIONS
# =================================================================================

def create_payment_invoice(site_id: str, description: str) -> dict:
    """결제 내역서를 생성합니다."""
    invoice_id = f"INV-{site_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    if site_id not in project_data["costs"]:
        return {"status": "error", "message": f"현장 {site_id}의 원가 데이터가 없습니다."}
    
    total_amount = sum(cost_info["total_cost"] for cost_info in project_data["costs"][site_id].values())
    
    project_data["payments"][invoice_id] = {
        "site_id": site_id,
        "description": description,
        "total_amount": total_amount,
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return {
        "status": "success",
        "invoice_id": invoice_id,
        "total_amount": total_amount,
        "message": f"결제 내역서 생성: {invoice_id}, 총 금액: {total_amount:,}원"
    }

def get_project_summary() -> dict:
    """전체 프로젝트 현황을 요약합니다."""
    total_sites = len(project_data["sites"])
    total_invoices = len(project_data["payments"])
    
    return {
        "status": "success",
        "summary": {
            "total_sites": total_sites,
            "total_invoices": total_invoices,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "message": f"현재 총 {total_sites}개 현장, {total_invoices}개 내역서"
    }

# =================================================================================
# 🔥 FIREBASE INTEGRATION FUNCTIONS
# =================================================================================

def query_schedule_collection(limit: int = 50) -> dict:
    """Schedule 컬렉션을 조회합니다."""
    try:
        response = firebase_client.query_collection("schedules", limit=limit)
        
        if response.get('success'):
            documents = response.get('data', {}).get('documents', [])
            
            formatted_result = f"📅 Schedule 컬렉션 조회 결과:\n총 {len(documents)}개의 일정\n\n"
            
            for i, doc in enumerate(documents, 1):
                doc_data = doc.get("data", {})
                title = doc_data.get('title', '제목 없음')
                date = doc_data.get('date', '날짜 없음')
                status = doc_data.get('status', '상태 없음')
                
                formatted_result += f"{i}. {title}\n"
                formatted_result += f"   📅 날짜: {date}\n"
                formatted_result += f"   📊 상태: {status}\n\n"
                
            return {
                'status': 'success',
                'message': f"schedule 컬렉션에서 {len(documents)}개 조회",
                'formatted_result': formatted_result
            }
        else:
            error_msg = response.get('error', '알 수 없는 오류')
            return {
                'status': 'error',
                'message': f"조회 실패: {error_msg}",
                'formatted_result': f"❌ 조회 실패: {error_msg}"
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'message': f"오류: {str(e)}",
            'formatted_result': f"❌ 오류: {str(e)}"
        }

def get_firebase_project_info() -> dict:
    """Firebase 프로젝트 정보를 조회합니다."""
    try:
        response = firebase_client.get_project_info()
        
        if response.get("success"):
            project_info = response.get("data", {})
            project_id = project_info.get("projectId", "Unknown")
            
            return {
                "status": "success",
                "project_info": project_info,
                "message": f"프로젝트 '{project_id}'에 연결됨"
            }
        else:
            return {
                "status": "error",
                "message": f"조회 실패: {response.get('error', '알 수 없는 오류')}"
            }
    except Exception as e:
        return {"status": "error", "message": f"오류: {str(e)}"}

def list_firestore_collections() -> dict:
    """Firestore 컬렉션 목록을 조회합니다."""
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
                "message": f"총 {len(collections)}개 컬렉션"
            }
        else:
            return {
                "status": "error",
                "message": f"조회 실패: {response.get('error', '알 수 없는 오류')}"
            }
    except Exception as e:
        return {"status": "error", "message": f"오류: {str(e)}"}

def query_any_collection(collection_name: str, limit: int = 50) -> dict:
    """지정된 Firestore 컬렉션을 조회합니다."""
    try:
        response = firebase_client.query_collection(collection_name, limit=limit)
        
        if response.get("success"):
            documents = response.get("data", {}).get("documents", [])
            
            formatted_result = f"📋 {collection_name} 컬렉션:\n총 {len(documents)}개 문서\n\n"
            
            for i, doc in enumerate(documents, 1):
                doc_data = doc.get("data", {})
                doc_id = doc.get("id", "Unknown ID")
                
                formatted_result += f"{i}. 문서 ID: {doc_id}\n"
                
                for key, value in doc_data.items():
                    if key in ['title', 'name', 'date', 'status', 'description']:
                        formatted_result += f"   {key}: {value}\n"
                
                formatted_result += f"   {'-' * 30}\n\n"
            
            return {
                "status": "success",
                "formatted_result": formatted_result,
                "message": f"{collection_name}에서 {len(documents)}개 문서 조회"
            }
        else:
            return {
                "status": "error",
                "message": f"조회 실패: {response.get('error', '알 수 없는 오류')}"
            }
    except Exception as e:
        return {"status": "error", "message": f"오류: {str(e)}"}

def list_storage_files(prefix: str = "") -> dict:
    """Firebase Storage의 파일 목록을 조회합니다."""
    try:
        response = firebase_client.list_files(prefix=prefix)
        
        if response.get("success"):
            files = response.get("data", {}).get("files", [])
            
            formatted_list = f"📁 Storage 파일 목록:\n총 {len(files)}개 파일\n\n"
            
            for i, file_info in enumerate(files[:10], 1):  # 상위 10개만 표시
                name = file_info.get("name", "Unknown")
                size = file_info.get("size", "Unknown")
                
                formatted_list += f"{i}. {name}\n"
                formatted_list += f"   크기: {size} bytes\n\n"
            
            return {
                "status": "success",
                "files": files,
                "formatted_list": formatted_list,
                "message": f"Storage에서 {len(files)}개 파일 조회"
            }
        else:
            return {
                "status": "error",
                "message": f"조회 실패: {response.get('error', '알 수 없는 오류')}"
            }
    except Exception as e:
        return {"status": "error", "message": f"오류: {str(e)}"}

# =================================================================================
# 🤖 ROOT AGENT
# =================================================================================

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
    - "schedules 컬렉션을 조회해서" → query_schedule_collection() 사용
    - "컬렉션 목록을 보여줘" → list_firestore_collections() 사용
    - "프로젝트 정보 확인해줘" → get_firebase_project_info() 사용
    - "파일 목록을 보여줘" → list_storage_files() 사용
    - 특정 컬렉션 조회 → query_any_collection(collection_name) 사용
    
    사용자가 Firebase 관련 요청을 하면:
    1. 적절한 Firebase 도구를 사용하여 온라인 데이터를 조회
    2. 결과를 읽기 쉽게 포맷팅하여 제공
    3. 추가적인 분석이나 작업이 필요한지 확인
    
    모든 금액은 원화(₩)로 표시하고, 천 단위마다 쉼표를 사용해주세요.
    """,
    tools=[
        # 현장 관리 도구
        register_site, get_site_info, list_all_sites,
        
        # 원가 계산 도구
        calculate_material_cost, get_total_cost,
        
        # 결제 관리 도구
        create_payment_invoice, get_project_summary,
        
        # 🔥 Firebase 연동 도구
        query_schedule_collection, get_firebase_project_info,
        list_firestore_collections, query_any_collection, list_storage_files
    ]
)

# ADK가 인식하는 root_agent를 export
__all__ = ['root_agent'] 