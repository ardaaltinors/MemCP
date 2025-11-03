# Running MemCP Locally

This guide will help you run MemCP on your local machine for development or self-hosting.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- UV (Python package manager)

## Quick Start with Docker

The easiest way to run MemCP locally is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/ardaaltinors/MemCP.git
cd MemCP

# Start infrastructure services (PostgreSQL, RabbitMQ, Qdrant)
docker-compose -f docker-compose-dev.yml up
```

This will start:
- PostgreSQL (database)
- RabbitMQ (message broker)
- Qdrant (vector database)
- Redis (Celery result backend)

## Running the Backend

In a separate terminal, start the backend servers:

```bash
# Install dependencies
uv install

# Run database migrations
alembic upgrade head

# Start FastAPI and MCP servers
uv run python main.py
```

This starts two servers:
- **FastAPI REST API**: http://localhost:8000
- **MCP Server**: http://localhost:4200

## Running the Celery Worker

In another terminal, start the Celery worker for background tasks:

```bash
uv run celery -A src.celery_app worker --loglevel=info
```

## Running the Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at the URL shown in the terminal (typically http://localhost:4321).

## Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your configuration:
   ```env
   # Database
   DB_HOST=localhost
   DB_NAME=memory_mcp
   DB_USER=postgres
   DB_PASSWORD=postgres

   # API Keys
   GOOGLE_API_KEY=your-google-api-key
   OPENAI_API_KEY=your-openai-api-key

   # Authentication
   AUTH_SECRET_KEY=your-secret-key

   # MCP Server
   MCP_SERVER_HOST=127.0.0.1
   MCP_SERVER_PORT=4200
   ```

## Production Deployment with Docker

For a production deployment, use the main docker-compose file:

```bash
docker-compose up -d
```

This will start all services including the frontend with Nginx:
- **Web Interface**: http://localhost:80
- **Backend API**: http://localhost:8000
- **MCP Server**: http://localhost:4200

## Service URLs

When running locally, you can access:

- **Frontend**: http://localhost:4321 (dev)
- **API Documentation**: http://localhost:8000/docs
- **MCP Server**: http://localhost:4200
- **Qdrant Dashboard**: http://localhost:6334
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## Health Check

You can verify that all services are running correctly using the health endpoint:

```bash
curl http://localhost:8000/health
```

This returns the status of all critical services:

```json
{
  "status": "healthy",
  "services": {
    "postgres": {
      "status": "healthy",
      "details": "Connection successful"
    },
    "qdrant": {
      "status": "healthy",
      "details": "Connection successful, able to list collections"
    },
    "rabbitmq": {
      "status": "healthy",
      "details": "Broker connection successful"
    },
    "redis": {
      "status": "healthy",
      "details": "Connection successful, 0 keys in DB"
    },
    "celery": {
      "status": "healthy",
      "details": "1 worker(s) online",
      "workers": [
        {
          "name": "celery@hostname",
          "active_tasks": 0,
          "status": "online"
        }
      ]
    }
  },
  "timestamp": "2025-11-03T15:22:08.046425+00:00",
  "uptime": {
    "seconds": 1065.255657,
    "formatted": "17m 45s"
  }
}
```

If any service shows an unhealthy status, check the logs and refer to the troubleshooting section below.

## Troubleshooting

### Database Connection Issues
Make sure PostgreSQL is running and the credentials in `.env` match your setup.

### Celery Worker Not Processing Tasks
Check that RabbitMQ is running and accessible. Verify the Celery worker logs for errors.

### Vector Search Not Working
Ensure Qdrant is running on port 6333. Check the Qdrant dashboard at http://localhost:6334.

### Frontend Can't Connect to Backend
Make sure the backend is running on port 8000 and check CORS settings if needed.

## Development Tips

- Use `uv add <package>` to add new Python dependencies (not pip)
- Run `alembic revision --autogenerate -m "description"` after model changes
- Frontend has hot-reload enabled in dev mode
- Check logs in each terminal for debugging

## Next Steps

- Configure your AI assistant to connect to `http://localhost:4200`
- Create an account through the web interface
- Get your API key from the dashboard
- Start using the MCP tools with your AI assistant

For more information, see the main [README.md](../README.md) for development guidelines.
