"""
HTTP-based MCP client for financial calculations.
Connects to FastMCP server running on localhost.
"""
import httpx
import json
from typing import Dict, Any
import asyncio

class MCPCalculator:
    """Calculator that uses HTTP to call FastMCP server"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.client = None
        self.connected = False
        self.session_id = None
    
    async def connect(self):
        """Initialize HTTP client and establish SSE session"""
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
            
            # Quick connection test
            response = await self.client.get(
                f"{self.server_url}/",
                timeout=5.0
            )
            
            # Server is up
            self.connected = True
            print("✅ MCP Calculator connected to HTTP server at http://localhost:8000")
            return True
            
        except httpx.ConnectError:
            print("⚠️ MCP Server not responding at http://localhost:8000")
            print("   Make sure the server is running: python -m backend.agents.mcp_server")
            self.connected = False
            return False
        except Exception as e:
            print(f"⚠️ MCP Server connection error: {e}")
            self.connected = False
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """
        Call a tool on the MCP server via REST API
        """
        if not self.connected:
            return {"error": "MCP server not connected"}
        
        if not self.client:
            return {"error": "HTTP client not initialized"}
        
        try:
            print(f"   🔧 Calling MCP tool: {tool_name}")
            
            # Call the REST API endpoint
            response = await self.client.post(
                f"{self.server_url}/{tool_name}",
                json=arguments,
                headers={"Content-Type": "application/json"},
                timeout=15.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            
        except httpx.TimeoutException:
            return {"error": f"MCP call timeout for {tool_name}"}
        except Exception as e:
            return {"error": f"MCP call failed: {str(e)}"}
    
    async def calculate_growth_rate(
        self, 
        current_value: float, 
        previous_value: float, 
        periods: int = 1
    ) -> Dict:
        """Calculate growth rate via MCP"""
        return await self.call_tool("calculate_growth_rate", {
            "current_value": current_value,
            "previous_value": previous_value,
            "periods": periods
        })
    
    async def calculate_profitability_ratios(
        self,
        revenue: float = 0,
        gross_profit: float = 0,
        operating_income: float = 0,
        net_income: float = 0,
        shareholders_equity: float = 0,
        total_assets: float = 0,
        cost_of_goods_sold: float = 0
    ) -> Dict:
        """Calculate profitability ratios via MCP"""
        return await self.call_tool("calculate_profitability_ratios", {
            "revenue": revenue,
            "gross_profit": gross_profit,
            "operating_income": operating_income,
            "net_income": net_income,
            "shareholders_equity": shareholders_equity,
            "total_assets": total_assets,
            "cost_of_goods_sold": cost_of_goods_sold
        })
    
    async def calculate_liquidity_ratios(
        self,
        current_assets: float = 0,
        current_liabilities: float = 0,
        cash_and_equivalents: float = 0,
        inventory: float = 0
    ) -> Dict:
        """Calculate liquidity ratios via MCP"""
        return await self.call_tool("calculate_liquidity_ratios", {
            "current_assets": current_assets,
            "current_liabilities": current_liabilities,
            "cash_and_equivalents": cash_and_equivalents,
            "inventory": inventory
        })
    
    async def calculate_leverage_ratios(
        self,
        total_debt: float = 0,
        total_liabilities: float = 0,
        shareholders_equity: float = 0,
        total_assets: float = 0,
        ebit: float = 0,
        interest_expense: float = 0
    ) -> Dict:
        """Calculate leverage ratios via MCP"""
        return await self.call_tool("calculate_leverage_ratios", {
            "total_debt": total_debt,
            "total_liabilities": total_liabilities,
            "shareholders_equity": shareholders_equity,
            "total_assets": total_assets,
            "ebit": ebit,
            "interest_expense": interest_expense
        })
    
    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
            self.connected = False

# Global calculator instance
mcp_calculator = MCPCalculator()

# Test function
async def test_connection():
    """Test MCP server connection"""
    print("🔗 Testing MCP Calculator connection...")
    
    connected = await mcp_calculator.connect()
    
    if connected:
        print("\n🧪 Running test calculation...")
        # Test calculation
        result = await mcp_calculator.calculate_growth_rate(120.0, 100.0, 1)
        print(f"✅ Test result: {result}\n")
        
        if not result.get("error"):
            print("🎉 MCP server is working correctly!")
        else:
            print("⚠️  MCP call failed - check server logs")
    
    await mcp_calculator.close()

if __name__ == "__main__":
    asyncio.run(test_connection())