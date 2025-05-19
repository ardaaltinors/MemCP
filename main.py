from dotenv import load_dotenv

load_dotenv()

from src.server import mcp

def main():
    print("Starting MCP server...")
    
    try:
        mcp.run(
            transport="streamable-http",
            host="127.0.0.1",
            port=4200,
            path="/mcp",
            log_level="debug",
        )
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Shutting down server...")


if __name__ == "__main__":
    main()
