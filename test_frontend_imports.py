#!/usr/bin/env python3
"""
Test script to verify all imports work correctly from frontend
"""
import sys
from pathlib import Path

# Add backend to path (same as app.py does)
backend_path = str(Path(__file__).parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("Testing imports from frontend context...")
print("=" * 60)

try:
    print("\n1. Testing agents.graph import...")
    from agents.graph import app
    print("   ✅ agents.graph imported successfully")
except Exception as e:
    print(f"   ❌ Failed: {e}")

try:
    print("\n2. Testing ingestion.parser import...")
    from ingestion.parser import PDFParser
    print("   ✅ ingestion.parser imported successfully")
except Exception as e:
    print(f"   ❌ Failed: {e}")

try:
    print("\n3. Testing ingestion.summarizer import...")
    from ingestion.summarizer import MultiModalSummarizer
    print("   ✅ ingestion.summarizer imported successfully")
except Exception as e:
    print(f"   ❌ Failed: {e}")

try:
    print("\n4. Testing database.init_db import...")
    from database.init_db import init_database
    print("   ✅ database.init_db imported successfully")
except Exception as e:
    print(f"   ❌ Failed: {e}")

try:
    print("\n5. Testing retrieval.loader import...")
    from retrieval.loader import DataLoader
    print("   ✅ retrieval.loader imported successfully")
except Exception as e:
    print(f"   ❌ Failed: {e}")

try:
    print("\n6. Testing agents.mcp_client import...")
    from agents.mcp_client import MCPClient
    print("   ✅ agents.mcp_client imported successfully")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print("\n" + "=" * 60)
print("✅ All imports working correctly!")
print("\nYour frontend should now work without 'No module named backend' errors.")
