#!/usr/bin/env python3
"""
Test WITHOUT session ID parameter - maybe FastMCP HTTP doesn't need it?
"""
import httpx
import json

def test_no_session():
    """Test MCP without explicit session ID"""
    
    print("Testing MCP Without Session Parameter...")
    print("=" * 60)
    
    client = httpx.Client(timeout=10.0)
    
    # Step 1: Initialize (no session ID)
    print("\n1. INITIALIZE (no sessionId param)...")
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = client.post(
        "http://localhost:8000/mcp",
        json=init_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
    )
    
    print(f"Status: {response.status_code}")
    session_id = response.headers.get('mcp-session-id')
    print(f"Session ID from header: {session_id}")
    print(f"Cookies: {client.cookies}")
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text[:200]}")
        return
    
    # Step 2: Initialized notification
    print("\n2. INITIALIZED NOTIFICATION (no param, relying on cookies)...")
    notify_payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    response2 = client.post(
        "http://localhost:8000/mcp",
        json=notify_payload,
        headers={
            "Content-Type": "application/json"
        }
    )
    
    print(f"Status: {response2.status_code}")
    print(f"Response: {response2.text[:200]}")
    
    # Step 3: List tools
    print("\n3. LIST TOOLS (no param, relying on cookies)...")
    list_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response3 = client.post(
        "http://localhost:8000/mcp",
        json=list_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
    )
    
    print(f"Status: {response3.status_code}")
    
    if response3.status_code == 200:
        print("✅ Tools list successful!")
        for line in response3.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                tools = data.get('result', {}).get('tools', [])
                print(f"Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool['name']}")
    else:
        print(f"❌ Failed: {response3.text[:200]}")
    
    # Step 4: Call tool
    print("\n4. CALL TOOL (no param)...")
    call_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "calculate_all_ratios",
            "arguments": {
                "rag_data": "Current Assets: $15,500\nCurrent Liabilities: $6,000\nInventory: $2,100\nTotal Debt: $4,500\nTotal Assets: $45,000\nShareholders' Equity: $38,000"
            }
        }
    }
    
    response4 = client.post(
        "http://localhost:8000/mcp",
        json=call_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
    )
    
    print(f"Status: {response4.status_code}")
    
    if response4.status_code == 200:
        print("✅ Tool call successful!")
        print(f"Response: {response4.text[:500]}")
    else:
        print(f"❌ Failed: {response4.text[:200]}")
    
    client.close()

if __name__ == "__main__":
    test_no_session()
