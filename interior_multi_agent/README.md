# 🏠 인테리어 멀티 에이전트 시스템

Google Agent Development Kit(ADK)를 사용해서 만든 **인테리어 업무를 자동화해주는 AI 로봇** 시스템입니다!

## 📁 현재 프로젝트 구조

```
interior_multi_agent/                   # 📂 메인 프로젝트 폴더
├── 📂 interior_agents/                 # AI 에이전트들이 모여있는 폴더
│   ├── 📂 tools/                       # 🔧 도구 모듈들
│   │   ├── 🔥 firebase_client.py       # Firebase 연동 클라이언트 (9.3KB)
│   │   └── 📄 __init__.py              # 도구 패키지 초기화
│   ├── 📂 agent/                       # 빈 폴더 (향후 확장용)
│   ├── 🤖 agent.py                     # 모든 AI 에이전트들의 핵심 코드 (21KB)
│   ├── 📄 __init__.py                  # Python 패키지 초기화 파일
│   └── 📝 config_template.txt          # 환경설정 파일 템플릿
├── 📄 requirements.txt                 # 필요한 Python 패키지 목록
└── 📖 README.md                        # 사용법 설명서 (이 파일!)
```

## 🤖 각 파일이 하는 일

### 📄 `interior_agents/__init__.py` 
```python
from .agent import root_agent
__all__ = ['root_agent']
```
- **역할**: 메인 에이전트를 외부에서 사용할 수 있게 export
- **쉽게 말하면**: "여기서 root_agent를 가져다 쓸 수 있어!" 라고 알려주는 파일

### 🤖 `interior_agents/agent.py` (21KB - 핵심 파일!)
이 파일 안에는 **4명의 전문가 AI 로봇**들과 **Firebase 연동 기능**이 들어있습니다:

#### 🏢 1. 현장주소 관리 로봇
```python
# 이런 일들을 담당해요:
def register_site()      # 새 공사현장 정보 저장하기
def get_site_info()      # 현장 정보 찾아보기  
def list_all_sites()     # 모든 현장 목록 보여주기
```

#### 💰 2. 원가계산 로봇
```python  
# 이런 일들을 담당해요:
def calculate_material_cost()  # 자재(재료) 비용 계산하기
def estimate_labor_cost()      # 일하는 사람 인건비 계산하기
def get_total_cost()          # 전체 비용 합계 내기
```

#### 💳 3. 결제관리 로봇
```python
# 이런 일들을 담당해요:
def create_payment_invoice()   # 청구서(계산서) 만들기
def get_payment_status()       # 돈 받았는지 확인하기
def update_payment_status()    # 결제 상태 바꾸기
def list_all_invoices()        # 모든 청구서 목록 보기
```

#### 📊 4. 프로젝트 현황관리 로봇
```python
# 이런 일들을 담당해요:
def get_project_summary()      # 전체 사업 현황 요약하기
```

#### 🔥 5. Firebase 연동 로봇
```python
# 온라인 데이터베이스 관련 일들:
def query_schedule_collection()    # 일정 데이터 조회하기
def get_firebase_project_info()    # Firebase 프로젝트 정보 확인
def list_firestore_collections()  # 데이터베이스 컬렉션 목록 보기
def query_any_collection()        # 원하는 컬렉션 데이터 조회
def list_storage_files()          # 파일 저장소 목록 보기
```

### 🔧 `interior_agents/tools/firebase_client.py` (9.3KB)
- **역할**: Firebase(구글의 온라인 데이터베이스) 연결을 담당하는 전문 도구
- **주요 기능**:
  - Firestore 데이터베이스 조회/수정
  - Firebase Storage 파일 관리
  - 사용자 인증 관리
  - 견적서 PDF 이메일 전송

### 📝 `config_template.txt`
```bash
# Google AI Studio 사용하는 경우 (권장 - 빠른 시작)
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=여기에_Google_AI_Studio_API_키를_입력하세요
```
- **역할**: 환경설정 파일(`.env`)을 만들 때 참고하는 견본
- **사용법**: 이 파일을 복사해서 `.env`로 이름 바꾸고 실제 API 키 입력

