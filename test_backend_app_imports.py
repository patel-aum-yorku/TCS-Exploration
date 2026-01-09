#!/usr/bin/env python3
"""
Test imports from backend/app.py context
"""
import sys
from pathlib import Path

# Simulate what backend/app.py does
backend_path = str(Path(__file__).parent / "backend")
sys.path.insert(0, backend_path)

print("Testing imports from backend/app.py context...")
print(f"Backend path: {backend_path}")
print(f"sys.path[0]: {sys.path[0]}")
print("=" * 60)

try:
    print("\n1. Testing agents.graph...")
    from agents.graph import app
    print("   ✅ Success! agents.graph imported")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("If imports work, Streamlit should work too!")
print(f"Streamlit is running at: http://localhost:8502")
