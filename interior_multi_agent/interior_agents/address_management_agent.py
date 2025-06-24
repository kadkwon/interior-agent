"""
주소 관리 전용 에이전트 - Firebase MCP 직접 연결 버전

🔄 변경 사항:
- 중복 도구 함수들 제거
- firebase_client.py를 통한 직접 Firebase MCP 연결
- 프롬프트 기반 지능형 요청 처리
""" 

import asyncio
import json
from datetime import datetime
from google.adk.agents import Agent
from .firebase_client import FirebaseDirectClient

class DataManagerAgent:
    """Firebase 데이터 관리를 위한 지능형 에이전트 클래스"""
    
    def __init__(self):
        """Firebase 클라이언트 초기화"""
        self.firebase_client = FirebaseDirectClient()
        print("🔥 데이터 관리 에이전트 초기화 완료")
    
    def _run_async(self, coro):
        """비동기 함수를 동기적으로 실행하는 헬퍼 메서드"""
        try:
            # 이미 실행 중인 이벤트 루프가 있는지 확인
            loop = asyncio.get_running_loop()
            # 있다면 새 스레드에서 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            # 실행 중인 루프가 없다면 직접 실행
            return asyncio.run(coro)
    
    def process_request(self, instruction: str) -> str:
        """
        사용자 요청을 분석하여 적절한 Firebase 작업 수행
        
        Args:
            instruction: 사용자 명령어/요청
            
        Returns:
            str: 작업 결과 메시지
        """
        try:
            instruction_lower = instruction.lower()
            
            # 컨텍스트 정보 파싱
            context_info = self._parse_context(instruction)
            
            # 1. 컬렉션 목록 조회
            if any(keyword in instruction_lower for keyword in ['컬렉션 목록', 'collection list', '전체 컬렉션']):
                return self._list_collections()
            
            # 2. 문서 목록 조회
            elif any(keyword in instruction_lower for keyword in ['주소', 'address', '주소 조회']):
                return self._list_addresses(instruction)
            
            elif any(keyword in instruction_lower for keyword in ['schedules', '스케줄', '일정']):
                return self._list_schedules(instruction)
            
            elif any(keyword in instruction_lower for keyword in ['ai-templates-v3', '템플릿', 'template']):
                return self._list_templates(instruction)
            
            elif any(keyword in instruction_lower for keyword in ['문서 목록', '목록 조회', 'list documents']):
                return self._handle_list_documents(instruction)
            
            # 3. 문서 상세 조회 (컨텍스트 기반)
            elif any(keyword in instruction_lower for keyword in ['상세', '첫 번째', '두 번째', '세 번째', '마지막']):
                return self._handle_detail_request(instruction, context_info)
            
            # 4. 문서 생성
            elif any(keyword in instruction_lower for keyword in ['추가', '생성', '만들어', 'add']):
                return self._handle_add_document(instruction)
            
            # 5. 문서 수정
            elif any(keyword in instruction_lower for keyword in ['수정', '업데이트', 'update']):
                return self._handle_update_document(instruction)
            
            # 6. 문서 삭제
            elif any(keyword in instruction_lower for keyword in ['삭제', '제거', 'delete']):
                return self._handle_delete_document(instruction)
            
            else:
                return self._show_help()
                
        except Exception as e:
            return f"❌ 요청 처리 중 오류가 발생했습니다: {str(e)}"
    
    def _parse_context(self, instruction: str) -> dict:
        """명령어에서 컨텍스트 정보 추출"""
        context = {"has_context": False, "previous_results": None, "collection": None}
        
        # 컨텍스트 정보 패턴 찾기
        if "[컨텍스트 정보]" in instruction:
            context["has_context"] = True
            # 이전 결과에서 컬렉션 정보 추출
            if "addressesJson" in instruction:
                context["collection"] = "addressesJson"
            elif "schedules" in instruction:
                context["collection"] = "schedules"
            elif "ai-templates-v3" in instruction:
                context["collection"] = "ai-templates-v3"
        
        return context
    
    def _list_collections(self) -> str:
        """Firebase 컬렉션 목록 조회"""
        try:
            async def get_collections():
                return await self.firebase_client.call_tool("firestore_list_collections", {"random_string": "dummy"})
            
            result_data = self._run_async(get_collections())
            
            if "error" in result_data:
                return f"❌ 컬렉션 목록 조회 실패: {result_data['error']}"
            
            # content에서 컬렉션 목록 추출
            collections = []
            if "content" in result_data:
                for item in result_data["content"]:
                    if "text" in item:
                        text = item["text"]
                        # JSON에서 컬렉션 ID들 추출
                        import re
                        # "id":"컬렉션명" 패턴으로 추출
                        collection_matches = re.findall(r'"id":"([^"]+)"', text)
                        collections.extend(collection_matches)
            
            if not collections:
                return "📂 Firebase에 컬렉션이 없습니다."
            
            result = "📂 Firebase 컬렉션 목록:\n"
            for i, collection in enumerate(collections, 1):
                result += f"{i}. **{collection}**\n"
            
            return result
            
        except Exception as e:
            return f"❌ 컬렉션 목록 조회 실패: {str(e)}"
    
    def _list_addresses(self, instruction: str) -> str:
        """주소 목록 조회"""
        return self._list_documents_by_collection("addressesJson", 50, instruction)
    
    def _list_schedules(self, instruction: str) -> str:
        """스케줄 목록 조회"""
        return self._list_documents_by_collection("schedules", 20, instruction)
    
    def _list_templates(self, instruction: str) -> str:
        """AI 템플릿 목록 조회"""
        return self._list_documents_by_collection("ai-templates-v3", 20, instruction)
    
    def _list_documents_by_collection(self, collection: str, limit: int, instruction: str) -> str:
        """특정 컬렉션의 문서 목록 조회"""
        try:
            async def get_documents():
                return await self.firebase_client.call_tool("firestore_list_documents", {
                    "collection": collection,
                    "limit": limit
                })
            
            result_data = self._run_async(get_documents())
            
            if "error" in result_data:
                return f"❌ {collection} 컬렉션 조회 실패: {result_data['error']}"
            
            # content에서 응답 텍스트 추출
            if "content" in result_data:
                for item in result_data["content"]:
                    if "text" in item:
                        return item["text"]
            
            return f"📄 '{collection}' 컬렉션에 문서가 없습니다."
            
        except Exception as e:
            return f"❌ {collection} 컬렉션 조회 실패: {str(e)}"
    
    def _handle_list_documents(self, instruction: str) -> str:
        """일반적인 문서 목록 조회 처리"""
        # 컬렉션 이름 추출
        collection = self._extract_collection_name(instruction)
        if not collection:
            return "❌ 컬렉션 이름을 찾을 수 없습니다. 예: 'schedules 컬렉션의 문서 목록을 조회해줘'"
        
        return self._list_documents_by_collection(collection, 20, instruction)
    
    def _handle_detail_request(self, instruction: str, context_info: dict) -> str:
        """상세 조회 요청 처리 (컨텍스트 기반)"""
        # 컨텍스트가 있고 순서 지정이 있는 경우
        if context_info["has_context"] and context_info["collection"]:
            collection = context_info["collection"]
            
            # 순서 추출
            order = self._extract_order(instruction)
            if order:
                return f"📋 {collection} 컬렉션의 {order} 문서 상세 조회 요청을 처리합니다.\n(실제 구현 시 이전 결과에서 해당 순서의 문서 ID를 추출하여 상세 조회)"
        
        return "❌ 상세 조회를 위해서는 이전 조회 결과가 필요합니다."
    
    def _handle_add_document(self, instruction: str) -> str:
        """문서 생성 요청 처리"""
        collection = self._extract_collection_name(instruction)
        if not collection:
            return "❌ 컬렉션 이름을 지정해주세요."
        
        return f"📝 {collection} 컬렉션에 문서 추가 기능 (구현 예정)"
    
    def _handle_update_document(self, instruction: str) -> str:
        """문서 수정 요청 처리"""
        return "📝 문서 수정 기능 (구현 예정)"
    
    def _handle_delete_document(self, instruction: str) -> str:
        """문서 삭제 요청 처리"""
        return "🗑️ 문서 삭제 기능 (구현 예정)"
    
    def _extract_collection_name(self, instruction: str) -> str:
        """명령어에서 컬렉션 이름 추출"""
        known_collections = [
            'schedules', 'addressesJson', 'ai-templates-v3', 'users', 'orders',
            'materials', 'projects', 'estimates', 'customers', 'inventory'
        ]
        
        instruction_lower = instruction.lower()
        for collection in known_collections:
            if collection.lower() in instruction_lower:
                return collection
        
        return None
    
    def _extract_order(self, instruction: str) -> str:
        """명령어에서 순서 표현 추출"""
        order_patterns = {
            '첫 번째': '1번째',
            '두 번째': '2번째',
            '세 번째': '3번째',
            '네 번째': '4번째',
            '마지막': '마지막'
        }
        
        for pattern, result in order_patterns.items():
            if pattern in instruction:
                return result
        
        return None
    
    def _show_help(self) -> str:
        """도움말 메시지 반환"""
        return """
🤖 데이터 관리 에이전트 도움말

**지원하는 명령어:**

1. **컬렉션 목록 조회**
   - "컬렉션 목록을 보여줘"

2. **문서 목록 조회**
   - "주소 조회" → addressesJson 컬렉션
   - "schedules 조회" → schedules 컬렉션  
   - "ai-templates-v3 조회" → ai-templates-v3 컬렉션

3. **상세 조회** (컨텍스트 기반)
   - "첫 번째 문서 상세 보여줘"
   - "두 번째 문서 상세 조회"

**지원 컬렉션:** schedules, addressesJson, ai-templates-v3, users, orders 등
        """

