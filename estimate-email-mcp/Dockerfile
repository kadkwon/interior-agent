# Estimate Email MCP Server - TypeScript Node.js
FROM node:18-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files first for better Docker caching
COPY package*.json tsconfig.json ./

# Install all dependencies (including devDependencies for build)
RUN npm ci

# Copy source code
COPY src/ ./src/

# Build TypeScript
RUN npm run build

# Remove devDependencies after build
RUN npm prune --production

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port 8080 (Cloud Run standard)
EXPOSE 8080

# Set environment variables for Cloud Run
ENV PORT=8080
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Start the server
CMD ["node", "dist/index.js"] 