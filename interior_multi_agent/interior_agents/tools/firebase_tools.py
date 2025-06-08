# Firebase 클라이언트 import
try:
    from ..client.firebase_client import firebase_client, schedule_formatter
    FIREBASE_AVAILABLE = True
except ImportError:
    # Firebase 클라이언트가 없을 경우 더미 객체 생성
    class DummyFirebaseClient:
        def query_collection(self, *args, **kwargs):
            return {"success": False, "error": "Firebase client를 사용할 수 없습니다."}
        def get_project_info(self):
            return {"success": False, "error": "Firebase client를 사용할 수 없습니다."}
        def list_collections(self):
            return {"success": False, "error": "Firebase client를 사용할 수 없습니다."}
        def list_files(self, *args, **kwargs):
            return {"success": False, "error": "Firebase client를 사용할 수 없습니다."}
    
    class DummyScheduleFormatter:
        def format_schedule_data(self, data):
            return "Firebase 연결이 필요합니다."
    
    firebase_client = DummyFirebaseClient()
    schedule_formatter = DummyScheduleFormatter()
    FIREBASE_AVAILABLE = False

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