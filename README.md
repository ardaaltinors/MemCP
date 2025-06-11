---
<div align="center">
  <h1>🚧 <span style="color:#ffd700">MemCP</span> — *Work in Progress*</h1>
  <p><i>Next-gen portable memory for AI assistants. Join the journey!</i></p>
</div>
---

# 🚧🚧🚧 MemCP — Work In Progress 🚧🚧🚧

# MemCP - Portable Memory for AI

A powerful memory management system for AI assistants that implements the Model Context Protocol (MCP), enabling persistent context and knowledge across conversations and different AI providers.

## Overview

Memory MCP Server solves a fundamental limitation of AI assistants - the inability to remember information between conversations. It provides a centralized memory service that any MCP-compatible AI assistant can connect to, allowing them to store facts, build user profiles, and retrieve relevant context seamlessly.

## Key Features

- **Persistent AI Memory**: Store and retrieve information across multiple conversations and AI platforms
- **Semantic Search**: Find related memories using vector embeddings and similarity search
- **User Profile Synthesis**: Automatically build comprehensive user profiles from conversation history
- **Visual Memory Graph**: Interactive visualization of your AI's knowledge as a connected graph
- **Multi-User Support**: Secure authentication with isolated memory spaces for each user
- **MCP Protocol**: Industry-standard protocol for AI tool integration

## How It Works

1. **Connect Your AI**: Configure your AI assistant (Claude, etc.) to use the MCP server
2. **Automatic Memory Creation**: As you chat, the AI automatically stores important information
3. **Intelligent Retrieval**: The AI queries relevant memories to provide contextual responses
4. **Visual Management**: Use the web dashboard to view, edit, and organize your memories

# Quick Start with Cloud 

We provide a easy to use MCP endpoint with hosted version.

## Self Hosted Version

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/ardaaltinors/memory-mcp.git
cd memory-mcp

# Start all services
docker-compose up

# Access the services:
# - Web Interface: http://localhost
# - API: http://localhost:8000
# - MCP Server: http://localhost:4200
```

### Manual Installation

```bash
# Backend setup
uv install
alembic upgrade head
uv run python main.py

# Frontend setup
cd frontend
npm install
npm run dev
```

## MCP Tools Available

The server provides three core tools for AI assistants:

- `remember_fact`: Store specific facts or information
- `record_and_get_context`: Process messages and retrieve user context
- `get_related_memory`: Search for semantically related memories

## Architecture

- **Backend**: FastAPI + FastMCP dual-server architecture
- **Storage**: PostgreSQL for structured data, Qdrant for vector search
- **Processing**: Celery + RabbitMQ for background tasks
- **AI**: Google Gemini for profile synthesis
- **Frontend**: Astro + React with D3.js visualization

## Configuration

1. Create a `.env` file with required environment variables (see `.env.example`)
2. Configure your AI assistant to connect to the MCP server at `http://localhost:4200`
3. Use the API key from your user dashboard for authentication

## Use Cases

- **Personal AI Assistant**: Give your AI assistant long-term memory about your preferences and history
- **Customer Support**: Maintain context across multiple support interactions
- **Knowledge Management**: Build a personal knowledge graph (your second brain) accessible by AI
- **Cross-Platform Memory**: Use the same memory across different AI tools and platforms

## Contributing

We welcome contributions! Please see our contributing guidelines for more information.

## License



---

Built with ❤️ to give AI assistants the memory they deserve.