"""
견적서 이메일 전송 전용 에이전트 - Estimate Email MCP 연결 버전

🔄 변경 사항:
- Firebase MCP와 Estimate Email MCP 연동
- 자연어 처리를 통한 이메일 주소 및 주소 추출
- 프롬프트 기반 지능형 이메일 전송 처리
""" 

import asyncio
import json
import re
import aiohttp
from datetime import datetime
from google.adk.agents import Agent
from .firebase_client import FirebaseDirectClient

class EmailManagerAgent:
    """견적서 이메일 전송을 위한 지능형 에이전트 클래스"""
    
    def __init__(self):
        """Firebase 클라이언트 및 Estimate Email MCP 연결 초기화"""
        self.firebase_client = FirebaseDirectClient()
        self.estimate_mcp_url = "http://localhost:8001"
        print("📧 이메일 관리 에이전트 초기화 완료")
    
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
        이메일 전송 요청을 분석하여 적절한 처리 수행
        
        Args:
            instruction: 사용자 명령어/요청
            
        Returns:
            str: 작업 결과 메시지
        """
        try:
            instruction_lower = instruction.lower()
            
            # 이메일 전송 의도 감지
            if self._detect_email_intent(instruction_lower):
                return self._handle_email_request(instruction)
            else:
                return self._show_help()
                
        except Exception as e:
            return f"❌ 이메일 요청 처리 중 오류가 발생했습니다: {str(e)}"
    
    def _detect_email_intent(self, instruction: str) -> bool:
        """이메일 전송 의도 감지"""
        email_keywords = [
            "이메일", "메일", "email", "전송", "보내", "발송", 
            "견적서", "estimate", "@"
        ]
        return any(keyword in instruction for keyword in email_keywords)
    
    def _handle_email_request(self, instruction: str) -> str:
        """이메일 전송 요청 처리"""
        try:
            print(f"📧 이메일 전송 요청 처리 시작: {instruction}")
            
            # 1. 파라미터 추출
            params = self._extract_email_params(instruction)
            print(f"📧 추출된 파라미터: {params}")
            
            # 2. Firebase에서 견적서 조회
            estimate_data = self._get_estimate_data(params['address'])
            print(f"📧 견적서 데이터 조회 완료: {len(estimate_data)}개 공정")
            
            # 3. Estimate Email MCP 호출
            result = self._send_email_via_mcp(
                email=params['email'],
                address=params['address'],
                process_data=estimate_data
            )
            
            return result
            
        except Exception as e:
            return f"❌ 이메일 전송 실패: {str(e)}"
    
    def _extract_email_params(self, instruction: str) -> dict:
        """메시지에서 이메일 주소와 주소 추출"""
        # 이메일 주소 추출
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, instruction)
        
        # 주소 패턴 추출 (한국 아파트 주소 형태)
        address_patterns = [
            r'([가-힣\s\d]+(?:아파트|APT)\s*\d+차?\s*\d+동\s*\d+호[^\s]*)',
            r'([가-힣\s\d]+\s*\d+동\s*\d+호[^\s]*)',
            r'([가-힣\s\d]+아파트[^\s]*)',
        ]
        
        address_matches = []
        for pattern in address_patterns:
            matches = re.findall(pattern, instruction)
            if matches:
                address_matches.extend(matches)
                break
        
        if not email_matches:
            raise ValueError("이메일 주소를 찾을 수 없습니다. 예: user@naver.com")
            
        if not address_matches:
            raise ValueError("주소를 찾을 수 없습니다. 예: 월배아이파크 1차 109동 2401호")
            
        return {
            "email": email_matches[0],
            "address": address_matches[0].strip()
        }
    
    def _get_estimate_data(self, address: str) -> list:
        """Firebase에서 견적서 데이터 조회"""
        async def get_estimate():
            # estimateVersionsV3에서 주소로 검색
            search_keys = [
                f"{address}_2차",
                f"{address}_1차", 
                address
            ]
            
            for search_key in search_keys:
                print(f"📧 견적서 검색 시도: {search_key}")
                
                result = await self.firebase_client.call_tool("firestore_get_document", {
                    "collection": "estimateVersionsV3",
                    "id": search_key
                })
                
                if "error" not in result and "data" in result:
                    print(f"📧 견적서 발견: {search_key}")
                    # JSON 데이터 파싱
                    json_data = json.loads(result["data"]["jsonData"])
                    return json_data["processData"]
            
            # 견적서를 찾을 수 없는 경우
            raise ValueError(f"견적서를 찾을 수 없습니다: {address}")
        
        return self._run_async(get_estimate())
    
    def _send_email_via_mcp(self, email: str, address: str, process_data: list) -> str:
        """Estimate Email MCP를 통한 이메일 전송"""
        async def send_email():
            print(f"📧 Estimate Email MCP 호출 시작: {self.estimate_mcp_url}")
            
            # MCP 서버에 직접 도구 호출 (simple_api_server.py 방식)
            payload = {
                "tool_name": "send_estimate_email",
                "arguments": {
                    "email": email,
                    "address": address,
                    "process_data": process_data
                }
            }
            
            timeout = aiohttp.ClientTimeout(total=60)
            
            async with aiohttp.ClientSession() as session:
                try:
                    # MCP 서버 테스트 연결 요청
                    async with session.post(
                        f"{self.estimate_mcp_url}/test_connection",
                        json={"random_string": "test"},
                        headers={"Content-Type": "application/json"},
                        timeout=timeout
                    ) as test_response:
                        if test_response.status != 200:
                            raise Exception(f"Estimate Email MCP 서버 연결 실패: {test_response.status}")
                    
                    # 실제 이메일 전송 요청
                    async with session.post(
                        f"{self.estimate_mcp_url}/send_estimate_email",
                        json=payload["arguments"],
                        headers={"Content-Type": "application/json"},
                        timeout=timeout
                    ) as response:
                        
                        response_text = await response.text()
                        print(f"📧 MCP 응답 상태: {response.status}")
                        print(f"📧 MCP 응답 내용: {response_text[:300]}")
                        
                        if response.status == 200:
                            try:
                                result = await response.json()
                                if "content" in result and len(result["content"]) > 0:
                                    return result["content"][0]["text"]
                                else:
                                    return f"✅ 견적서가 {email}로 전송되었습니다!"
                            except json.JSONDecodeError:
                                return f"✅ 견적서가 {email}로 전송되었습니다!"
                        else:
                            raise Exception(f"MCP 호출 실패: {response.status} - {response_text}")
                
                except aiohttp.ClientError as e:
                    raise Exception(f"HTTP 연결 오류: {str(e)}")
                except asyncio.TimeoutError:
                    raise Exception("요청 시간 초과 (60초)")
        
        return self._run_async(send_email())
    
    def _show_help(self) -> str:
        """도움말 메시지 반환"""
        return """
