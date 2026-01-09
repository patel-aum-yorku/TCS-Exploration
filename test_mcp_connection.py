#!/usr/bin/env python3
"""
Test script to verify MCP server connection
"""
import httpx
import uuid
import json

def test_mcp_connection():
    """Test connection to MCP server"""
    
    print("Testing MCP Server Connection...")
    print("=" * 60)
    
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    # Test 1: Initialize session
    print("\n1. Testing session initialization...")
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
    
    try:
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
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        # Handle SSE response
        if "text/event-stream" in response.headers.get('content-type', ''):
            print("Response Format: SSE (Server-Sent Events)")
            print("\nRaw Response:")
            print(response.text[:500])  # First 500 chars
            
            # Parse SSE
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    data = json.loads(line[6:])  # Remove 'data: ' prefix
                    print("\nParsed Data:")
                    print(json.dumps(data, indent=2))
                    
                    if "result" in data:
                        print("✅ Session initialized successfully!")
                        
                        # Test 2: List tools
                        print("\n2. Testing tools/list...")
                        list_payload = {
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/list",
                            "params": {}
                        }
                        
                        response2 = httpx.post(
                            "http://localhost:8000/mcp",
                            json=list_payload,
                            headers={
                                "Content-Type": "application/json",
                                "Accept": "application/json, text/event-stream"
                            },
                            params={"sessionId": session_id},
                            timeout=5.0
                        )
                        
                        print(f"Status Code: {response2.status_code}")
                        lines2 = response2.text.strip().split('\n')
                        for line2 in lines2:
                            if line2.startswith('data: '):
                                data2 = json.loads(line2[6:])
                                if "result" in data2 and "tools" in data2["result"]:
                                    print("✅ Tools retrieved successfully!")
                                    print(f"Available tools: {len(data2['result']['tools'])}")
                                    for tool in data2['result']['tools']:
                                        print(f"  - {tool['name']}")
                        
                        return True
        else:
            print("Response Format: JSON")
            print(json.dumps(response.json(), indent=2))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False

if __name__ == "__main__":
    success = test_mcp_connection()
    print("\n" + "=" * 60)
    if success:
        print("✅ MCP Server is working correctly!")
    else:
        print("❌ MCP Server test failed")
