/**
 * Transport Factory Module
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { initializeHttpTransport } from './http.js';
import type { ServerConfig } from '../config.js';
import { logger } from '../utils/logger.js';

/**
 * Initialize transport based on configuration
 */
export async function initializeTransport(server: Server, config: ServerConfig): Promise<void> {
  logger.info('Initializing HTTP transport');
  await initializeHttpTransport(server, config);
} 