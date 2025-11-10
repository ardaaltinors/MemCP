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

# Database Configuration
# Validate individual database credentials and build connection string

# Database Host
DB_HOST = os.getenv("DB_HOST", "localhost")
if not DB_HOST or DB_HOST.strip() == "":
    raise ConfigurationError(
        message="Database host is required. Please set DB_HOST environment variable.",
        config_key="DB_HOST",
        expected_type="string"
    )

# Database Port
DB_PORT_STR = os.getenv("DB_PORT", "5432")
if not DB_PORT_STR or DB_PORT_STR.strip() == "":
    raise ConfigurationError(
        message="Database port is required. Please set DB_PORT environment variable.",
        config_key="DB_PORT",
        expected_type="integer"
    )

try:
    DB_PORT = int(DB_PORT_STR.strip())
    if not (1 <= DB_PORT <= 65535):
        raise ValueError("Port must be between 1 and 65535")
except ValueError as e:
    raise ConfigurationError(
        message=f"Database port must be a valid integer between 1-65535. Got: {DB_PORT_STR}",
        config_key="DB_PORT",
        expected_type="integer",
        actual_value=DB_PORT_STR
    )

# Database Name
DB_NAME = os.getenv("DB_NAME")
if not DB_NAME or DB_NAME.strip() == "":
    raise ConfigurationError(
        message="Database name is required. Please set DB_NAME environment variable.",
        config_key="DB_NAME",
        expected_type="string"
    )

# Database User
DB_USER = os.getenv("DB_USER")
if not DB_USER or DB_USER.strip() == "":
    raise ConfigurationError(
        message="Database user is required. Please set DB_USER environment variable.",
        config_key="DB_USER",
        expected_type="string"
    )

# Database Password
DB_PASSWORD = os.getenv("DB_PASSWORD")
if not DB_PASSWORD or DB_PASSWORD.strip() == "":
    raise ConfigurationError(
        message="Database password is required. Please set DB_PASSWORD environment variable.",
        config_key="DB_PASSWORD",
        expected_type="string"
    )

# Build Database Connection URL
ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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