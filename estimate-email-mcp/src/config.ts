/**
 * Configuration for Estimate Email MCP Server
 */

import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

export interface ServerConfig {
  name: string;
  version: string;
  transport: 'http';
  port: number;
  host: string;
  cloudFunctionsUrl: string;
  emailTimeout: number;
  defaultCorporateProfit: {
    percentage: number;
    isVisible: boolean;
  };
  emailTemplate: {
    subject: string;
    content: string;
  };
}

const config: ServerConfig = {
  name: 'estimate-email-mcp',
  version: '1.0.0',
  transport: 'http',
  port: parseInt(process.env.PORT || '8080', 10),
  host: process.env.HOST || '0.0.0.0',
  cloudFunctionsUrl: process.env.CLOUD_FUNCTIONS_URL || 
    'https://us-central1-interior-one-click.cloudfunctions.net/sendEstimatePdfHttp',
  emailTimeout: parseInt(process.env.EMAIL_TIMEOUT || '30000', 10),
  defaultCorporateProfit: {
    percentage: parseInt(process.env.DEFAULT_CORPORATE_PROFIT_PERCENTAGE || '10', 10),
    isVisible: true,
  },
  emailTemplate: {
    subject: '인테리어 견적서 - {address}',
    content: `안녕하세요!

{address} 인테리어 견적서를 보내드립니다.

📋 견적 내역:
{process_details}

💰 견적 요약:
- 기본 공사비: {basic_total:,}원  
- 기업이윤 ({corporate_profit_percentage}%): {corporate_profit_amount:,}원
- 총 견적 금액: {total_amount:,}원

추가 문의사항이 있으시면 언제든지 연락주세요.

감사합니다.`
  }
};

export default config; 