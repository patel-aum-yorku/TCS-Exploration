#!/usr/bin/env python3
"""
Test using mcp-session-id as REQUEST header
"""
import httpx
import json

def test_session_header():
    """Test MCP with session ID in request header"""
    
    print("Testing MCP With Session ID as Request Header...")
    print("=" * 60)
    
    # Step 1: Initialize
    print("\n1. INITIALIZE...")
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
    
    response = httpx.post(
        "http://localhost:8000/mcp",
        json=init_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        },
        timeout=10.0
    )
    
    print(f"Status: {response.status_code}")
    session_id = response.headers.get('mcp-session-id')
    print(f"Session ID from response header: {session_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text[:200]}")
        return
    
    print("✅ Initialize successful")
    
    # Step 2: Initialized notification - send session ID as REQUEST header
    print("\n2. INITIALIZED NOTIFICATION (session ID in request header)...")
    notify_payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    response2 = httpx.post(
        "http://localhost:8000/mcp",
        json=notify_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id  # Send as REQUEST header!
        },
        timeout=10.0
    )
    
    print(f"Status: {response2.status_code}")
    print(f"Response: {response2.text[:200]}")
    
    # Step 3: List tools
    print("\n3. LIST TOOLS (session ID in request header)...")
    list_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response3 = httpx.post(
        "http://localhost:8000/mcp",
        json=list_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id  # Send as REQUEST header!
        },
        timeout=10.0
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
        return
    
    # Step 4: Call tool
    print("\n4. CALL TOOL (session ID in request header)...")
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
    
    response4 = httpx.post(
        "http://localhost:8000/mcp",
        json=call_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id  # Send as REQUEST header!
        },
        timeout=10.0
    )
    
    print(f"Status: {response4.status_code}")
    
    if response4.status_code == 200:
        print("✅ Tool call successful!")
        # Parse SSE response
        for line in response4.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                print("\nParsed response:")
                print(json.dumps(data, indent=2))
    else:
        print(f"❌ Failed: {response4.text[:200]}")

if __name__ == "__main__":
    test_session_header()
