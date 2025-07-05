"""
🎨 Firebase 응답 포맷팅 전용 에이전트 - 영어 필드명을 한글로 변환
"""

import json
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

def format_korean_response(result: Dict[str, Any], operation_type: str) -> str:
    """MCP 응답을 한글로 가독성 좋게 포맷팅"""
    print(f"🎨 [FORMAT] 포맷팅 시작: operation_type={operation_type}")
    print(f"🎨 [FORMAT] 원본 데이터: {str(result)[:200]}...")
    
    try:
        if "error" in result:
            return f"❌ 오류 발생: {result['error']}"
        
        # MCP 응답에서 실제 데이터 추출
        actual_data = None
        if "content" in result and result["content"]:
            content_item = result["content"][0]
            if "text" in content_item:
                try:
                    actual_data = json.loads(content_item["text"])
                except:
                    return f"❌ JSON 파싱 오류: {content_item['text'][:100]}..."
        
        if not actual_data:
            return f"❌ 응답 데이터가 없습니다: {str(result)[:100]}..."
        
        if operation_type == "list_collections":
            collections = actual_data.get("collections", [])
            if not collections:
                return "📂 사용 가능한 컬렉션이 없습니다."
            
            formatted = "📂 사용 가능한 컬렉션 목록:\n"
            for i, collection in enumerate(collections, 1):
                collection_id = collection.get("id", collection) if isinstance(collection, dict) else collection
                formatted += f"   {collection_id}\n"
            return formatted
        
        elif operation_type == "list_documents":
            documents = actual_data.get("documents", [])
            print(f"🎨 [FORMAT] documents 개수: {len(documents) if documents else 0}")
            
            if not documents:
                return "📄 해당 컬렉션에 문서가 없습니다."
            
            formatted = f"📄 문서 목록 ({len(documents)}개):\n\n"
            print(f"🎨 [FORMAT] 포맷팅 시작 - 문서 {len(documents)}개")
            
            for i, doc in enumerate(documents, 1):
                print(f"🔍 [DEBUG] 문서 {i} 구조 분석 시작")
                
                doc_id = doc.get("id", f"문서_{i}")
                formatted += f"{doc_id}\n"
            
            print(f"🎨 [FORMAT] 최종 결과 길이: {len(formatted)}")
            return formatted
        
        elif operation_type == "get_document":
            # 🔍 문서 조회: 필드명 한글화해서 상세 표시
            doc = actual_data
            if not doc or "id" not in doc:
                return "📄 해당 문서를 찾을 수 없습니다."
            
            doc_id = doc.get("id", "ID 없음")
            formatted = f"🔍 {doc_id} 상세 정보:\n\n"
            
            # 필드명 한글화 매핑
            field_mapping = {
                'createdAt': '생성일',
                'updatedAt': '수정일',
                'address': '주소',
                'buildingName': '건물명',
                'description': '설명',
                'name': '이름',
                'title': '제목',
                'phoneNumber': '전화번호',
                'phone': '전화번호',
                'email': '이메일',
                'managerName': '담당자',
                'versionName': '버전명',
                'totalAmount': '총액',
                'unitPassword': '세대비밀번호',
                'firstFloorPassword': '1층비밀번호',
                'memo': '메모',
                'note': '노트',
                'status': '상태',
                'type': '유형',
                'category': '분류',
                'id': 'ID',
                'data': '데이터'
            }
            
            # 기본 정보 표시 (한글화)
            data_info = doc.get("data", {})
            
            # 중요한 필드들 우선 표시
            priority_fields = ['address', 'buildingName', 'description', 'name', 'title', 
                             'managerName', 'phoneNumber', 'phone', 'email', 'versionName', 
                             'createdAt', 'updatedAt', 'status', 'type', 'category']
            
            for field in priority_fields:
                if field in data_info and data_info[field]:
                    korean_name = field_mapping.get(field, field)
                    value = data_info[field]
                    
                    # 날짜 형식 정리
                    if field in ['createdAt', 'updatedAt'] and isinstance(value, str):
                        if 'T' in value:
                            value = value.split('T')[0]
                    
                    formatted += f"{korean_name}: {value}\n"
            
            # JSON 필드 자동 탐지 및 파싱
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
                            formatted += _format_json_data(json_data, field_mapping)
                        except:
                            pass
            
            return formatted
        
        elif operation_type in ["add_document", "update_document", "delete_document"]:
            if operation_type == "add_document":
                return "✅ 문서가 성공적으로 추가되었습니다."
            elif operation_type == "update_document":
                return "✅ 문서가 성공적으로 수정되었습니다."
            else:
                return "✅ 문서가 성공적으로 삭제되었습니다."
        
        print(f"🎨 [FORMAT] 기본 응답 반환: operation_type={operation_type}")
        return "✅ 작업이 완료되었습니다."
        
    except Exception as e:
        print(f"🎨 [FORMAT] 오류 발생: {str(e)}")
        return f"❌ 응답 처리 중 오류 발생: {str(e)}"

def _format_json_data(data, field_mapping):
    """JSON 데이터를 한글화해서 포맷팅"""
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
                    formatted += _format_json_data(value, field_mapping)
                else:
                    formatted += f"  {korean_key}: {value}\n"
    
    return formatted

async def format_response(result: Dict[str, Any], operation_type: str) -> str:
    """포맷팅 전용 함수 - 에이전트 도구로 사용"""
    return format_korean_response(result, operation_type)

# 포맷팅 전용 에이전트
formatter_agent = LlmAgent(
    model='gemini-2.5-flash-lite-preview-06-17',
    name='response_formatter',
    instruction='''
🎨 Firebase 응답 포맷팅 전문가입니다!

## 핵심 기능:
- Firebase에서 받은 영어 필드명을 한글로 변환
- JSON 응답을 가독성 좋게 포맷팅
- 이모지와 함께 사용자 친화적인 응답 생성

## 영어→한글 필드명 매핑:
- firstFloorPassword → 🔑 1층 비밀번호
- unitPassword → 🏠 호별 비밀번호  
- managerName → 👤 관리소장
- phoneNumber → 📞 연락처
- address → 📍 주소
- buildingType → 🏢 건물 유형
- date → 📅 등록일

## 작업 방식:
1. 원본 Firebase 응답 분석
2. 영어 필드명을 한글로 변환
3. 이모지와 함께 가독성 좋은 형태로 포맷팅
4. 사용자에게 친화적인 한글 응답 생성
    ''',
    tools=[
        FunctionTool(format_response)
    ]
)

print(f"✅ 포맷팅 에이전트 초기화 완료")
print(f"🎨 Firebase 응답 → 한글 포맷팅 전담")
print(f"📝 영어 필드명 → 한글 변환 기능") 