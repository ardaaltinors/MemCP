export const env = {
  backendUrl: (import.meta as any).env?.PUBLIC_BACKEND_URL || 'http://localhost:8000',
  mcpUrl: (import.meta as any).env?.PUBLIC_MCP_URL || 'https://mcp.altinors.com/mcp',
};