# 전역 에이전트 인스턴스
data_manager_instance = DataManagerAgent()

def create_address_agent():
    """주소/데이터 관리 에이전트 생성 - Firebase MCP 직접 연결"""
    try:
        print("🏠 데이터 관리 에이전트 생성 중... (Firebase MCP 직접 연결)")
        
        agent = Agent(
            model='gemini-2.5-flash-preview-05-20',
            name='data_manager',
            description="Firebase MCP 서버에 직접 연결하여 모든 컬렉션의 데이터를 관리하는 전문 에이전트입니다.",
            instruction=f'''당신은 Firebase Firestore의 모든 데이터를 관리하는 전문 AI 어시스턴트입니다.

## 🔥 CRITICAL: 지능형 요청 처리!

### ⚡ 키워드 감지 시 즉시 실행:

**사용자 요청을 받으면 즉시 data_manager_instance.process_request(instruction) 호출**

### 🧠 지원하는 주요 기능:

1. **컬렉션 목록 조회**
   - "컬렉션 목록", "collection list" 등
   
2. **문서 목록 조회**
   - "주소", "address" → addressesJson 컬렉션
   - "schedules", "스케줄" → schedules 컬렉션
   - "ai-templates-v3", "템플릿" → ai-templates-v3 컬렉션

3. **컨텍스트 기반 상세 조회**
   - "첫 번째", "두 번째", "마지막" 등 순서 기반 조회
   - 이전 조회 결과를 기반으로 한 상세 정보 요청

### 🔧 작업 방식:
1. 모든 요청을 data_manager_instance.process_request()로 전달
2. Firebase MCP 서버와 직접 통신하여 실시간 데이터 조회
3. 결과를 사용자 친화적으로 포맷팅하여 반환

### 🚫 절대 금지:
- ❌ 추가 정보 요청 금지 (바로 실행)
- ❌ 도구 사용 없이 텍스트로만 응답 금지
- ❌ "지원하지 않습니다" 응답 금지

### ✅ 올바른 동작:
1. 요청 받음 → 즉시 data_manager_instance.process_request() 호출
2. 결과를 명확하게 한국어로 설명
3. 에러 시에도 재시도 또는 대안 제시

**핵심**: 모든 Firebase 관련 요청은 data_manager_instance를 통해 처리하여 일관성과 효율성을 보장합니다!

모든 응답은 한국어로 해주세요.''',
            tools=[]
        )
        
        print(f"✅ 데이터 관리 에이전트 '{agent.name}' 생성 완료 (Firebase MCP 직접 연결)")
        return agent
        
    except Exception as e:
        print(f"❌ 데이터 관리 에이전트 생성 실패: {e}")
        print("기본 에이전트로 폴백합니다.")
        
        # 기본 에이전트로 폴백
        return Agent(
            model='gemini-2.5-flash-preview-05-20',
            name='data_manager_fallback',
            description="주소 정보를 관리하는 폴백 에이전트입니다.",
            instruction='''주소 관리 전문 AI 어시스턴트입니다. 

현재 Firebase 연결에 문제가 있어 기본 모드로 동작합니다.
주소 관련 질문에 대해 일반적인 조언과 안내를 제공하겠습니다.

주소 관리 기능:
1. 주소 형식 안내
2. 주소 입력 방법 설명  
3. 주소 관리 팁 제공
4. 인테리어 프로젝트에서의 주소 활용 방법

모든 응답은 한국어로 해주세요.'''
        )

# ADK web에서 사용할 에이전트 인스턴스
print("=== 주소 관리 에이전트 공통 클라이언트 초기화 시작 ===")
address_agent = create_address_agent()
print(f"=== 주소 관리 에이전트 초기화 완료: {address_agent.name} ===") 