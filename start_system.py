"""
Startup script to run both MCP server and agent system
"""
import subprocess
import time
import signal
import sys
import asyncio
from pathlib import Path

class SystemRunner:
    def __init__(self):
        self.mcp_process = None
    
    def start_mcp_server(self):
        """Start the FastMCP server in background"""
        print("🚀 Starting FastMCP Financial Calculator Server...")
        
        self.mcp_process = subprocess.Popen(
            [sys.executable, "-m", "backend.agents.mcp_server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        time.sleep(3)
        
        if self.mcp_process.poll() is None:
            print("✅ MCP Server started on http://localhost:8000")
            return True
        else:
            print("❌ Failed to start MCP server")
            return False
    
    def stop_mcp_server(self):
        """Stop the MCP server"""
        if self.mcp_process:
            print("\n🛑 Stopping MCP server...")
            self.mcp_process.terminate()
            self.mcp_process.wait()
            print("✅ MCP server stopped")
    
    async def run_agents(self):
        """Run the agent system"""
        from backend.agents.run_agents import main
        await main()
    
    def run(self):
        """Run the complete system"""
        try:
            # Start MCP server
            if not self.start_mcp_server():
                return
            
            # Run agents
            print("\n" + "="*80)
            print("🤖 Starting Multi-Agent Financial Analysis System")
            print("="*80 + "\n")
            
            asyncio.run(self.run_agents())
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Received interrupt signal...")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            self.stop_mcp_server()
            print("\n✅ System shutdown complete")

if __name__ == "__main__":
    runner = SystemRunner()
    runner.run()