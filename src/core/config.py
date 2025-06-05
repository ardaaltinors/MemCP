import os
from src.exceptions import ConfigurationError

# MCP Server Configuration
# MCP_SERVER_HOST: Address to bind the uvicorn server to
# - Local dev: "127.0.0.1" (localhost only)
# - Container: "0.0.0.0" (all interfaces)

# Validate MCP_SERVER_HOST
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
if not MCP_SERVER_HOST or MCP_SERVER_HOST.strip() == "":
    raise ConfigurationError(
        message="MCP Server Host is required. Please set MCP_SERVER_HOST environment variable.",
        config_key="MCP_SERVER_HOST",
        expected_type="string"
    )

# Validate and convert MCP_SERVER_PORT
MCP_SERVER_PORT_STR = os.getenv("MCP_SERVER_PORT", "4200")
if not MCP_SERVER_PORT_STR or MCP_SERVER_PORT_STR.strip() == "":
    raise ConfigurationError(
        message="MCP Server Port is required. Please set MCP_SERVER_PORT environment variable.",
        config_key="MCP_SERVER_PORT",
        expected_type="integer"
    )

try:
    MCP_SERVER_PORT = int(MCP_SERVER_PORT_STR.strip())
    if not (1 <= MCP_SERVER_PORT <= 65535):
        raise ValueError("Port must be between 1 and 65535")
except ValueError as e:
    raise ConfigurationError(
        message=f"MCP Server Port must be a valid integer between 1-65535. Got: {MCP_SERVER_PORT_STR}",
        config_key="MCP_SERVER_PORT",
        expected_type="integer",
        actual_value=MCP_SERVER_PORT_STR
    )
    
API_SERVER_PORT_STR = os.getenv("API_SERVER_PORT")
if not API_SERVER_PORT_STR or API_SERVER_PORT_STR.strip() == "":
    raise ConfigurationError(
        message="API Server Port is required for FastAPI. Please set API_SERVER_PORT environment variable.",
        config_key="API_SERVER_PORT",
        expected_type="integer"
    )

try:
    API_SERVER_PORT = int(API_SERVER_PORT_STR.strip())
    if not (1 <= API_SERVER_PORT <= 65535):
        raise ValueError("Port must be between 1 and 65535")
except ValueError as e:
    raise ConfigurationError(
        message=f"API Server Port must be a valid integer between 1-65535. Got: {API_SERVER_PORT_STR}",
        config_key="API_SERVER_PORT",
        expected_type="integer",
        actual_value=API_SERVER_PORT_STR
    )

# MCP_BASE_URL: External URL that clients use to connect
# - Local dev: http://127.0.0.1:4200
# - Production: https://mcp.altinors.com
# - Container: http://localhost:4200 or your domain
MCP_BASE_URL = os.getenv("MCP_BASE_URL")
if not MCP_BASE_URL or MCP_BASE_URL.strip() == "":
    raise ConfigurationError(
        message="MCP Base URL is required. Please set MCP_BASE_URL environment variable.",
        config_key="MCP_BASE_URL",
        expected_type="string"
    )

def get_mcp_connection_url(api_key: str) -> str:
    """
    Generate the private MCP connection URL for a given API key.
    
    Args:
        api_key: The user's API key
        
    Returns:
        The complete MCP connection URL
    """
    if not api_key:
        raise ConfigurationError(
            message="API key is required to generate connection URL",
            config_key="api_key",
            expected_type="string"
        )
    
    return f"{MCP_BASE_URL}/mcp/{api_key}" 