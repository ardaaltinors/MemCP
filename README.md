<div align="center">
  <h1>MemCP - Portable Memory for AI</h1>
  <p><i>Give your AI assistant long-term memory that persists across conversations and platforms</i></p>
</div>

---

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

## Quick Start

### Cloud-Hosted Version (Recommended)

Get started immediately with our hosted MCP server:

**🌐 Production URL**: https://mcp.altinors.com/

1. Sign up for an account at the web interface
2. Get your API key from the dashboard
3. Configure your AI assistant to use the MCP endpoint
4. Start chatting with persistent memory

### Run Locally

Want to run MemCP on your own machine? It's easy!

- For detailed setup instructions, development tips, and troubleshooting, see [RUNNING_LOCALLY.md](docs/RUNNING_LOCALLY.md).

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

Configure your AI assistant to connect to the MCP server:
- **Cloud**: https://mcp.altinors.com/
- **Local**: http://localhost:4200

Use the API key from your dashboard for authentication. For local setup configuration details, see [RUNNING_LOCALLY.md](docs/RUNNING_LOCALLY.md).

## Use Casesn

- **Personal AI Assistant**: Give your AI assistant long-term memory about your preferences and history
- **Customer Support**: Maintain context across multiple support interactions
- **Knowledge Management**: Build a personal knowledge graph (your second brain) accessible by AI
- **Cross-Platform Memory**: Use the same memory across different AI tools and platforms

## Contributing

We welcome contributions! Whether it's bug fixes, new features, or documentation improvements, feel free to:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built with ❤️ to give AI assistants the memory they deserve.