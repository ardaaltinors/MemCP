# Memory MCP Server

MCP memory management server.

---

## Development

1. Set environment variables
    - Check .env.example

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
