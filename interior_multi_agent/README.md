# Interior Management System

인테리어 현장 관리와 Firebase 데이터를 처리하는 멀티 에이전트 시스템

## 시스템 구조

```
interior_multi_agent/
├── host-agent/           # 메인 Host Agent 서버
│   ├── __init__.py
│   ├── main.py          # FastAPI 서버 (메인 엔트리포인트)
│   └── agent.py         # Host Agent 로직
│
├── site-agent/          # 현장 관리 Agent 서버
│   ├── __init__.py
│   ├── main.py         # FastAPI 서버
│   └── agent.py        # 현장 관리 Agent 로직
│
├── firebase-agent/      # Firebase 연동 Agent 서버
│   ├── __init__.py
│   ├── main.py         # FastAPI 서버
│   ├── agent.py        # Firebase Agent 로직
│   ├── config/         # Firebase 설정
│   │   ├── config_template.txt
│   │   └── firebase_key.json  # Firebase 서비스 계정 키 (필요)
│   └── tools/          # Firebase 도구들
│       └── firebase_client.py
│
└── requirements.txt     # 프로젝트 의존성
```

## 설치 방법

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. Firebase 설정:
- Firebase Console에서 서비스 계정 키를 다운로드
- `firebase-agent/config/firebase_key.json`로 저장

## 실행 방법

```bash
cd interior_multi_agent
python -m uvicorn host-agent.main:app --reload --port 8000
```

## API 사용 예시

1. 현장 등록:
```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "site",
    "action": "register",
    "site_id": "site1",
    "address": "서울시 강남구",
    "area_sqm": 85.5
  }'
```

2. 현장 정보 조회:
```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "site",
    "action": "get_info",
    "site_id": "site1"
  }'
```

3. Firebase 일정 조회:
```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "firebase",
    "action": "query_schedule",
    "limit": 10
  }'
```

## Agent 설명

1. Host Agent
- 모든 요청의 진입점
- 요청을 분석하여 적절한 Agent에게 전달
- 결과를 취합하여 응답

2. Site Agent
- 현장 정보 등록 및 관리
- 현장 데이터 조회
- 현장 목록 관리

3. Firebase Agent
- Firestore 데이터 관리
- Storage 파일 관리
- 실시간 데이터 동기화

## 주의사항

1. Firebase 설정
- `firebase_key.json` 파일이 반드시 필요합니다
- `config_template.txt`를 참고하여 설정하세요

2. 포트 설정
- 기본 포트는 8000입니다
- 변경이 필요한 경우 실행 명령어의 포트를 수정하세요

## 라이선스

MIT License 