### 📄 `requirements.txt`
```
google-adk
python-dotenv
requests
asyncio
aiohttp
```
- **역할**: 이 프로그램이 작동하는데 필요한 다른 프로그램들의 목록
- **쉽게 말하면**: "이 재료들이 있어야 요리(프로그램)를 만들 수 있어요" 하는 장보기 목록

## 🚀 주요 기능 (무엇을 할 수 있나요?)

### 🏢 현장 관리 
- ✅ 공사 현장 정보 등록 (주소, 크기 등)
- ✅ 등록된 현장 정보 찾아보기
- ✅ 모든 현장 목록 한번에 보기

### 💰 비용 계산
- ✅ 자재비 자동 계산 (페인트, 타일, 벽지, 바닥재, 조명, 수납장)
- ✅ 인건비 자동 계산 (작업자 일당 × 작업일수)
- ✅ 프로젝트 전체 비용 합계

### 💳 결제 관리
- ✅ 고객용 청구서 자동 생성
- ✅ 결제 상태 추적 (대기중, 완료, 취소)
- ✅ 모든 결제 내역 관리

### 📊 사업 현황 파악
- ✅ 전체 프로젝트 요약 보고서
- ✅ 매출 통계 (총 매출, 입금 완료, 미수금)
- ✅ 현장별 진행 상황 한눈에 보기

### 🔥 Firebase 온라인 연동
- ✅ 실시간 일정 관리 (schedule 컬렉션)
- ✅ 온라인 데이터베이스 조회
- ✅ 파일 저장소 관리
- ✅ 프로젝트 정보 동기화

## 📋 설치하고 실행하는 방법

### 🔧 1단계: 컴퓨터 환경 준비하기
```bash
# 1. 프로그램들끼리 충돌 안나게 격리된 공간(가상환경) 만들기
python -m venv .venv

# 2. 가상환경 켜기
# Windows 사용자:
.venv\Scripts\activate
# Mac/Linux 사용자:
source .venv/bin/activate

# 3. 필요한 프로그램들 설치하기
pip install -r requirements.txt
```

### 🗝️ 2단계: Google AI 사용 권한 받기

#### Google AI Studio에서 무료 API 키 받기:
1. 🌐 https://aistudio.google.com/ 접속
2. 🔑 **"Get API Key"** 버튼 클릭
3. 📋 생성된 키 복사하기

#### 설정 파일에 키 입력하기:
1. `interior_agents/config_template.txt` 파일을 복사
2. 이름을 `interior_agents/.env`로 바꾸기
3. 파일 열어서 API 키 입력:
```bash
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=여기에_복사한_실제_API_키_붙여넣기
```

### 🚀 3단계: 프로그램 실행하기

#### 방법 1: 웹 브라우저에서 사용 (추천!)
```bash
adk web
```
- 브라우저에서 `http://localhost:8000` 접속
- 예쁜 화면에서 AI와 대화하면서 사용 가능

#### 방법 2: 터미널에서 바로 사용
```bash
adk run interior_agents
```
- 검은 화면에서 글자로만 AI와 대화

## 🧪 바로 해볼 수 있는 테스트

### 🎯 전체 과정 한번에 테스트하기
AI에게 이렇게 말해보세요:
```
"강남구 논현동 30평 아파트 거실 리모델링 프로젝트를 시작하고 싶습니다. 
현장 등록부터 견적서 작성까지 전체 과정을 도와주세요."
```

### 📝 단계별로 천천히 테스트하기
1. **현장 등록하기**: 
   ```
   "현장코드 GN001로 서울시 강남구 논현동 123-45, 면적 99㎡ 현장을 등록해주세요"
   ```

2. **자재비 계산하기**: 
   ```
   "GN001 현장에 페인트 99㎡, 타일 30㎡ 원가를 계산해주세요"
   ```

3. **인건비 계산하기**: 
   ```
   "GN001 현장의 페인트 작업 3일 인건비를 계산해주세요"
   ```

4. **청구서 만들기**: 
   ```
   "GN001 현장의 결제 내역서를 생성해주세요"
   ```

