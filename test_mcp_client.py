#!/usr/bin/env python3
"""
Test the MCP client integration with agents
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent / "backend")
sys.path.insert(0, backend_path)

from agents.mcp_client import MCPClient

async def test_mcp_client():
    """Test MCP client functionality"""
    
    print("Testing MCP Client...")
    print("=" * 60)
    
    client = MCPClient()
    
    # Initialize session explicitly
    print("\n0. Initializing session...")
    session_id = await client.initialize_session()
    print(f"Session ID: {session_id}")
    
    # Test sample RAG data
    sample_rag_data = """
    NVIDIA Corporation
    Consolidated Balance Sheet (in millions)
    
    Current Assets: $15,500
    Inventory: $2,100
    Current Liabilities: $6,000
    Total Debt: $4,500
    Total Assets: $45,000
    Shareholders' Equity: $38,000
    """
    
    print("\n1. Testing calculate_all_ratios...")
    try:
        result = await client.calculate_all_ratios(sample_rag_data)
        print("Result:")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2. Testing list_tools...")
    try:
        tools = await client.list_tools()
        print("Tools:")
        print(tools)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    await client.close()
    print("\n" + "=" * 60)
    print("✅ MCP Client test complete!")

if __name__ == "__main__":
    asyncio.run(test_mcp_client())
