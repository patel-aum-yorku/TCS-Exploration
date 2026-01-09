"""
HTTP MCP Client for LangGraph agent integration.
Communicates with the FastMCP server running on localhost.
"""
import httpx
import json
from typing import Dict, Any, Optional
import asyncio
import uuid

class MCPClient:
    """Client for communicating with FastMCP HTTP server"""
    
    def __init__(self, base_url: str = "http://localhost:8000/mcp"):
        self.base_url = base_url
        self.session_id = None
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        )
    
    def parse_sse_response(self, text: str) -> Dict[str, Any]:
        """Parse Server-Sent Events response from FastMCP"""
        try:
            # SSE format: "data: {json}\n\n"
            for line in text.split('\n'):
                if line.startswith('data: '):
                    json_str = line[6:]  # Remove "data: " prefix
                    return json.loads(json_str)
            # If no SSE format, try parsing as plain JSON
            return json.loads(text)
        except:
            return {"error": "Failed to parse response"}
    
    async def _parse_sse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse Server-Sent Events response from FastMCP"""
        try:
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    return json.loads(line[6:])  # Remove 'data: ' prefix
            return {"error": "No data in SSE response"}
        except Exception as e:
            return {"error": f"Failed to parse SSE: {str(e)}"}
    
    async def initialize_session(self):
        """Initialize a session with the MCP server"""
        if self.session_id:
            return self.session_id
        
        try:
            # Initialize session
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "financial-rag-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Don't send session ID on initialize - server will provide it
            response = await self.client.post(
                self.base_url,
                json=payload
            )
            response.raise_for_status()
            
            # Capture session ID from response header
            self.session_id = response.headers.get("mcp-session-id")
            
            # Parse SSE response
            result = await self._parse_sse_response(response)
            if "result" in result:
                print(f"✅ MCP Session initialized: {self.session_id}")
            
            # Send initialized notification with session ID in request header
            notify_payload = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            
            notify_response = await self.client.post(
                self.base_url,
                json=notify_payload,
                headers={"mcp-session-id": self.session_id}
            )
            
            return self.session_id
        except Exception as e:
            print(f"Session initialization error: {e}")
            return None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server using FastMCP's JSON-RPC format.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments for the tool
        
        Returns:
            Tool execution result
        """
        try:
            # Ensure session is initialized
            if not self.session_id:
                await self.initialize_session()
            
            # FastMCP uses JSON-RPC 2.0 format
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Send session ID in request header (not query param!)
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers={"mcp-session-id": self.session_id}
            )
            
            response.raise_for_status()
            
            # Parse SSE response
            result = await self._parse_sse_response(response)
            
            # Extract the actual result from JSON-RPC response
            if "result" in result:
                return result["result"]
            elif "error" in result:
                return {"error": f"MCP Error: {result['error']}"}
            return result
            
        except httpx.HTTPError as e:
            return {"error": f"HTTP error calling {tool_name}: {str(e)}"}
        except Exception as e:
            return {"error": f"Error calling {tool_name}: {str(e)}"}
    
    async def list_tools(self) -> Dict[str, Any]:
        """List all available tools on the MCP server"""
        try:
            # Ensure session is initialized
            if not self.session_id:
                await self.initialize_session()
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers={"mcp-session-id": self.session_id}
            )
            response.raise_for_status()
            result = await self._parse_sse_response(response)
            return result.get("result", result)
        except Exception as e:
            return {"error": f"Error listing tools: {str(e)}"}
    
    async def calculate_liquidity_ratios(self, rag_data: str) -> str:
        """Calculate liquidity ratios from financial data"""
        result = await self.call_tool("calculate_liquidity_ratios", {"rag_data": rag_data})
        if "error" in result:
            return json.dumps(result)
        # FastMCP returns content in the result
        if "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", json.dumps(result))
        return json.dumps(result)
    
    async def calculate_leverage_ratios(self, rag_data: str) -> str:
        """Calculate leverage ratios from financial data"""
        result = await self.call_tool("calculate_leverage_ratios", {"rag_data": rag_data})
        if "error" in result:
            return json.dumps(result)
        # FastMCP returns content in the result
        if "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", json.dumps(result))
        return json.dumps(result)
    
    async def calculate_all_ratios(self, rag_data: str) -> str:
        """Calculate all financial ratios from financial data"""
        result = await self.call_tool("calculate_all_ratios", {"rag_data": rag_data})
        if "error" in result:
            return json.dumps(result)
        # FastMCP returns content in the result
        if "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", json.dumps(result))
        return json.dumps(result)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()