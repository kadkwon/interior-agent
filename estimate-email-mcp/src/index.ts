#!/usr/bin/env node

/**
 * Estimate Email MCP Server
 *
 * This server implements the Model Context Protocol (MCP) for estimate email services.
 * It provides tools for sending estimate emails through Cloud Functions.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import { logger } from './utils/logger.js';
import config from './config.js';
import { initializeTransport } from './transports/index.js';

/**
 * Main server class that implements the MCP protocol for estimate email services.
 */
class EstimateEmailMcpServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: config.name,
        version: config.version,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();

    // Set up error handling and graceful shutdown
    this.server.onerror = () => {};
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupToolHandlers(): void {
    // Register available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'send_estimate_email',
          description: '견적서를 이메일로 전송합니다',
          inputSchema: {
            type: 'object',
            properties: {
              email: {
                type: 'string',
                description: '수신자 이메일 주소',
              },
              address: {
                type: 'string',
                description: '견적서 주소',
              },
              process_data: {
                type: 'array',
                description: '공정 데이터 리스트',
              },
              notes: {
                type: 'object',
                description: '견적서 메모 (선택사항)',
              },
              hidden_processes: {
                type: 'object',
                description: '숨김 공정 설정 (선택사항)',
              },
              corporate_profit: {
                type: 'object',
                description: '기업이윤 설정 (선택사항)',
              },
              subject: {
                type: 'string',
                description: '이메일 제목 (선택사항)',
              },
              template_content: {
                type: 'string',
                description: '이메일 본문 (선택사항)',
              },
            },
            required: ['email', 'address', 'process_data'],
          },
        },
        {
          name: 'test_connection',
          description: 'MCP 서버 연결 테스트',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        {
          name: 'get_server_info',
          description: '서버 정보 조회',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        const { name, arguments: args } = request.params;

        switch (name) {
          case 'send_estimate_email':
            return await this.sendEstimateEmail(args);

          case 'test_connection':
            return {
              content: [
                {
                  type: 'text',
                  text: '✅ Estimate Email MCP 서버가 정상 작동 중입니다!',
                },
              ],
            };

          case 'get_server_info':
            const info = {
              서버명: 'Estimate Email MCP Server',
              환경: process.env.PORT ? '클라우드런' : '로컬',
              포트: config.port,
              호스트: config.host,
              'Cloud Functions URL': config.cloudFunctionsUrl,
              '지원 도구': ['send_estimate_email', 'test_connection', 'get_server_info'],
            };
            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(info, null, 2),
                },
              ],
            };

          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        logger.error('Error in tool call:', errorMessage);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ error: errorMessage }),
            },
          ],
        };
      }
    });
  }

  private async sendEstimateEmail(args: any): Promise<any> {
    try {
      logger.info(`📧 이메일 전송 시작: ${args.email} → ${args.address}`);

      // 기본값 설정
      const notes = args.notes || {};
      const hiddenProcesses = args.hidden_processes || {};
      const corporateProfit = args.corporate_profit || config.defaultCorporateProfit;
      const subject = args.subject || config.emailTemplate.subject.replace('{address}', args.address);

      // 견적 금액 계산
      const basicTotal = this.calculateBasicTotal(args.process_data);
      const corporateProfitAmount = this.calculateCorporateProfitAmount(args.process_data, corporateProfit);
      const totalAmount = basicTotal + corporateProfitAmount;
      const corporateProfitPercentage = corporateProfit.percentage || 10;

      // 공정 상세 정보 생성
      const processDetails = this.generateProcessDetails(args.process_data, hiddenProcesses);

      const templateContent = args.template_content || config.emailTemplate.content
        .replace('{address}', args.address)
        .replace('{process_details}', processDetails)
        .replace('{basic_total:,}', basicTotal.toLocaleString())
        .replace('{corporate_profit_percentage}', corporateProfitPercentage.toString())
        .replace('{corporate_profit_amount:,}', corporateProfitAmount.toLocaleString())
        .replace('{total_amount:,}', totalAmount.toLocaleString());

      // Cloud Functions API 호출을 위한 데이터 준비
      const payload = {
        to: args.email,
        subject: subject,
        html: templateContent,
        estimateData: {
          selectedAddress: args.address,
          processData: args.process_data,
          notes: notes,
          hiddenProcesses: hiddenProcesses,
          corporateProfit: corporateProfit,
          isCorporateProfitVisible: true,
          calculateCorporateProfitAmount: corporateProfitAmount,
        },
      };

      logger.debug(`🔄 Cloud Functions API 호출 준비: ${config.cloudFunctionsUrl}`);

      // HTTP 요청으로 Cloud Functions 직접 호출
      const response = await axios.post(config.cloudFunctionsUrl, payload, {
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        timeout: config.emailTimeout,
      });

      logger.debug(`📨 Cloud Functions 응답 상태: ${response.status}`);

      if (response.status === 200) {
        logger.info(`✅ 이메일 전송 성공: ${args.email}`);
        return {
          content: [
            {
              type: 'text',
              text: `✅ 견적서가 ${args.email}로 성공적으로 전송되었습니다!\n\n📋 전송 정보:\n- 수신자: ${args.email}\n- 주소: ${args.address}\n- 제목: ${subject}\n- 공정 개수: ${args.process_data.length}개\n- 기업이윤: ${corporateProfitAmount.toLocaleString()}원`,
            },
          ],
        };
      } else {
        throw new Error(`Cloud Functions 호출 실패: HTTP ${response.status}`);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      logger.error(`❌ 이메일 전송 실패: ${errorMessage}`);
      return {
        content: [
          {
            type: 'text',
            text: `❌ 이메일 전송 실패: ${errorMessage}`,
          },
        ],
      };
    }
  }

  private generateProcessDetails(processData: any[], hiddenProcesses: any = {}): string {
    const details: string[] = [];

    for (const process of processData) {
      const processName = process.processName || '알 수 없는 공정';

      // 숨김 공정 처리
      if (hiddenProcesses[processName]) {
        continue;
      }

      try {
        const unitPrice = parseFloat(process.unitPrice || '0');
        const quantity = parseFloat(process.quantity || '0');
        const totalPrice = unitPrice * quantity;

        const formattedTotal = totalPrice > 0 ? `${totalPrice.toLocaleString()}원` : '가격 문의';
        details.push(`▶ ${processName}: ${formattedTotal}`);
      } catch (error) {
        logger.warn(`공정 '${processName}' 처리 중 오류: ${error}`);
        details.push(`▶ ${processName}: 가격 문의`);
      }
    }

    return details.length > 0 ? details.join('\n\n') : '공정 정보 없음';
  }

  private calculateBasicTotal(processData: any[]): number {
    let total = 0;
    for (const process of processData) {
      try {
        const unitPrice = parseFloat(process.unitPrice || '0');
        const quantity = parseFloat(process.quantity || '0');
        total += unitPrice * quantity;
      } catch (error) {
        // 잘못된 데이터는 무시
      }
    }
    return Math.round(total);
  }

  private calculateCorporateProfitAmount(processData: any[], corporateProfit: any): number {
    const basicTotal = this.calculateBasicTotal(processData);
    const profitType = corporateProfit.type || 'percentage';

    if (profitType === 'percentage') {
      const percentage = corporateProfit.percentage || 10;
      return Math.round(basicTotal * (percentage / 100));
    } else if (profitType === 'fixed') {
      return Math.round(corporateProfit.amount || 0);
    } else {
      return Math.round(basicTotal * 0.1); // 기본 10%
    }
  }

  /**
   * Starts the MCP server using the configured transport.
   */
  async run(): Promise<void> {
    logger.info(`Starting Estimate Email MCP server v${config.version} with ${config.transport} transport`);
    await initializeTransport(this.server, config);
  }
}

// Create and start the server
const server = new EstimateEmailMcpServer();
server.run(); 