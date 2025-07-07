"""
🎨 Firebase 응답 포맷팅 전용 도구 - 영어 필드명을 한글로 변환

✨ 이 모듈은 순수 함수로 구성되어 다른 에이전트들이 공통으로 사용할 수 있습니다.

📋 주소 데이터베이스 구조:
- description: "수성 효성 헤링턴 105동 1503호" (실제 주소 정보)
- dataJson: JSON 문자열 형태의 상세 정보
  {
    "date": "",
    "firstFloorPassword": "1503#1234",
    "unitPassword": "1234", 
    "supervisorName": "",
    "contractAmount": "",
    "contractDate": "",
    "phoneLastFourDigits": "",
    "email": "",
    "isCompleted": true,
    "createdAt": "2024-12-24T02:49:35.432Z",
    "siteNumber": 15
  }
"""

import json
from typing import Dict, Any

def format_korean_response(result: Dict[str, Any], operation_type: str, search_term: str = None) -> str:
    """MCP 응답을 한글로 가독성 좋게 포맷팅 - instruction 기반 로직"""
    print(f"🎨 [FORMAT] 포맷팅 시작: operation_type={operation_type}")
    print(f"🎨 [FORMAT] 원본 데이터: {str(result)[:200]}...")
    
    try:
        # 에러 처리
        if "error" in result:
            return f"❌ 오류 발생: {result['error']}"
        
        # MCP 응답에서 실제 데이터 추출
        actual_data = None
        if "content" in result and result["content"]:
            content_item = result["content"][0]
            if "text" in content_item:
                try:
                    actual_data = json.loads(content_item["text"])
                except json.JSONDecodeError:
                    return f"❌ JSON 파싱 오류: {content_item['text'][:100]}..."
        
        if not actual_data:
            return f"❌ 응답 데이터가 없습니다: {str(result)[:100]}..."
        
        # instruction 기반 포맷팅 로직
        return _format_by_instruction(actual_data, operation_type, search_term)
        
    except Exception as e:
        print(f"🎨 [FORMAT] 오류 발생: {str(e)}")
        return f"❌ 응답 처리 중 오류 발생: {str(e)}"

