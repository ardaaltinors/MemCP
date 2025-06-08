# =============================================================================
# Multi-stage Dockerfile for Astro Frontend
# Uses Node.js for building and nginx for serving
# =============================================================================

# Build stage
FROM node:lts AS build

WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for environment variables
ARG FRONTEND_URL=http://localhost:4321
ARG BACKEND_URL=http://localhost:8000

# Set environment variables for build
ENV FRONTEND_URL=${FRONTEND_URL}
ENV BACKEND_URL=${BACKEND_URL}

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine AS runtime

# Install bash for healthcheck
RUN apk add --no-cache bash

# Copy custom nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx cache directory
RUN mkdir -p /var/cache/nginx/client_temp

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 