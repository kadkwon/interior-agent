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
                # 🔍 디버깅: 실제 문서 구조 확인
                print(f"🔍 [DEBUG] 문서 {i} 구조: {doc}")
                
                doc_id = doc.get("id", "ID 없음")
                description = doc.get("data", {}).get("description", "")
                
                # 🔍 description이 없다면 문서 ID를 그대로 사용
                if not description:
                    # 우선순위 1: 문서 ID 그대로 사용 (정확한 매칭을 위해)
                    description = doc_id
                    print(f"🔍 [DEBUG] 문서 ID 그대로 사용: {description}")
                    
                    # 만약 문서 ID가 의미 없는 값이라면 다른 필드에서 찾기
                    if not description or description == "ID 없음" or len(description) < 3:
                        # dataJson에서 찾기
                        data_json = doc.get("data", {}).get("dataJson")
                        if data_json:
                            try:
                                data = json.loads(data_json)
                                # 여러 필드를 시도해서 가장 적절한 문서명 찾기
                                description = (
                                    data.get("description") or 
                                    data.get("address") or
                                    data.get("name") or 
                                    data.get("title") or 
                                    data.get("buildingName") or
                                    f"문서 #{i}"
                                )
                                print(f"🔍 [DEBUG] dataJson에서 찾은 문서명: {description}")
                            except Exception as e:
                                print(f"🔍 [DEBUG] dataJson 파싱 오류: {e}")
                                description = f"문서 #{i}"
                
                if not description:
                    description = f"문서 #{i}"
                
                print(f"🔍 [DEBUG] 최종 문서명: {description}")
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
            description = doc.get("data", {}).get("description", "")
            
            # 🔍 description이 없다면 문서 ID를 그대로 사용 (리스트와 동일한 로직)
            if not description:
                # 우선순위 1: 문서 ID 그대로 사용 (정확한 매칭을 위해)
                description = doc_id
                print(f"🔍 [DEBUG] 상세조회 - 문서 ID 그대로 사용: {description}")
                
                # 만약 문서 ID가 의미 없는 값이라면 다른 필드에서 찾기
                if not description or description == "ID 없음" or len(description) < 3:
                    # jsonData에서 찾기 (필드명 수정!)
                    json_data = doc.get("data", {}).get("jsonData")
                    if json_data:
                        try:
                            data = json.loads(json_data)
                            # 여러 필드를 시도해서 가장 적절한 문서명 찾기
                            description = (
                                data.get("description") or 
                                data.get("address") or
                                data.get("name") or 
                                data.get("title") or 
                                data.get("buildingName") or
                                "문서"
                            )
                            print(f"🔍 [DEBUG] 상세조회 - jsonData에서 찾은 문서명: {description}")
                        except Exception as e:
                            print(f"🔍 [DEBUG] 상세조회 - jsonData 파싱 오류: {e}")
                            description = "문서"
            
            if not description:
                description = "문서"
                
            print(f"🔍 [DEBUG] 상세조회 - 최종 문서명: {description}")
            
            formatted = f"🔍 **{description} 상세 정보:**\n\n"
            
            # 기본 정보 표시
            data_info = doc.get("data", {})
            if data_info.get("address"):
                formatted += f"📍 **주소:** {data_info['address']}\n"
            if data_info.get("versionName"):
                formatted += f"📋 **버전:** {data_info['versionName']}\n"
            if data_info.get("createdAt"):
                formatted += f"📅 **생성일:** {data_info['createdAt'][:10]}\n"
            formatted += "\n"
            
            # jsonData 상세 파싱 (필드명 수정!)
            json_data = doc.get("data", {}).get("jsonData")
            if json_data:
                try:
                    data = json.loads(json_data)
                    
                    # 견적서 프로세스 데이터 파싱
                    if "processData" in data:
                        formatted += "💼 **견적서 상세 내역:**\n\n"
                        process_data = data["processData"]
                        
                        total_amount = 0
                        for process in process_data:
                            if process.get("isActive", True) and process.get("total", 0) > 0:
                                name = process.get("name", "알 수 없음")
                                total = process.get("total", 0)
                                formatted += f"**{name}:** {total:,}원\n"
                                total_amount += total
                        
                        formatted += f"\n💰 **총 견적 금액:** {total_amount:,}원\n\n"
                    
                    # 기타 정보들
                    if "firstFloorPassword" in data:
                        formatted += f"🔑 **1층 비밀번호:** {data['firstFloorPassword']}\n"
                    if "unitPassword" in data:
                        formatted += f"🏠 **호별 비밀번호:** {data['unitPassword']}\n"
                    if "managerName" in data:
                        formatted += f"👤 **관리소장:** {data['managerName']}\n"
                    if "phoneNumber" in data:
                        formatted += f"📞 **연락처:** {data['phoneNumber']}\n"
                            
                except Exception as e:
                    formatted += f"   ⚠️ 상세 정보 파싱 중 오류: {str(e)}\n"
                    print(f"🔍 [DEBUG] jsonData 파싱 오류 상세: {e}")
            
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