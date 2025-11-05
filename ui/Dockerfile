# Multi-stage build for HK Immigration Assistant UI
FROM node:22-alpine AS builder

# Set working directory
WORKDIR /app

# Build arguments for environment variables
ARG AZURE_OPENAI_API_KEY
ARG AZURE_OPENAI_ENDPOINT
ARG AZURE_OPENAI_DEPLOYMENT
ARG AZURE_OPENAI_API_VERSION
ARG REMOTE_ACTION_URL

# Set environment variables for build
ENV AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
ENV AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
ENV AZURE_OPENAI_DEPLOYMENT=${AZURE_OPENAI_DEPLOYMENT}
ENV AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION}
ENV REMOTE_ACTION_URL=${REMOTE_ACTION_URL}

# Install pnpm
RUN npm install -g pnpm@latest

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Build application
RUN pnpm run build

# Production stage
FROM node:22-alpine

# Set working directory
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm@latest

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install production dependencies only
RUN pnpm install --prod --frozen-lockfile

# Copy built application from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.mjs ./

# Create non-root user (use system-assigned IDs to avoid conflicts)
RUN addgroup -S appuser && \
    adduser -S -G appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start application
CMD ["pnpm", "start"]
