"""
Script to start the MCP server as a background process.
This can be run independently or from the Streamlit UI.
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

if __name__ == "__main__":
    from mcp_server.server import mcp
    
    print("=" * 80)
    print("🚀 Starting Financial Calculator MCP Server")
    print("=" * 80)
    print("\n📡 Server Configuration:")
    print("   - Protocol: HTTP")
    print("   - Host: localhost")
    print("   - Port: 8000")
    print("\n📊 Available Tools:")
    print("   - calculate_liquidity_ratios")
    print("   - calculate_leverage_ratios")
    print("   - calculate_all_ratios")
    print("\n" + "=" * 80)
    print("✅ Server is ready to accept connections...")
    print("=" * 80 + "\n")
    
    # Run server on HTTP
    mcp.run(transport="http", port=8000)
