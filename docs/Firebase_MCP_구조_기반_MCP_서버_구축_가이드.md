# Firebase-MCP 구조 기반 MCP 서버 구축 가이드

## 개요

이 가이드는 Firebase-MCP의 성공적인 구조를 참조하여 새로운 MCP 서버를 구축하는 방법을 설명합니다. estimate-email-mcp를 Firebase-MCP와 동일한 구조로 변환하면서 얻은 경험을 바탕으로 작성되었습니다.

## 🎯 핵심 원칙

Firebase-MCP는 Claude와 완벽하게 호환되는 이유:
1. **표준 MCP SDK 사용**: `@modelcontextprotocol/sdk` 공식 라이브러리
2. **StreamableHTTPServerTransport**: 세션 기반 HTTP 통신
3. **TypeScript 기반**: 타입 안정성과 표준 Node.js 환경
4. **Cloud Run 최적화**: 컨테이너 기반 무상태 서비스

## 📁 프로젝트 구조

```
your-mcp-server/
├── src/
│   ├── index.ts                 # 메인 서버 클래스
│   ├── config.ts               # 설정 관리
│   ├── utils/
│   │   └── logger.ts           # 로깅 유틸리티
│   └── transports/
│       ├── index.ts            # Transport 팩토리
│       └── http.ts             # HTTP transport 구현
├── package.json
├── tsconfig.json
├── Dockerfile
├── .dockerignore
└── README.md
```

## 🛠️ 구현 단계

### 1. 패키지 설정 (package.json)

```json
{
  "name": "your-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsc && node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.11.0",
    "express": "^5.1.0",
    "cors": "^2.8.5",
    "dotenv": "^16.5.0"
  },
  "devDependencies": {
    "@types/express": "^5.0.1",
    "@types/cors": "^2.8.17",
    "@types/node": "^22.15.14",
    "typescript": "^5.8.3"
  }
}
```

### 2. TypeScript 설정 (tsconfig.json)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "node",
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "strict": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### 3. 설정 관리 (src/config.ts)

```typescript
import dotenv from 'dotenv';
dotenv.config();

export interface ServerConfig {
  name: string;
  version: string;
  transport: 'http';
  port: number;
  host: string;
  // 기타 서비스별 설정
}

const config: ServerConfig = {
  name: 'your-mcp-server',
  version: '1.0.0',
  transport: 'http',
  port: parseInt(process.env.PORT || '8080', 10),
  host: process.env.HOST || '0.0.0.0',
};

export default config;
```

### 4. 로거 유틸리티 (src/utils/logger.ts)

```typescript
export const logger = {
  debug: (message: string, ...args: any[]) => {
    if (process.env.DEBUG === 'true') {
      console.debug(`[DEBUG] ${message}`, ...args);
    }
  },
  info: (message: string, ...args: any[]) => {
    console.info(`[INFO] ${message}`, ...args);
  },
  warn: (message: string, ...args: any[]) => {
    console.warn(`[WARN] ${message}`, ...args);
  },
  error: (message: string, ...args: any[]) => {
    console.error(`[ERROR] ${message}`, ...args);
  }
};
```

### 5. HTTP Transport (src/transports/http.ts)

**핵심**: Firebase-MCP와 동일한 StreamableHTTPServerTransport 사용

```typescript
import express from 'express';
import cors from 'cors';
import { randomUUID } from 'node:crypto';
import type { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { isInitializeRequest } from '@modelcontextprotocol/sdk/types.js';
import { logger } from '../utils/logger.js';
import type { ServerConfig } from '../config.js';

export async function initializeHttpTransport(server: Server, config: ServerConfig): Promise<void> {
  const app = express();
  
  app.use(cors());
  app.use(express.json());

  // 세션별 transport 저장소
  const transports: { [sessionId: string]: StreamableHTTPServerTransport } = {};

  // 헬스체크 엔드포인트
  app.get('/', (req, res) => {
    res.json({
      status: 'healthy',
      service: config.name,
      version: config.version,
      transport: 'http'
    });
  });

  // MCP 메인 엔드포인트
  app.post('/mcp', async (req, res) => {
    try {
      const sessionId = req.headers['mcp-session-id'] as string | undefined;
      let transport: StreamableHTTPServerTransport;

      if (sessionId && transports[sessionId]) {
        // 기존 세션 재사용
        transport = transports[sessionId];
      } else if (!sessionId && isInitializeRequest(req.body)) {
        // 새로운 세션 초기화
        transport = new StreamableHTTPServerTransport({
          sessionIdGenerator: () => randomUUID(),
          onsessioninitialized: sessionId => {
            transports[sessionId] = transport;
            logger.debug(`Initialized new session: ${sessionId}`);
          },
        });

        transport.onclose = () => {
          if (transport.sessionId) {
            logger.debug(`Closing session: ${transport.sessionId}`);
            delete transports[transport.sessionId];
          }
        };

        await server.connect(transport);
      } else {
        res.status(400).json({
          jsonrpc: '2.0',
          error: { code: -32000, message: 'Bad Request: No valid session ID provided' },
          id: null,
        });
        return;
      }

      await transport.handleRequest(req, res, req.body);
    } catch (error) {
      logger.error('Error handling MCP request:', error);
      res.status(500).json({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // SSE와 세션 종료 핸들러
  const handleSessionRequest = async (req: express.Request, res: express.Response): Promise<void> => {
    const sessionId = req.headers['mcp-session-id'] as string | undefined;
    if (!sessionId || !transports[sessionId]) {
      res.status(400).send('Invalid or missing session ID');
      return;
    }
    await transports[sessionId].handleRequest(req, res);
  };

  app.get('/mcp', handleSessionRequest);
  app.delete('/mcp', handleSessionRequest);

  // 서버 시작
  const serverInstance = app.listen(config.port, config.host, () => {
    logger.info(`HTTP transport listening on ${config.host}:${config.port}/mcp`);
  });
}
```

