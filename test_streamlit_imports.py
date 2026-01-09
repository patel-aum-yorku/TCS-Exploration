#!/usr/bin/env python3
"""
Test if imports work from Streamlit frontend context
"""
import sys
from pathlib import Path

# Simulate what app.py does
backend_path = str(Path(__file__).parent / "backend")
sys.path.insert(0, backend_path)

print("Testing imports with backend in sys.path...")
print(f"Backend path: {backend_path}")
print(f"sys.path[0]: {sys.path[0]}")
print("=" * 60)

try:
    print("\n1. Testing agents.graph...")
    from agents.graph import app
    print("   ✅ Success! agents.graph imported")
    print(f"   App type: {type(app)}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n2. Testing agents.mcp_client...")
    from agents.mcp_client import MCPClient
    print("   ✅ Success! agents.mcp_client imported")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n3. Testing agents.tools...")
    from agents.tools import retrieve_financial_docs
    print("   ✅ Success! agents.tools imported")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n4. Testing agents.state...")
    from agents.state import AgentState
    print("   ✅ Success! agents.state imported")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete!")