5. **전체 현황 보기**: 
   ```
   "전체 프로젝트 현황을 보여주세요"
   ```

### 🔥 Firebase 연동 테스트하기
- `"Firebase 프로젝트 정보를 확인해주세요"`
- `"Firestore 컬렉션 목록을 보여주세요"`
- `"schedule 컬렉션을 조회해주세요"`
- `"Storage 파일 목록을 보여주세요"`

### 🔄 추가로 해볼 수 있는 것들
- `"등록된 모든 현장 목록을 보여주세요"`
- `"GN001 현장의 총 원가를 확인해주세요"`  
- `"생성된 모든 결제 내역서를 보여주세요"`
- `"INV-GN001-20240101120000 결제 상태를 완료로 변경해주세요"`

## 🔍 AI 로봇들이 어떻게 협력하는지 보기

웹 UI의 **Events(이벤트)** 탭을 클릭하면:
- 🤖 어떤 AI 로봇이 언제 일했는지
- 📊 각 작업이 얼마나 걸렸는지  
- 🔄 로봇들끼리 어떻게 정보를 주고받았는지
- ⚡ 전체 과정이 어떤 순서로 진행되었는지

모든 것을 실시간으로 볼 수 있어요!

## 💰 자재 종류별 기본 단가표

| 자재 이름 | 가격 (원/㎡) | 설명 |
|-----------|-------------|------|
| paint | 15,000 | 벽에 칠하는 페인트 |
| tile | 30,000 | 화장실, 주방용 타일 |
| wallpaper | 20,000 | 벽에 붙이는 벽지 |
| flooring | 50,000 | 바닥에 까는 마루, 장판 |
| lighting | 100,000 | 조명기구 (개당 가격) |
| cabinet | 200,000 | 수납장, 붙박이장 |

## 👷 작업 종류별 인건비 (하루 일당)

| 작업 종류 | 하루 일당 (원) | 어떤 일인가요? |
|-----------|-------------|-------------|
| painting | 150,000 | 페인트칠 전문 작업자 |
| tiling | 200,000 | 타일 붙이기 전문 작업자 |
| flooring | 180,000 | 바닥재 시공 전문 작업자 |
| general | 120,000 | 일반 보조 작업자 |

## ⚠️ 문제 해결 (뭔가 안될 때)

### 🚫 `adk: command not found` 에러가 날 때
- **원인**: 가상환경이 꺼져있거나 패키지 설치가 안됨
- **해결방법**: 
  ```bash
  # 1. 가상환경 다시 켜기
  .venv\Scripts\activate  # Windows
  source .venv/bin/activate  # Mac/Linux
  
  # 2. 패키지 다시 설치
  pip install -r requirements.txt
  ```

### 🔑 API 키 관련 에러가 날 때
- **원인**: `.env` 파일에 올바른 API 키가 없음
- **해결방법**: 
  1. Google AI Studio에서 새 API 키 발급
  2. `.env` 파일 다시 확인하고 올바른 키 입력

### 🔥 Firebase 연결 에러가 날 때
- **원인**: Firebase 클라이언트 모듈 import 실패
- **해결방법**: 
  - 시스템이 자동으로 더미 객체를 생성하여 기본 기능은 동작
  - Firebase 기능이 필요하면 `tools/firebase_client.py` 파일 확인

### 🌐 웹 UI가 안 열릴 때
- **해결방법**: `adk web --no-reload` 명령어 사용

## 🔧 시스템 아키텍처

```mermaid
graph TD
    A[🏠 Root Agent<br/>인테리어 매니저] --> B[🏢 현장관리 모듈]
    A --> C[💰 원가계산 모듈]
    A --> D[💳 결제관리 모듈]
    A --> E[📊 현황관리 모듈]
    A --> F[🔥 Firebase 연동 모듈]
    
    F --> G[Firestore<br/>데이터베이스]
    F --> H[Firebase Storage<br/>파일 저장소]
    F --> I[Firebase Auth<br/>사용자 인증]
    
    B --> J[project_data<br/>메모리 저장소]
    C --> J
    D --> J
    E --> J
```

