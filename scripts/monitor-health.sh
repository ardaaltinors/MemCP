#!/bin/bash

# =============================================================================
# Health Monitoring Script for Memory MCP
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL="${FRONTEND_URL:-http://localhost}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
MCP_URL="${MCP_URL:-http://localhost:4200}"
LOG_FILE="/tmp/memory-mcp-health.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    local endpoint=${3:-/health}
    
    echo -n "Checking $name... "
    
    if curl -sf --connect-timeout 5 --max-time 10 "${url}${endpoint}" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        log "ERROR: $name is not responding at ${url}${endpoint}"
        return 1
    fi
}

# Function to check container resources
check_container_resources() {
    local container=$1
    
    echo -e "\n${YELLOW}Container: $container${NC}"
    
    # Check if container exists
    if ! docker ps --format "table {{.Names}}" | grep -q "^${container}$"; then
        echo -e "${RED}Container not running${NC}"
        return 1
    fi
    
    # Get container stats
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" "$container"
    
    # Check container logs for errors
    echo "Recent errors in logs:"
    docker logs "$container" 2>&1 | grep -i "error\|exception\|critical" | tail -5 || echo "No recent errors"
}

# Function to check nginx status
check_nginx_status() {
    local container=$1
    
    echo -e "\n${YELLOW}Nginx Status:${NC}"
    
    # Check nginx process
    docker exec "$container" ps aux | grep nginx || echo "Nginx process not found"
    
    # Check nginx config
    docker exec "$container" nginx -t 2>&1 || echo "Nginx config test failed"
    
    # Check active connections
    echo "Active connections:"
    docker exec "$container" sh -c 'netstat -an | grep :80 | wc -l' || echo "Failed to count connections"
}

# Function to check database connections
check_db_connections() {
    echo -e "\n${YELLOW}Database Connections:${NC}"
    
    docker exec memory-mcp-postgres psql -U memory_user -d memory_mcp -c "
    SELECT 
        state,
        COUNT(*) as count,
        MAX(state_change) as last_change
    FROM pg_stat_activity
    WHERE datname = 'memory_mcp'
    GROUP BY state
    ORDER BY count DESC;" 2>/dev/null || echo "Failed to check DB connections"
}

# Main monitoring loop
main() {
    log "Starting Memory MCP health monitoring..."
    
    while true; do
        clear
        echo "=== Memory MCP Health Check ==="
        echo "Time: $(date)"
        echo "================================"
        
        # Check services
        echo -e "\n${YELLOW}Service Health:${NC}"
        check_service "Frontend" "$FRONTEND_URL" "/"
        check_service "Backend API" "$BACKEND_URL" "/api/v1/health"
        check_service "MCP Server" "$MCP_URL" "/health"
        
        # Check container resources
        echo -e "\n${YELLOW}Container Resources:${NC}"
        for container in memory-mcp-frontend memory-mcp-server memory-mcp-postgres memory-mcp-qdrant; do
            check_container_resources "$container" || true
        done
        
        # Check nginx specifically
        check_nginx_status "memory-mcp-frontend"
        
        # Check database connections
        check_db_connections
        
        # Check disk usage
        echo -e "\n${YELLOW}Disk Usage:${NC}"
        docker system df
        
        echo -e "\n${YELLOW}Docker Volume Usage:${NC}"
        docker volume ls --format "table {{.Name}}\t{{.Size}}" | grep memory-mcp || true
        
        # Wait before next check
        echo -e "\n${GREEN}Next check in 30 seconds... (Ctrl+C to exit)${NC}"
        sleep 30
    done
}

# Run main function
main