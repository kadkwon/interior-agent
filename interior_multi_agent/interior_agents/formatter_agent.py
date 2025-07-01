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
            
            formatted = "📂 **사용 가능한 컬렉션 목록:**\n"
            for i, collection in enumerate(collections, 1):
                collection_id = collection.get("id", collection) if isinstance(collection, dict) else collection
                formatted += f"   {i}. {collection_id}\n"
            return formatted
        
        elif operation_type == "list_documents":
            documents = actual_data.get("documents", [])
            print(f"🎨 [FORMAT] documents 개수: {len(documents) if documents else 0}")
            
            if not documents:
                return "📄 해당 컬렉션에 문서가 없습니다."
            
            formatted = f"📄 **문서 목록 ({len(documents)}개):**\n\n"
            print(f"🎨 [FORMAT] 포맷팅 시작 - 문서 {len(documents)}개")
            for i, doc in enumerate(documents, 1):
                doc_id = doc.get("id", "ID 없음")
                description = doc.get("data", {}).get("description", "설명 없음")
                
                formatted += f"**{i}. {description}**\n"
                
                # dataJson 파싱
                data_json = doc.get("data", {}).get("dataJson")
                if data_json:
                    try:
                        data = json.loads(data_json)
                        if "firstFloorPassword" in data:
                            formatted += f"   🔑 1층 비밀번호: {data['firstFloorPassword']}\n"
                        if "unitPassword" in data:
                            formatted += f"   🏠 호별 비밀번호: {data['unitPassword']}\n"
                        if "managerName" in data:
                            formatted += f"   👤 관리소장: {data['managerName']}\n"
                        if "phoneNumber" in data:
                            formatted += f"   📞 연락처: {data['phoneNumber']}\n"
                    except:
                        pass
                formatted += "\n"
            
            print(f"🎨 [FORMAT] 최종 결과 길이: {len(formatted)}")
            print(f"🎨 [FORMAT] 최종 결과 미리보기: {formatted[:100]}...")
            return formatted
        
        elif operation_type == "get_document":
            # actual_data 자체가 문서 데이터임
            doc = actual_data
            if not doc or "id" not in doc:
                return "📄 해당 문서를 찾을 수 없습니다."
            
            doc_id = doc.get("id", "ID 없음")
            description = doc.get("data", {}).get("description", "설명 없음")
            
            formatted = f"🔍 **{description} 상세 정보:**\n\n"
            formatted += f"📄 **설명:** {description}\n\n"
            
            # dataJson 상세 파싱
            data_json = doc.get("data", {}).get("dataJson")
            if data_json:
                try:
                    data = json.loads(data_json)
                    formatted += "🏠 **상세 정보:**\n"
                    
                    if "firstFloorPassword" in data:
                        formatted += f"   🔑 1층 비밀번호: {data['firstFloorPassword']}\n"
                    if "unitPassword" in data:
                        formatted += f"   🏠 호별 비밀번호: {data['unitPassword']}\n"
                    if "managerName" in data:
                        formatted += f"   👤 관리소장: {data['managerName']}\n"
                    if "phoneNumber" in data:
                        formatted += f"   📞 연락처: {data['phoneNumber']}\n"
                    if "address" in data:
                        formatted += f"   📍 주소: {data['address']}\n"
                    if "buildingType" in data:
                        formatted += f"   🏢 건물 유형: {data['buildingType']}\n"
                    if "date" in data and data["date"]:
                        formatted += f"   📅 등록일: {data['date']}\n"
                    
                    # 기타 정보들
                    for key, value in data.items():
                        if key not in ["firstFloorPassword", "unitPassword", "managerName", "phoneNumber", "address", "buildingType", "date"] and value:
                            formatted += f"   📋 {key}: {value}\n"
                            
                except Exception as e:
                    formatted += f"   ⚠️ 상세 정보 파싱 중 오류: {str(e)}\n"
            
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