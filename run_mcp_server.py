"""
Runner script for the FastMCP server
Can be used to test the MCP server independently
"""
import sys
import uvicorn
from mcp_server import mcp

def main():
    """
    Start the FastMCP server
    """
    print("🚀 Starting FastMCP Financial Tools Server...")
    print("📊 Available tools:")
    
    # List available tools
    for tool_name in dir(mcp):
        if not tool_name.startswith('_'):
            print(f"   - {tool_name}")
    
    print("\n🌐 Server starting on http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Run the MCP server
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()