### 6. 메인 서버 클래스 (src/index.ts)

```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { logger } from './utils/logger.js';
import config from './config.js';
import { initializeTransport } from './transports/index.js';

class YourMcpServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      { name: config.name, version: config.version },
      { capabilities: { tools: {} } }
    );

    this.setupToolHandlers();

    // 그레이스풀 셧다운
    this.server.onerror = () => {};
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupToolHandlers(): void {
    // 도구 목록 등록
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'your_tool_name',
          description: '도구 설명',
          inputSchema: {
            type: 'object',
            properties: {
              // 입력 스키마 정의
            },
            required: ['필수_파라미터'],
          },
        },
      ],
    }));

    // 도구 호출 처리
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        const { name, arguments: args } = request.params;

        switch (name) {
          case 'your_tool_name':
            return await this.handleYourTool(args);
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        logger.error('Error in tool call:', errorMessage);
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: errorMessage }) }],
        };
      }
    });
  }

  private async handleYourTool(args: any): Promise<any> {
    // 도구 로직 구현
    return {
      content: [{ type: 'text', text: '결과 메시지' }],
    };
  }

  async run(): Promise<void> {
    logger.info(`Starting ${config.name} v${config.version}`);
    await initializeTransport(this.server, config);
  }
}

// 서버 시작
const server = new YourMcpServer();
server.run();
```

### 7. Dockerfile

```dockerfile
FROM node:18-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 패키지 파일 복사
COPY package*.json tsconfig.json ./

# 의존성 설치 (빌드용 포함)
RUN npm ci

# 소스코드 복사
COPY src/ ./src/

# TypeScript 빌드
RUN npm run build

# 프로덕션 의존성만 남기기
RUN npm prune --production

# 비루트 사용자 생성
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

ENV PORT=8080
ENV NODE_ENV=production

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

CMD ["node", "dist/index.js"]
```

## 🚀 배포 과정

### 1. 빌드 및 테스트
```bash
npm install
npm run build
npm start  # 로컬 테스트
```

### 2. Docker 이미지 빌드
```bash
docker build -t gcr.io/your-project/your-mcp-server:latest .
```

### 3. Container Registry 푸시
```bash
docker push gcr.io/your-project/your-mcp-server:latest
```

### 4. Cloud Run 배포
```bash
gcloud run deploy your-mcp-server \
  --image gcr.io/your-project/your-mcp-server:latest \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1
```

## 🔗 Cursor 연동 설정

`.cursor/mcp.json`에 추가:

```json
{
  "mcpServers": {
    "your-server-name": {
      "url": "https://your-mcp-server-url.run.app/mcp"
    }
  }
}
```

## ⚠️ 주의사항

1. **반드시 Firebase-MCP와 동일한 SDK 버전 사용**
   - `@modelcontextprotocol/sdk: ^1.11.0`

2. **StreamableHTTPServerTransport 필수**
   - 단순 HTTP 요청/응답 방식은 세션 관리 불가
   - Claude와의 호환성을 위해 반드시 필요

3. **ESM 모듈 사용**
   - `"type": "module"` 설정 필수
   - import/export 문법 사용

4. **세션 관리**
   - 각 클라이언트별 독립적인 세션 유지
   - 메모리 누수 방지를 위한 세션 정리

## 🎯 성공 요인

1. **검증된 구조 활용**: Firebase-MCP의 성공적인 아키텍처 복사
2. **표준 준수**: MCP 공식 SDK와 권장사항 따름  
3. **Cloud Run 최적화**: 컨테이너 환경에 적합한 설계
4. **타입 안정성**: TypeScript로 런타임 오류 최소화

이 가이드를 따르면 Firebase-MCP와 동일한 수준의 안정성과 호환성을 가진 MCP 서버를 구축할 수 있습니다. 