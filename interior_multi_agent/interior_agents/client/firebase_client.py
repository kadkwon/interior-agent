import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

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
        """
        Firebase Cloud Functions에 HTTP 요청을 보냅니다.
        
        Args:
            endpoint: API 엔드포인트 (예: '/firestoreQueryCollection')
            method: HTTP 메소드 ('GET', 'POST', 'PUT', 'DELETE')
            data: 요청 데이터 (POST/PUT의 경우)
            
        Returns:
            Dict: API 응답 데이터
        """
        url = f"{self.base_url}{endpoint}"
        
        # 요청 로깅
        print(f"🔥 Firebase 요청: {method} {url}")
        if data:
            print(f"📤 요청 데이터: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data if data else None, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data if data else {}, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data if data else {}, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, json=data if data else {}, timeout=30)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메소드: {method}")
            
            # 응답 로깅
            print(f"📥 응답 상태: {response.status_code}")
            print(f"📥 응답 헤더: {dict(response.headers)}")
            
            # HTTP 상태 코드 확인
            if response.status_code >= 400:
                error_text = response.text
                print(f"❌ HTTP 오류: {response.status_code} - {error_text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_text}",
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat()
                }
            
            # JSON 응답 파싱
            response_data = response.json()
            print(f"📥 응답 데이터: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            return response_data
            
        except requests.exceptions.Timeout as e:
            error_msg = f"요청 타임아웃: {str(e)}"
            print(f"⏰ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.ConnectionError as e:
            error_msg = f"연결 오류: {str(e)}"
            print(f"🔌 {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP 요청 실패: {str(e)}"
            print(f"🌐 {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            error_msg = f"JSON 파싱 실패: {str(e)}"
            print(f"📄 {error_msg}")
            print(f"📄 원본 응답: {response.text if 'response' in locals() else 'N/A'}")
            return {
                "success": False,
                "error": error_msg,
                "endpoint": endpoint,
                "raw_response": response.text if 'response' in locals() else None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"예상치 못한 오류: {str(e)}"
            print(f"💥 {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }
    
    # =================
    # 🔥 CORE APIs
    # =================
    
    def get_project_info(self) -> Dict[str, Any]:
        """Firebase 프로젝트 정보를 조회합니다."""
        return self._make_request('/firebaseGetProject', 'GET')
    
    def get_sdk_config(self) -> Dict[str, Any]:
        """Firebase SDK 설정을 조회합니다."""
        return self._make_request('/firebaseGetSdkConfig', 'GET')
    
    def list_apis(self) -> Dict[str, Any]:
        """사용 가능한 모든 API 목록을 조회합니다."""
        return self._make_request('/mcpListApis', 'GET')
    
    # =================
    # 👤 AUTH APIs
    # =================
    
    def get_user(self, uid: str = None, email: str = None, phone_number: str = None) -> Dict[str, Any]:
        """
        사용자 정보를 조회합니다.
        
        Args:
            uid: 사용자 UID
            email: 이메일 주소
            phone_number: 전화번호
        """
        data = {}
        if uid:
            data['uid'] = uid
        elif email:
            data['email'] = email
        elif phone_number:
            data['phoneNumber'] = phone_number
        else:
            return {
                "success": False,
                "error": "uid, email, 또는 phoneNumber 중 하나는 필수입니다."
            }
        
        return self._make_request('/authGetUser', 'POST', data)
    
    def list_users(self, max_results: int = 1000, page_token: str = None) -> Dict[str, Any]:
        """
        사용자 목록을 조회합니다.
        
        Args:
            max_results: 최대 결과 수
            page_token: 페이지 토큰
        """
        data = {"maxResults": max_results}
        if page_token:
            data["pageToken"] = page_token
        
        return self._make_request('/authListUsers', 'POST', data)
    
    # =================
    # 🗄️ FIRESTORE APIs
    # =================
    
    def get_document(self, collection_path: str, document_id: str) -> Dict[str, Any]:
        """
        MCP 호환: 단일 Firestore 문서를 조회합니다.
        
        Args:
            collection_path: 컬렉션 경로 (예: 'addressesJson', 'schedules')
            document_id: 문서 ID
            
        Returns:
            Dict: 문서 데이터 또는 오류 정보
        """
        data = {
            "collectionPath": collection_path,
            "documentId": document_id
        }
        return self._make_request('/firestoreGetDocument', 'POST', data)
    
    def list_documents(self, collection_path: str, limit: int = 10, 
                      order_by: str = "", order_direction: str = 'asc',
                      where: List = None, start_after: str = None, 
                      end_before: str = None, select: List = None, 
                      offset: int = 0) -> Dict[str, Any]:
        """
        MCP 호환: 고급 Firestore 문서 목록을 조회합니다.
        필터링, 정렬, 페이지네이션을 지원합니다.
        
        Args:
            collection_path: 컬렉션 경로 (예: 'addressesJson', 'schedules')
            limit: 조회할 문서 수 제한 (기본값: 10, 최대: 1000)
            order_by: 정렬 필드명
            order_direction: 정렬 방향 ('asc' 또는 'desc')
            where: WHERE 조건 배열 (예: [["field", "==", "value"]])
            start_after: 페이지네이션 시작 커서
            end_before: 페이지네이션 종료 커서
            select: 선택할 필드 배열
            offset: 오프셋 (비효율적이지만 호환성을 위해 지원)
            
        Returns:
            Dict: 문서 목록과 페이지네이션 정보
        """
        data = {
            "collectionPath": collection_path,
            "limit": limit,
            "offset": offset,
            "orderDirection": order_direction
        }
        
        if order_by:
            data["orderBy"] = order_by
            
        if where:
            data["where"] = where
            
        if start_after:
            data["startAfter"] = start_after
            
        if end_before:
            data["endBefore"] = end_before
            
        if select:
            data["select"] = select
        
        return self._make_request('/firestoreListDocuments', 'POST', data)

    def get_documents(self, paths: List[str]) -> Dict[str, Any]:
        """
        Firestore 문서들을 조회합니다. (기존 함수 - 여러 경로)
        
        Args:
            paths: 문서 경로 리스트 (예: ['users/user123', 'posts/post456'])
        """
        data = {"paths": paths}
        return self._make_request('/firestoreGetDocuments', 'POST', data)
    
    def list_collections(self) -> Dict[str, Any]:
        """Firestore 컬렉션 목록을 조회합니다."""
        return self._make_request('/firestoreListCollections', 'POST', {})
    
    def query_collection(self, collection_path: str, limit: int = 50, where_conditions: List[Dict] = None, order_by: str = "") -> Dict[str, Any]:
        """
        Firestore 컬렉션을 쿼리합니다.
        
        Args:
            collection_path: 컬렉션 경로 (예: 'schedule', 'users', 'projects/project123/tasks')
            limit: 결과 수 제한
            where_conditions: WHERE 조건 리스트
            order_by: 정렬 필드
        """
        data = {
            "collectionPath": collection_path,
            "limit": limit
        }
        
        if where_conditions:
            data["where"] = where_conditions
        
        if order_by:
            data["orderBy"] = order_by
        
        return self._make_request('/firestoreQueryCollection', 'POST', data)
    
    def add_document(self, collection_path: str, document_data: Dict[str, Any], document_id: str = None) -> Dict[str, Any]:
        """
        Firestore 컬렉션에 새 문서를 추가합니다.
        
        Args:
            collection_path: 컬렉션 경로 (예: 'addressesJson', 'schedules')
            document_data: 추가할 문서 데이터
            document_id: 문서 ID (없으면 자동 생성)
            
        Returns:
            Dict: 추가 결과
        """
        data = {
            "collectionPath": collection_path,
            "data": document_data
        }
        
        if document_id:
            data["documentId"] = document_id
        
        return self._make_request('/firestoreAddDocument', 'POST', data)
    
    def update_document(self, document_path: str, update_data: Dict[str, Any], merge: bool = True) -> Dict[str, Any]:
        """
        Firestore 문서를 업데이트합니다.
        
        Args:
            document_path: 문서 경로 (예: 'addressesJson/doc123')
            update_data: 업데이트할 데이터
            merge: 기존 데이터와 병합 여부
            
        Returns:
            Dict: 업데이트 결과
        """
        # document_path에서 collection과 document ID 분리
        path_parts = document_path.split('/')
        if len(path_parts) >= 2:
            collection_path = path_parts[0]
            document_id = path_parts[1]
        else:
            collection_path = document_path
            document_id = document_path
            
        data = {
            "collectionPath": collection_path,
            "documentId": document_id,
            "documentPath": document_path,
            "data": update_data,
            "merge": merge
        }
        
        return self._make_request('/firestoreUpdateDocument', 'POST', data)
    
    def delete_document(self, document_path: str) -> Dict[str, Any]:
        """
        Firestore 문서를 삭제합니다.
        
        Args:
            document_path: 문서 경로 (예: 'addressesJson/doc123')
            
        Returns:
            Dict: 삭제 결과
        """
        data = {"documentPath": document_path}
        return self._make_request('/firestoreDeleteDocument', 'POST', data)
    
    # =================
    # 📁 STORAGE APIs
    # =================
    
    def list_files(self, prefix: str = "") -> Dict[str, Any]:
        """
        Firebase Storage 파일 목록을 조회합니다.
        
        Args:
            prefix: 파일 경로 접두사
        """
        data = {"prefix": prefix}
        return self._make_request('/storageListFiles', 'POST', data)
    
    def get_download_url(self, file_path: str) -> Dict[str, Any]:
        """
        Firebase Storage 파일의 다운로드 URL을 조회합니다.
        
        Args:
            file_path: 파일 경로
        """
        data = {"filePath": file_path}
        return self._make_request('/storageGetDownloadUrl', 'POST', data)
    
    def smart_search(self, search_query: str, collection_path: str = None,
                    search_fields: List[str] = None, search_type: str = 'fuzzy',
                    threshold: float = 0.3, sort_by: str = 'score',
                    sort_field: str = '', sort_direction: str = 'desc',
                    limit: int = 20) -> Dict[str, Any]:
        """
        범용 스마트 검색 API를 호출합니다.
        
        Args:
            search_query: 검색어 (필수)
            collection_path: 검색할 특정 컬렉션 (선택)
            search_fields: 검색할 필드 목록 (선택)
            search_type: 검색 방식 (fuzzy/exact/regex)
            threshold: 유사도 임계값 (0.0~1.0)
            sort_by: 정렬 기준 (score/field)
            sort_field: 정렬 기준 필드명
            sort_direction: 정렬 방향 (asc/desc)
            limit: 검색 결과 제한
            
        Returns:
            Dict: 검색 결과와 메타데이터
        """
        data = {
            "searchQuery": search_query,
            "limit": limit,
            "searchType": search_type,
            "threshold": threshold,
            "sortBy": sort_by,
            "sortDirection": sort_direction
        }
        
        if collection_path:
            data["collectionPath"] = collection_path
        if search_fields:
            data["searchFields"] = search_fields
        if sort_field:
            data["sortField"] = sort_field
        
        return self._make_request('/smartSearch', 'POST', data)
    
    # =================
    # 📄 기타 APIs
    # =================
    
    def send_estimate_pdf(self, recipient_email: str, pdf_data: str, project_info: Dict = None) -> Dict[str, Any]:
        """
        견적서 PDF를 전송합니다.
        
        Args:
            recipient_email: 받는 사람 이메일
            pdf_data: PDF 데이터 (base64 인코딩)
            project_info: 프로젝트 정보
        """
        data = {
            "recipientEmail": recipient_email,
            "pdfData": pdf_data
        }
        
        if project_info:
            data["projectInfo"] = project_info
        
        return self._make_request('/sendEstimatePdfHttp', 'POST', data)

class ScheduleFormatter:
    """Schedule 데이터 포맷팅 클래스"""
    
    @staticmethod
    def format_schedule_data(firestore_response: Dict[str, Any]) -> str:
        """
        Firestore 응답을 읽기 쉬운 형태로 포맷팅합니다.
        
        Args:
            firestore_response: Firestore API 응답
            
        Returns:
            str: 포맷팅된 문자열
        """
        if not firestore_response.get("success", False):
            return f"❌ 조회 실패: {firestore_response.get('message', '알 수 없는 오류')}"
        
        documents = firestore_response.get("data", {}).get("documents", [])
        
        if not documents:
            return "📅 등록된 일정이 없습니다."
        
        formatted_text = f"📅 Schedule 컬렉션 조회 결과:\n총 {len(documents)}개의 일정이 있습니다.\n\n"
        
        for i, doc in enumerate(documents, 1):
            # 문서 데이터 추출
            doc_data = doc.get("data", {})
            doc_id = doc.get("id", "Unknown ID")
            
            # 기본 필드들 추출
            title = doc_data.get('title', '제목 없음')
            date = doc_data.get('date', '날짜 없음')
            status = doc_data.get('status', '상태 없음')
            description = doc_data.get('description', '설명 없음')
            assignee = doc_data.get('assignee', '담당자 없음')
            site_id = doc_data.get('site_id', '현장ID 없음')
            
            formatted_text += f"{i}. {title}\n"
            formatted_text += f"   📅 날짜: {date}\n"
            formatted_text += f"   📊 상태: {status}\n"
            formatted_text += f"   👤 담당자: {assignee}\n"
            formatted_text += f"   🏢 현장ID: {site_id}\n"
            formatted_text += f"   📝 설명: {description}\n"
            formatted_text += f"   🆔 문서ID: {doc_id}\n"
            formatted_text += f"   {'-' * 40}\n\n"
        
        return formatted_text

# 전역 클라이언트 인스턴스
firebase_client = FirebaseCloudFunctionsClient()
schedule_formatter = ScheduleFormatter() 