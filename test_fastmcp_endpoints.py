"""
Test what endpoints FastMCP actually exposes
"""
import httpx
import asyncio

async def test_endpoints():
    """Test various FastMCP endpoints"""
    client = httpx.AsyncClient(timeout=10.0)
    base_url = "http://localhost:8000"
    
    print("🔍 Testing FastMCP endpoints...\n")
    
    # Test endpoints
    endpoints = [
        "/",
        "/sse",
        "/health",
        "/tools",
        "/tools/calculate_growth_rate",
        "/message",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"Testing GET {endpoint}...")
            response = await client.get(f"{base_url}{endpoint}")
            print(f"  ✅ Status: {response.status_code}")
            print(f"  📄 Response: {response.text[:200]}\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
    
    # Try POST to SSE with a tool call
    print("\nTrying POST to /sse with tool call...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "calculate_growth_rate",
                "arguments": {
                    "current_value": 120.0,
                    "previous_value": 100.0,
                    "periods": 1
                }
            }
        }
        response = await client.post(
            f"{base_url}/sse",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"  ✅ Status: {response.status_code}")
        print(f"  📄 Response: {response.text}\n")
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
    
    await client.aclose()

if __name__ == "__main__":
    print("Make sure MCP server is running: python -m backend.agents.mcp_server\n")
    asyncio.run(test_endpoints())