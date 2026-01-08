import asyncio
from backend.agents.graph import app
from backend.agents.calculator import mcp_calculator

async def main():
    """Run the multi-agent financial analysis system with MCP"""
    
    print("🔌 Connecting to MCP Financial Calculator Server...")
    
    # Try to connect with timeout
    try:
        connected = await asyncio.wait_for(
            mcp_calculator.connect(),
            timeout=10.0
        )
        
        if not connected:
            print("⚠️  MCP server not available - continuing without calculations")
            print("   Start server in another terminal: python -m backend.agents.mcp_server\n")
    except asyncio.TimeoutError:
        print("⚠️  MCP connection timeout - continuing without calculations\n")
    except Exception as e:
        print(f"⚠️  MCP connection error: {e}")
        print("   Continuing without MCP calculations...\n")
    
    # Test query
    query = "Analyze Nvidia's profitability ratios and revenue growth from their latest 10-K data. Also get current stock price and recent news."
    print(f"{'='*80}")
    print(f"🚀 MULTI-AGENT FINANCIAL ANALYSIS")
    print(f"{'='*80}")
    print(f"\n📝 Query: {query}\n")
    
    initial_state = {
        "query": query,
        "messages": [],
        "rag_data": None,
        "stock_data": None, 
        "calc_data": None,
        "next_step": "start"
    }
    
    config = {"recursion_limit": 15}
    
    try:
        result = None
        async for output in app.astream(initial_state, config=config):
            for key, value in output.items():
                if key == "reporter":
                    result = value['messages'][0]
        
        if result:
            print(f"\n{'='*80}")
            print("📊 FINAL COMPREHENSIVE ANALYSIS")
            print(f"{'='*80}\n")
            print(result.content if hasattr(result, 'content') else result)
            print(f"\n{'='*80}\n")
    
    finally:
        # Clean up MCP connection
        try:
            await mcp_calculator.close()
            print("🔌 MCP connection closed")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())