## 🔧 나중에 더 발전시킬 수 있는 것들

이 기본 시스템을 더 고급스럽게 만들려면:
- 🗄️ **진짜 데이터베이스** 연결하기 (PostgreSQL, MongoDB 등)
- 📷 **사진 업로드** 기능 (현장 사진 분석)
- 🏗️ **3D 모델링** 제안 기능
- 💱 **실시간 자재 가격** 자동 업데이트
- 📱 **고객 관리 시스템** 연동
- 🤝 **협력업체 관리** 시스템
- 📱 **모바일 앱** 버전 개발
- 🔄 **더 많은 Firebase 기능** 활용

---

### 🎉 만든 사람에게 한마디
이 시스템은 **간단한 테스트용**이지만, **실제 인테리어 업무에 바로 적용**할 수 있을 만큼 실용적으로 만들어졌습니다! 

특히 **Firebase 연동 기능**으로 온라인 데이터베이스와 실시간 동기화가 가능해서 여러 사람이 함께 사용할 수 있어요!

궁금한 점이 있으면 언제든 물어보세요! 🚀 

## 🚀 **NEW: Vertex AI Agent Engine 배포**

이제 **클라우드에서 완전 관리형 AI 에이전트**로 배포할 수 있습니다!

### 배포 방법

#### 1단계: 환경 설정 (자동)
```bash
# 모든 환경을 자동으로 설정
python setup_deployment.py
```

#### 2단계: 배포 실행
```bash
# 개발 환경 배포
python deploy.py --environment development

# 프로덕션 환경 배포 (아시아 지역)
python deploy.py --environment production --region asia-northeast1
```

#### 3단계: 배포 테스트
```bash
# 빠른 테스트
python quick_test.py

# 상세 테스트
python test_deployment.py
```

### 배포 특징
- ✅ **완전 관리형**: 인프라 관리 불필요
- 🔒 **보안**: Google Cloud 보안 기준 준수
- 📈 **자동 확장**: 사용량에 따른 자동 스케일링
- 📊 **모니터링**: Cloud Trace, Cloud Logging 통합

### 배포 아키텍처

```
🏠 인테리어 에이전트
├── 📦 Google ADK 기반
├── 🔥 Firebase 실시간 연동
├── ☁️ Vertex AI Agent Engine
├── 🗄️ Cloud Storage 스테이징
└── 📊 Cloud Monitoring
```

## 📋 기존 로컬 설정

### 사전 요구사항
- Python 3.9+
- Google AI Studio API 키 또는 Vertex AI 접근 권한
- Firebase 프로젝트 설정

### 설치 및 실행

1. **저장소 클론**
```bash
git clone [repository-url]
cd interior_multi_agent
```

2. **가상환경 설정**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate     # Windows
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **환경설정**
```bash
# 설정 템플릿 복사
cp interior_agents/config_template.txt .env

# .env 파일을 편집하여 실제 API 키 입력
# GOOGLE_API_KEY=your_actual_api_key_here
```

5. **실행**
```bash
cd interior_agents
python main.py
```

## 🏗️ 프로젝트 구조

```
interior_multi_agent/
├── 📁 interior_agents/              # 🎯 메인 에이전트 패키지
│   ├── 📄 __init__.py              # root_agent export
│   ├── 🤖 agent_main.py           # 메인 통합 에이전트
│   ├── 🔥 firebase_mcp_rules.py   # Firebase MCP 규칙
│   ├── 📁 services/                # 🛠️ 비즈니스 서비스
│   ├── 📁 tools/                   # 🔧 도구 모듈들
│   ├── 📁 client/                  # 📡 클라이언트 연결
│   ├── 📁 utils/                   # 🧰 유틸리티 함수들
│   └── 📁 config/                  # ⚙️ 배포 설정 (NEW)
├── 📄 requirements.txt             # 의존성 패키지
├── 📄 deployment_requirements.txt  # 배포용 패키지 (NEW)
├── 📄 deployment.env.template      # 배포 환경설정 (NEW)
├── 🚀 deploy.py                   # 배포 스크립트 (NEW)
├── 🔧 setup_deployment.py         # 환경 설정 (NEW)
├── 🧪 quick_test.py               # 빠른 테스트 (NEW)
├── 📚 DEPLOYMENT_GUIDE.md          # 배포 가이드 (NEW)
└── 📋 README.md                   # 프로젝트 설명
```