📧 이메일 관리 에이전트 도움말

**지원하는 명령어:**

1. **견적서 이메일 전송**
   - "월배아이파크 1차 109동 2401호 견적서를 test@naver.com으로 전송해줘"
   - "견적서를 user@gmail.com으로 메일 보내줘"
   - "gncloud86@naver.com으로 이메일 전송"

**필수 정보:**
- 이메일 주소 (예: user@domain.com)
- 주소 정보 (예: 월배아이파트 1차 109동 2401호)

**지원 기능:**
- 자동 견적서 조회 (Firebase estimateVersionsV3에서)
- 친근한 이메일 템플릿 적용
- 상세 공정별 금액 정보 포함
- 자동 기업이윤 계산

**예시:**
"월배아이파크 1차 109동 2401호_2차 견적서를 gncloud86@naver.com으로 전송해줘"
        """

# 전역 에이전트 인스턴스
email_manager_instance = EmailManagerAgent()

def create_email_agent():
    """견적서 이메일 전송 에이전트 생성"""
    try:
        print("📧 이메일 관리 에이전트 생성 중...")
        
        agent = Agent(
            model='gemini-2.5-flash-preview-05-20',
            name='email_manager',
            description="견적서 이메일 전송을 담당하는 전문 에이전트입니다.",
            instruction=f'''당신은 견적서 이메일 전송을 담당하는 전문 AI 어시스턴트입니다.

## 📧 핵심 임무: 견적서 이메일 전송

### ⚡ 키워드 감지 시 즉시 실행:

**사용자 요청을 받으면 즉시 email_manager_instance.process_request(instruction) 호출**

### 🧠 지원하는 주요 기능:

1. **자연어 처리**
   - 이메일 주소 자동 추출 (정규식 기반)
   - 주소 정보 자동 인식 (한국 아파트 주소 형태)
   - 의도 파악 및 분류

2. **견적서 조회**
   - Firebase estimateVersionsV3 컬렉션 검색
   - 버전별 견적서 조회 (2차 → 1차 → 기본 순서)
   - JSON 데이터 파싱 및 processData 추출

3. **이메일 전송**
   - Estimate Email MCP 서버 연동 (localhost:8001)
   - 친근한 템플릿 적용
   - 상세 공정별 금액 포함
   - 자동 기업이윤 계산

### 🔧 작업 방식:
1. 모든 요청을 email_manager_instance.process_request()로 전달
2. 자연어에서 이메일 주소와 주소 추출
3. Firebase에서 해당 견적서 조회 (여러 버전 시도)
4. Estimate Email MCP 호출하여 전송
5. 결과를 사용자에게 친화적으로 반환

### 🚫 절대 금지:
- ❌ 추가 정보 요청 금지 (바로 실행)
- ❌ 도구 사용 없이 텍스트로만 응답 금지
- ❌ "지원하지 않습니다" 응답 금지
- ❌ 이메일 전송을 직접 처리하려고 시도 금지

### ✅ 올바른 동작:
1. 요청 받음 → 즉시 email_manager_instance.process_request() 호출
2. 파라미터 추출 → Firebase 조회 → MCP 전송
3. 성공/실패 결과를 명화적으로 한국어로 설명
4. 에러 시 구체적인 원인과 해결 방법 제시

### 📧 지원 명령어 예시:
- "월배아이파크 1차 109동 2401호 견적서를 test@naver.com으로 전송해줘"
- "견적서를 user@gmail.com으로 메일 보내줘"
- "gncloud86@naver.com으로 이메일 전송"

**핵심**: 모든 이메일 관련 요청은 email_manager_instance를 통해 처리하여 일관성과 효율성을 보장합니다!

모든 응답은 한국어로 해주세요.''',
            tools=[]
        )
        
        print(f"✅ 이메일 관리 에이전트 '{agent.name}' 생성 완료")
        return agent
        
    except Exception as e:
        print(f"❌ 이메일 관리 에이전트 생성 실패: {e}")
        print("기본 에이전트로 폴백합니다.")
        
        # 기본 에이전트로 폴백
        return Agent(
            model='gemini-2.5-flash-preview-05-20',
            name='email_manager_fallback',
            description="견적서 이메일 전송을 관리하는 폴백 에이전트입니다.",
            instruction='''견적서 이메일 전송 전문 AI 어시스턴트입니다. 

현재 MCP 연결에 문제가 있어 기본 모드로 동작합니다.
이메일 전송 관련 질문에 대해 일반적인 조언과 안내를 제공하겠습니다.

이메일 전송 기능:
1. 견적서 형식 안내
2. 이메일 전송 방법 설명  
3. 견적서 관리 팁 제공
4. 인테리어 프로젝트에서의 견적서 활용 방법

모든 응답은 한국어로 해주세요.'''
        )

# ADK web에서 사용할 에이전트 인스턴스
print("=== 이메일 관리 에이전트 공통 클라이언트 초기화 시작 ===")
email_agent = create_email_agent()
print(f"=== 이메일 관리 에이전트 초기화 완료: {email_agent.name if email_agent else 'None'} ===") 