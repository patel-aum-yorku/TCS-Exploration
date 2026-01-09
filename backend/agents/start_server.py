"""
Startup script for the MCP HTTP server.
Run this before starting the agent system.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mcp_server.server import mcp

if __name__ == "__main__":
    print("🚀 Starting Financial Calculator MCP Server on http://localhost:8000")
    print("📊 Available tools:")
    print("   - calculate_liquidity_ratios")
    print("   - calculate_leverage_ratios")
    print("   - calculate_all_ratios")
    print("\nServer is ready to accept connections...\n")
    
    mcp.run(transport="http", port=8000)