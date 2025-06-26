/**
 * HTTP Transport for Estimate Email MCP Server
 */

import express from 'express';
import cors from 'cors';
import { randomUUID } from 'node:crypto';
import type { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { isInitializeRequest } from '@modelcontextprotocol/sdk/types.js';
import { logger } from '../utils/logger.js';
import type { ServerConfig } from '../config.js';

/**
 * Initialize HTTP transport
 */
export async function initializeHttpTransport(server: Server, config: ServerConfig): Promise<void> {
  const app = express();
  
  // Enable CORS
  app.use(cors());
  app.use(express.json());

  // Map to store transports by session ID
  const transports: { [sessionId: string]: StreamableHTTPServerTransport } = {};

  // Health check endpoint
  app.get('/', (req, res) => {
    res.json({
      status: 'healthy',
      service: config.name,
      version: config.version,
      transport: 'http'
    });
  });

  // Handle POST requests for client-to-server communication
  app.post('/mcp', async (req, res) => {
    try {
      // Check for existing session ID
      const sessionId = req.headers['mcp-session-id'] as string | undefined;
      let transport: StreamableHTTPServerTransport;

      if (sessionId && transports[sessionId]) {
        // Reuse existing transport
        transport = transports[sessionId];
      } else if (!sessionId && isInitializeRequest(req.body)) {
        // New initialization request
        transport = new StreamableHTTPServerTransport({
          sessionIdGenerator: () => randomUUID(),
          onsessioninitialized: sessionId => {
            // Store the transport by session ID
            transports[sessionId] = transport;
            logger.debug(`Initialized new session: ${sessionId}`);
          },
        });

        // Clean up transport when closed
        transport.onclose = () => {
          if (transport.sessionId) {
            logger.debug(`Closing session: ${transport.sessionId}`);
            delete transports[transport.sessionId];
          }
        };

        // Connect to the MCP server
        await server.connect(transport);
      } else {
        // Invalid request
        logger.error('Invalid request: No valid session ID provided');
        res.status(400).json({
          jsonrpc: '2.0',
          error: {
            code: -32000,
            message: 'Bad Request: No valid session ID provided',
          },
          id: null,
        });
        return;
      }

      // Handle the request
      await transport.handleRequest(req, res, req.body);
    } catch (error) {
      logger.error('Error handling MCP request:', error);
      res.status(500).json({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Reusable handler for GET and DELETE requests
  const handleSessionRequest = async (
    req: express.Request,
    res: express.Response
  ): Promise<void> => {
    const sessionId = req.headers['mcp-session-id'] as string | undefined;
    if (!sessionId || !transports[sessionId]) {
      logger.error(`Invalid or missing session ID: ${sessionId}`);
      res.status(400).send('Invalid or missing session ID');
      return;
    }

    const transport = transports[sessionId];
    await transport.handleRequest(req, res);
  };

  // Handle GET requests for server-to-client notifications via SSE
  app.get('/mcp', handleSessionRequest);

  // Handle DELETE requests for session termination
  app.delete('/mcp', handleSessionRequest);

  // Start the HTTP server
  const serverInstance = app.listen(config.port, config.host, () => {
    logger.info(`HTTP transport listening on ${config.host}:${config.port}/mcp`);
  });

  // Handle server errors
  if (serverInstance && typeof serverInstance.on === 'function') {
    serverInstance.on('error', error => {
      logger.error('HTTP server error', error);
    });
  }

  // Handle graceful shutdown
  const sigintHandler = async (): Promise<void> => {
    logger.info('Shutting down HTTP server');
    if (serverInstance && typeof serverInstance.close === 'function') {
      serverInstance.close();
    }
  };

  // Add SIGINT handler
  const existingListeners = process.listenerCount('SIGINT');
  if (existingListeners < 10) {
    process.on('SIGINT', sigintHandler);
  }
} 