## 🔧 기능 상세

### 1. 현장 관리 시스템
- **현장 등록**: 주소, 평수, 시공 유형 등 기본 정보 입력
- **현장 조회**: 등록된 모든 현장 정보 실시간 조회
- **현장 수정**: 기존 현장 정보 업데이트

### 2. 지급 계획 관리
- **자동 계산**: 평수와 시공 유형에 따른 자동 견적
- **단계별 지급**: 계약금, 중도금, 잔금 등 단계별 관리
- **지급 추적**: 각 단계별 지급 현황 실시간 추적

### 3. Firebase 실시간 연동
- **Firestore**: 구조화된 데이터 저장 및 조회
- **Storage**: 현장 사진, 도면 등 파일 관리
- **실시간 동기화**: 데이터 변경사항 즉시 반영

## 📊 사용 예시

### 현장 등록
```
사용자: "서울시 강남구 테헤란로 123번지, 30평 아파트 전체 리모델링 현장을 등록해주세요"

에이전트: "네, 새로운 현장을 등록하겠습니다.
- 주소: 서울시 강남구 테헤란로 123번지
- 면적: 30평 (99.2㎡)
- 시공유형: 전체 리모델링
- 예상 공사비: 1억 2천만원
Firebase에 성공적으로 저장되었습니다."
```

### 지급 계획 수립
```
사용자: "위 현장의 지급 계획을 세워주세요"

에이전트: "30평 전체 리모델링 지급 계획을 수립했습니다:
📋 총 공사비: 120,000,000원
💰 계약금 (10%): 12,000,000원 - 계약 시
💰 중도금1 (30%): 36,000,000원 - 철거/전기 완료 시  
💰 중도금2 (30%): 36,000,000원 - 타일/도배 완료 시
💰 잔금 (30%): 36,000,000원 - 준공 시"
```

## 🌐 배포 환경 비교

| 항목 | 로컬 개발 | Agent Engine 배포 |
|------|-----------|-------------------|
| **인프라 관리** | 개발자 직접 관리 | Google Cloud 완전 관리 |
| **확장성** | 수동 스케일링 | 자동 스케일링 |
| **보안** | 로컬 보안 설정 | 클라우드 보안 기준 |
| **모니터링** | 수동 로깅 | Cloud Monitoring 통합 |
| **비용** | 개발 비용만 | 사용량 기반 과금 |
| **접근성** | 로컬 네트워크만 | 글로벌 접근 가능 |

## 📚 추가 문서

- **[배포 가이드](DEPLOYMENT_GUIDE.md)**: Vertex AI Agent Engine 배포 상세 가이드
- **[기술 사양서](기술_사양서.md)**: 시스템 아키텍처 및 기술 스택
- **[프로젝트 현황](프로젝트_현황_요약.md)**: 개발 진행 상황

## 🔗 관련 링크

- **Vertex AI Agent Engine**: https://cloud.google.com/vertex-ai/docs/agent-engine
- **Google ADK**: https://google.github.io/adk-docs/
- **Firebase**: https://firebase.google.com/

## 🆘 지원 및 문제 해결

### 일반적인 문제
1. **API 키 오류**: `.env` 파일의 API 키 확인
2. **Firebase 연결 실패**: Firebase 프로젝트 설정 확인
3. **패키지 설치 오류**: Python 버전 및 가상환경 확인

### 배포 관련 문제
1. **권한 오류**: Google Cloud 프로젝트 권한 확인
2. **API 비활성화**: 필수 API 활성화 확인
3. **버킷 생성 실패**: Cloud Storage 권한 확인

### 지원 요청
- 📧 이메일: support@your-domain.com
- 🐛 GitHub Issues: [Repository Issues](https://github.com/your-repo/issues)

---

**🎉 이제 로컬 개발부터 클라우드 배포까지 완벽하게 지원합니다!** 