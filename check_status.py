#!/usr/bin/env python3
"""
System Status Checker for Financial RAG Assistant
Verifies all required services and dependencies
"""
import sys
import os
from pathlib import Path
import subprocess

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message, status):
    """Print a status line with color"""
    if status == "OK":
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
        return True
    elif status == "WARN":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}❌ {message}{Colors.END}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        return print_status(f"Python version: {version.major}.{version.minor}.{version.micro}", "OK")
    else:
        return print_status(f"Python version too old: {version.major}.{version.minor}.{version.micro} (need 3.10+)", "FAIL")

def check_package(package_name):
    """Check if a Python package is installed"""
    try:
        __import__(package_name.replace('-', '_'))
        return True
    except ImportError:
        return False

def check_packages():
    """Check required Python packages"""
    required = [
        'streamlit',
        'langchain',
        'langgraph',
        'psycopg2',
        'fastmcp',
        'httpx',
        'boto3',
        'google.generativeai'
    ]
    
    all_ok = True
    for package in required:
        if check_package(package):
            print_status(f"Package '{package}' installed", "OK")
        else:
            print_status(f"Package '{package}' missing", "FAIL")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        return print_status(".env file not found", "FAIL")
    
    required_vars = [
        'GOOGLE_API_KEY',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY'
    ]
    
    with open(env_path) as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if var not in content or f"{var}=your_" in content:
            missing.append(var)
    
    if missing:
        print_status(f".env file exists but missing/incomplete: {', '.join(missing)}", "WARN")
        return True
    else:
        return print_status(".env file exists with all required variables", "OK")

def check_directories():
    """Check if required directories exist"""
    base = Path(__file__).parent
    
    dirs = [
        base / "backend" / "data" / "uploads",
        base / "backend" / "data" / "processed",
        base / "frontend"
    ]
    
    all_ok = True
    for directory in dirs:
        if directory.exists():
            print_status(f"Directory exists: {directory.relative_to(base)}", "OK")
        else:
            print_status(f"Directory missing: {directory.relative_to(base)}", "WARN")
            # Try to create
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print_status(f"  Created directory: {directory.relative_to(base)}", "OK")
            except:
                all_ok = False
    
    return all_ok

def check_postgres():
    """Check if PostgreSQL is running"""
    try:
        result = subprocess.run(
            ['docker', 'ps'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'financial-rag-db' in result.stdout or 'pgvector' in result.stdout:
            return print_status("PostgreSQL container is running", "OK")
        else:
            return print_status("PostgreSQL container not found (run: docker run ... pgvector/pgvector:pg17)", "WARN")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return print_status("Docker not available or not responding", "WARN")

def check_mcp_server():
    """Check if MCP server is running"""
    try:
        import httpx
        import uuid
        
        session_id = str(uuid.uuid4())
        
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "status-check",
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
            timeout=2.0
        )
        
        if response.status_code == 200 and "result" in response.json():
            return print_status("MCP Server is running on port 8000", "OK")
        else:
            return print_status("MCP Server responded with error", "WARN")
    except:
        return print_status("MCP Server is not running (start with: python frontend/start_mcp.py)", "WARN")

def check_streamlit():
    """Check if Streamlit is running"""
    try:
        import httpx
        response = httpx.get("http://localhost:8501/_stcore/health", timeout=2.0)
        if response.status_code == 200:
            return print_status("Streamlit UI is running on port 8501", "OK")
        else:
            return print_status("Streamlit responded with error", "WARN")
    except:
        return print_status("Streamlit UI is not running (start with: streamlit run frontend/app.py)", "WARN")

def check_db_connection():
    """Check database connection"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname="financial_rag_db",
            user="postgres",
            password="root",
            host="localhost",
            port="5432",
            connect_timeout=3
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return print_status("Database connection successful", "OK")
    except Exception as e:
        return print_status(f"Database connection failed: {str(e)}", "WARN")

def count_documents():
    """Count uploaded and processed documents"""
    base = Path(__file__).parent
    uploads_dir = base / "backend" / "data" / "uploads"
    processed_dir = base / "backend" / "data" / "processed"
    
    upload_count = len(list(uploads_dir.glob("*.pdf"))) if uploads_dir.exists() else 0
    processed_count = len([d for d in processed_dir.iterdir() if d.is_dir()]) if processed_dir.exists() else 0
    
    print(f"\n{Colors.BLUE}{Colors.BOLD}📊 Document Status:{Colors.END}")
    print(f"   📤 Uploaded: {upload_count} PDF(s)")
    print(f"   ✅ Processed: {processed_count} document(s)")

def main():
    """Main status check function"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{'Financial RAG Assistant - System Status Check'.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")
    
    # Check Python environment
    print(f"{Colors.BOLD}🐍 Python Environment{Colors.END}")
    python_ok = check_python_version()
    print()
    
    # Check packages
    print(f"{Colors.BOLD}📦 Python Packages{Colors.END}")
    packages_ok = check_packages()
    print()
    
    # Check configuration
    print(f"{Colors.BOLD}⚙️  Configuration{Colors.END}")
    env_ok = check_env_file()
    dirs_ok = check_directories()
    print()
    
    # Check services
    print(f"{Colors.BOLD}🖥️  Services{Colors.END}")
    postgres_ok = check_postgres()
    db_ok = check_db_connection()
    mcp_ok = check_mcp_server()
    streamlit_ok = check_streamlit()
    print()
    
    # Document status
    count_documents()
    print()
    
    # Summary
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}📋 Summary{Colors.END}")
    
    critical_ok = python_ok and packages_ok and env_ok and dirs_ok
    services_ok = postgres_ok or db_ok  # Need at least one DB indicator
    
    if critical_ok and services_ok:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ System is ready to use!{Colors.END}")
        print(f"\n{Colors.BOLD}To start the application:{Colors.END}")
        print(f"   ./start.sh")
        print(f"   OR")
        print(f"   python frontend/launcher.py")
    elif critical_ok:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  System is partially ready{Colors.END}")
        print(f"\n{Colors.BOLD}Some services are not running. You can:{Colors.END}")
        print(f"   1. Start PostgreSQL: docker run ... pgvector/pgvector:pg17")
        print(f"   2. Start application: ./start.sh")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ System is not ready{Colors.END}")
        print(f"\n{Colors.BOLD}Please fix the issues above, then:{Colors.END}")
        print(f"   1. Install missing packages: pip install -r requirements.txt")
        print(f"   2. Configure .env file")
        print(f"   3. Run this check again: python check_status.py")
    
    print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

if __name__ == "__main__":
    main()
