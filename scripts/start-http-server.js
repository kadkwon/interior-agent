#!/usr/bin/env node

/**
 * Firebase MCP HTTP Server Startup Script
 * 
 * This script starts the Firebase MCP server in HTTP mode.
 * It configures the server with the provided environment variables
 * and starts listening for HTTP connections.
 */

import { spawn } from 'child_process';
import { resolve } from 'path';

// Default configuration
const config = {
  port: process.env.PORT || process.env.MCP_HTTP_PORT || '8080',
  host: process.env.MCP_HTTP_HOST || '0.0.0.0',
  path: process.env.MCP_HTTP_PATH || '/mcp'
};

// Start the server
console.log(`Starting Firebase MCP HTTP server on ${config.host}:${config.port}${config.path}`);

// Set environment variables for HTTP transport
process.env.MCP_TRANSPORT = 'http';
process.env.MCP_HTTP_PORT = config.port;
process.env.MCP_HTTP_HOST = config.host;
process.env.MCP_HTTP_PATH = config.path;

// Start the server process
const serverProcess = spawn('node', ['dist/index.js'], {
  stdio: 'inherit',
  env: process.env
});

// Handle process events
serverProcess.on('error', (err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});

serverProcess.on('exit', (code) => {
  if (code !== 0) {
    console.error(`Server exited with code ${code}`);
    process.exit(code);
  }
}); 