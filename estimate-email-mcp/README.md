# 📧 Estimate Email MCP 서버

FastMCP 기반 견적서 이메일 전송 전용 MCP 서버입니다.

## 🎯 역할

- Claude Web에서 Firebase MCP로 조회한 견적서 데이터를 받아서
- **직접 Cloud Functions API를 호출**하여 PDF 첨부 이메일 전송
- 기존 PDF 생성 및 이메일 전송 로직 재사용 (React 앱 우회)

## 🔄 동작 플로우

```
Claude Web
    ↓ (자연어 파싱)
Firebase MCP (기존 리모트)
    ↓ (견적서 데이터 조회)
Estimate Email MCP (신규)
    ↓ (Cloud Functions 직접 호출)
PDF 생성 + Gmail API
    ↓ (결과 반환)
Claude Web → 사용자
```

## 🛠️ 설치 및 실행

### 1. 의존성 설치
```bash
cd interior-agent/estimate-email-mcp
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
python server.py
```

서버는 `http://localhost:8001/sse`에서 실행됩니다.

### 3. 또는 시작 스크립트 사용
```bash
chmod +x start.sh
./start.sh
```

## 🔧 Claude Web 설정

Claude Web에서 Remote MCP 서버로 연결:

```json
{
  "mcpServers": {
    "firebase": {
      "url": "https://firebase-mcp-existing-url",
      "type": "remote"
    },
    "estimate-email": {
      "url": "http://localhost:8001/sse",
      "type": "remote"
    }
  }
}
```

## 📋 지원 도구

### `send_estimate_email`
견적서를 이메일로 전송합니다.

**매개변수:**
- `email`: 수신자 이메일 주소
- `address`: 견적서 주소
- `process_data`: 공정 데이터 리스트 (Firebase에서 조회)
- `notes`: 견적서 메모 (선택사항)
- `hidden_processes`: 숨김 공정 설정 (선택사항)
- `corporate_profit`: 기업이윤 설정 (선택사항)
- `subject`: 이메일 제목 (선택사항)
- `template_content`: 이메일 본문 (선택사항)

### `test_connection`
MCP 서버 연결 상태를 테스트합니다.

### `get_server_info`
서버 정보 및 설정을 조회합니다.

## ⚙️ 설정

`config.py`에서 다음 설정을 관리합니다:

- **서버 설정**: 호스트, 포트, 이름, 버전
- **Cloud Functions**: 직접 호출할 API URL
- **이메일 설정**: 타임아웃, 템플릿, 기본 기업이윤

## 🧪 테스트

### 설정 검증
```bash
python config.py
```

### MCP 서버 기능 테스트
```bash
python test_client.py
```

## 🚀 실제 사용 예시

Claude Web에서:

```
"gncloud86@naver.com에 수성구 래미안 아파트 버전2를 보내줘"
```

1. Firebase MCP가 주소와 버전 데이터 조회
2. Estimate Email MCP가 Cloud Functions 직접 호출
3. PDF 생성 및 Gmail로 전송
4. 결과를 Claude에 반환

## 🔑 핵심 특징

- ✅ **React 앱 우회**: Cloud Functions 직접 호출로 단순화
- ✅ **Remote MCP**: Claude Web에서 접근 가능
- ✅ **기존 코드 재사용**: PDF 생성 및 이메일 로직 보존
- ✅ **FastMCP 표준**: 올바른 도구 응답 형식
- ✅ **에러 처리**: 상세한 로깅 및 예외 처리
- ✅ **설정 관리**: 중앙화된 config.py

## 📞 문제 해결

### 포트 충돌
```bash
# 포트 8001이 사용 중인 경우
netstat -ano | findstr :8001
taskkill /PID <PID번호> /F
```

### Cloud Functions 연결 실패
- URL 확인: `https://us-central1-interior-one-click.cloudfunctions.net/sendEstimatePdfHttp`
- 네트워크 연결 상태 확인
- 타임아웃 설정 조정 (config.py)

## 🔍 디버깅

서버 실행 시 상세한 로그가 출력됩니다:
- 📧 이메일 전송 시작/완료
- 🔄 API 호출 상태
- 📊 전송 데이터 정보
- ❌ 오류 상세 정보

## 🚀 확장 계획

- [ ] 배치 이메일 전송
- [ ] 이메일 템플릿 관리
- [ ] 전송 이력 추적
- [ ] 스케줄링 기능 