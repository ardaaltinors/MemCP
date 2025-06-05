# Memory MCP Server

MCP memory management server.

---

## Development

1. Setting host and port for different environments:
   
   **Local Development:**
   ```bash
   MCP_SERVER_HOST=127.0.0.1
   MCP_SERVER_PORT=4200
   MCP_BASE_URL=http://127.0.0.1:4200
   ```
   
   **Container/Docker:**
   ```bash
   MCP_SERVER_HOST=0.0.0.0
   MCP_SERVER_PORT=4200
   MCP_BASE_URL=http://localhost:4200
   ```
   
   **Production:**
   ```bash
   MCP_SERVER_HOST=0.0.0.0
   MCP_SERVER_PORT=4200
   MCP_BASE_URL=https://mcp.altinors.com
   ```

2. Install dependencies:
   ```bash
   uv install
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. Start the application:
   ```bash
   uv run python main.py
   ```

## Services

- **FastAPI Server**: http://localhost:8000
- **MCP Server**: http://localhost:4200/mcp/
- **Qdrant**: http://localhost:6333
- **PostgreSQL**: localhost:5432
