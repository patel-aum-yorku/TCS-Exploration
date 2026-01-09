#!/usr/bin/env python3
"""
Manual step-by-step test of MCP protocol
"""
import httpx
import uuid
import json
import time

def test_full_flow():
    """Test complete MCP flow with all steps"""
    
    print("Testing Full MCP Flow...")
    print("=" * 60)
    
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
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
        params={"sessionId": session_id},
        timeout=5.0
    )
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    # IMPORTANT: Capture the session ID from the response header!
    server_session_id = response.headers.get('mcp-session-id')
    print(f"Server returned session ID: {server_session_id}")
    
    if response.status_code == 200:
        print("✅ Initialize successful")
        # Parse response
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                print(f"Result: {data.get('result', {}).get('serverInfo')}")
        
        # Use the server's session ID for all subsequent requests!
        session_id = server_session_id
        print(f"Using session ID: {session_id}")
    else:
        print(f"❌ Initialize failed: {response.text}")
        return
    
    # Step 2: Send initialized notification
    print("\n2. INITIALIZED NOTIFICATION...")
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
            "Accept": "application/json, text/event-stream"
        },
        params={"sessionId": session_id},
        timeout=5.0
    )
    
    print(f"Status: {response2.status_code}")
    print(f"Response: {response2.text[:200]}")
    
    if response2.status_code in [200, 204]:
        print("✅ Initialized notification sent")
    else:
        print(f"⚠️  Notification returned {response2.status_code}")
    
    # Small delay
    time.sleep(0.5)
    
    # Step 3: List tools
    print("\n3. LIST TOOLS...")
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
            "Accept": "application/json, text/event-stream"
        },
        params={"sessionId": session_id},
        timeout=5.0
    )
    
    print(f"Status: {response3.status_code}")
    print(f"Response text: {response3.text[:500]}")
    
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
        print(f"❌ Tools list failed")
        # Try to parse error
        try:
            for line in response3.text.split('\n'):
                if line.startswith('data: '):
                    error_data = json.loads(line[6:])
                    print(f"Error: {error_data.get('error')}")
        except:
            pass
    
    # Step 4: Call a tool
    print("\n4. CALL TOOL...")
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
            "Accept": "application/json, text/event-stream"
        },
        params={"sessionId": session_id},
        timeout=10.0
    )
    
    print(f"Status: {response4.status_code}")
    
    if response4.status_code == 200:
        print("✅ Tool call successful!")
        print(f"Response: {response4.text[:1000]}")
    else:
        print(f"❌ Tool call failed")
        print(f"Response: {response4.text[:500]}")

if __name__ == "__main__":
    test_full_flow()
