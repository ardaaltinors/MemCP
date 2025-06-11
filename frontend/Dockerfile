# =============================================================================
# Improved Multi-stage Dockerfile with Better Health Checks
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

# Install wget for health checks (Alpine-compatible)
RUN apk add --no-cache wget

# Copy custom nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx directories
RUN mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/log/nginx && \
    touch /var/log/nginx/access.log && \
    touch /var/log/nginx/error.log

# Create custom 50x.html error page
RUN echo '<!DOCTYPE html><html><head><title>Service Temporarily Unavailable</title></head><body><h1>Service Temporarily Unavailable</h1><p>Please try again later.</p></body></html>' > /usr/share/nginx/html/50x.html

# Set proper permissions
RUN chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chmod -R 755 /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check using wget (Alpine-compatible)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]