def _format_by_instruction(data: Dict[str, Any], operation_type: str, search_term: str = None) -> str:
    """instruction 기반 포맷팅 로직"""
    
    # 영어→한글 필드명 매핑
    field_mapping = {
        'createdAt': '📅 생성일',
        'updatedAt': '📅 수정일',
        'address': '📍 주소',
        'buildingName': '🏢 건물명',
        'description': '📝 설명',
        'name': '📛 이름',
        'title': '📛 제목',
        'phoneNumber': '📞 전화번호',
        'phone': '📞 전화번호',
        'email': '📧 이메일',
        'managerName': '👤 담당자',
        'versionName': '📋 버전명',
        'totalAmount': '💰 총액',
        'unitPassword': '🔑 세대비밀번호',
        'firstFloorPassword': '🗝️ 1층비밀번호',
        'memo': '📝 메모',
        'note': '📝 노트',
        'status': '⚡ 상태',
        'type': '🏷️ 유형',
        'category': '🏷️ 분류',
        'id': '🆔 ID',
        'data': '📊 데이터',
        'buildingType': '🏢 건물유형',
        'date': '📅 등록일'
    }
    
    if operation_type == "list_collections":
        collections = data.get("collections", [])
        if not collections:
            return "📂 사용 가능한 컬렉션이 없습니다."
        
        formatted = "📂 사용 가능한 컬렉션 목록:\n"
        for collection in collections:
            collection_id = collection.get("id", collection) if isinstance(collection, dict) else collection
            formatted += f"   {collection_id}\n"
        return formatted
    
    elif operation_type == "list_documents":
        documents = data.get("documents", [])
        if not documents:
            return "📄 해당 컬렉션에 문서가 없습니다."
        
        formatted = f"📄 문서 목록 ({len(documents)}개):\n\n"
        for doc in documents:
            doc_id = doc.get("id", "ID없음")
            description = doc.get("data", {}).get("description", "설명없음")
            formatted += f"{doc_id} - {description}\n"
        return formatted
    
    elif operation_type == "get_document":
        # 문서 상세 조회
        if not data or "id" not in data:
            return "📄 해당 문서를 찾을 수 없습니다."
        
        doc_id = data.get("id", "ID 없음")
        formatted = f"🔍 {doc_id} 상세 정보:\n\n"
        
        # data 필드 내에서 우선순위 필드 먼저 표시
        data_info = data.get("data", {})
        priority_fields = ['address', 'buildingName', 'description', 'name', 'title', 
                          'managerName', 'phoneNumber', 'phone', 'email', 'versionName', 
                          'createdAt', 'updatedAt', 'status', 'type', 'category']
        
        for field in priority_fields:
            if field in data_info and data_info[field]:
                korean_name = field_mapping.get(field, field)
                value = data_info[field]
                
                # 날짜 형식 정리 (T 제거)
                if field in ['createdAt', 'updatedAt'] and isinstance(value, str):
                    if 'T' in value:
                        value = value.split('T')[0]
                
                formatted += f"{korean_name}: {value}\n"
        
        # 우선순위 필드 이후 남은 필드 중 JSON 문자열 자동 탐지
        for field_name, field_value in data_info.items():
            if field_name in priority_fields:
                continue
                
            if isinstance(field_value, str) and field_value.strip():
                trimmed_value = field_value.strip()
                if (trimmed_value.startswith('{') and trimmed_value.endswith('}')) or \
                   (trimmed_value.startswith('[') and trimmed_value.endswith(']')):
                    try:
                        json_data = json.loads(trimmed_value)
                        korean_field = field_mapping.get(field_name, field_name)
                        formatted += f"\n📋 {korean_field} 내용:\n"
                        formatted += _format_json_recursively(json_data, field_mapping)
                    except json.JSONDecodeError:
                        pass
        
        return formatted
    
    elif operation_type == "query_collection_group":
        documents = data.get("documents", [])
        if not documents:
            return "🔍 검색 결과가 없습니다."
        
        # 검색어가 있으면 필터링
        if search_term:
            filtered_docs = []
            search_lower = search_term.lower()
            
            for doc in documents:
                doc_data = doc.get("data", {})
                description = doc_data.get("description", "")
                data_json = doc_data.get("dataJson", "")
                
                # description 또는 dataJson에서 검색어 찾기
                if (search_lower in description.lower()) or (search_lower in data_json.lower()):
                    filtered_docs.append(doc)
            
            documents = filtered_docs
        
        if not documents:
            return f"🔍 '{search_term}' 검색 결과가 없습니다." if search_term else "🔍 검색 결과가 없습니다."
        
        formatted = f"🔍 {'검색' if search_term else '조회'} 결과 ({len(documents)}개):\n\n"
        for doc in documents:
            doc_id = doc.get("id", "ID없음")
            doc_data = doc.get("data", {})
            description = doc_data.get("description", "설명없음")
            formatted += f"{doc_id} - {description}\n"
        return formatted
    
    elif operation_type == "add_document":
        return "✅ 문서가 성공적으로 추가되었습니다."
    elif operation_type == "update_document":
        return "✅ 문서가 성공적으로 수정되었습니다."
    elif operation_type == "delete_document":
        return "✅ 문서가 성공적으로 삭제되었습니다."
    else:
        return "✅ 작업이 완료되었습니다."

def _format_json_recursively(data, field_mapping):
    """JSON 데이터를 재귀적으로 한글화해서 포맷팅"""
    formatted = ""
    
    if isinstance(data, list):
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                formatted += f"\n{i}번째 항목:\n"
                for key, value in item.items():
                    if value:
                        korean_key = field_mapping.get(key, key)
                        formatted += f"  {korean_key}: {value}\n"
            else:
                formatted += f"  {item}\n"
    
    elif isinstance(data, dict):
        for key, value in data.items():
            if value:
                korean_key = field_mapping.get(key, key)
                if isinstance(value, (dict, list)):
                    formatted += f"\n{korean_key}:\n"
                    formatted += _format_json_recursively(value, field_mapping)
                else:
                    formatted += f"  {korean_key}: {value}\n"
    
    return formatted

# 모듈 초기화 로깅
print(f"✅ 포맷팅 도구 초기화 완료")
print(f"🎨 Firebase 응답 → 한글 포맷팅 전담")
print(f"📝 영어 필드명 → 한글 변환 기능") 