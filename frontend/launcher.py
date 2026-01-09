#!/usr/bin/env python3
"""
Launcher script for the Financial RAG Assistant
Starts both MCP server and Streamlit UI with proper error handling
"""
import subprocess
import sys
import time
import os
from pathlib import Path
import signal

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def check_prerequisites():
    """Check if all prerequisites are met"""
    print_info("Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print_error(f"Python 3.10+ required. Current version: {sys.version}")
        return False
    print_success(f"Python version: {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check required packages
    required_packages = [
        'streamlit',
        'langchain',
        'langgraph',
        'psycopg2',
        'fastmcp',
        'httpx'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"Package '{package}' found")
        except ImportError:
            missing_packages.append(package)
            print_warning(f"Package '{package}' not found")
    
    if missing_packages:
        print_error(f"Missing packages: {', '.join(missing_packages)}")
        print_info("Install with: pip install " + " ".join(missing_packages))
        return False
    
    # Check .env file
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        print_warning(".env file not found")
        print_info("Create .env file with required API keys")
    else:
        print_success(".env file found")
    
    # Check data directories
    data_dir = Path(__file__).parent.parent / "backend" / "data"
    if not data_dir.exists():
        print_warning("Data directory not found, creating...")
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "uploads").mkdir(exist_ok=True)
        (data_dir / "processed").mkdir(exist_ok=True)
    print_success("Data directories ready")
    
    return True

def check_port_available(port):
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def start_mcp_server():
    """Start the MCP server"""
    print_info("Starting MCP Server...")
    
    # Check if port is available
    if not check_port_available(8000):
        print_warning("Port 8000 is already in use. MCP server may already be running.")
        return None
    
    script_path = Path(__file__).parent / "start_mcp.py"
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print_success("MCP Server started on http://localhost:8000")
            return process
        else:
            print_error("MCP Server failed to start")
            stdout, stderr = process.communicate()
            print_error(f"STDOUT: {stdout}")
            print_error(f"STDERR: {stderr}")
            return None
    
    except Exception as e:
        print_error(f"Failed to start MCP server: {str(e)}")
        return None

def start_streamlit():
    """Start the Streamlit UI"""
    print_info("Starting Streamlit UI...")
    
    app_path = Path(__file__).parent / "app.py"
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(app_path), 
             "--server.headless", "true",
             "--browser.gatherUsageStats", "false"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for Streamlit to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print_success("Streamlit UI started on http://localhost:8501")
            return process
        else:
            print_error("Streamlit failed to start")
            stdout, stderr = process.communicate()
            print_error(f"STDOUT: {stdout}")
            print_error(f"STDERR: {stderr}")
            return None
    
    except Exception as e:
        print_error(f"Failed to start Streamlit: {str(e)}")
        return None

def cleanup(mcp_process, streamlit_process):
    """Clean up processes on exit"""
    print_info("\nShutting down services...")
    
    if mcp_process and mcp_process.poll() is None:
        mcp_process.terminate()
        mcp_process.wait(timeout=5)
        print_success("MCP Server stopped")
    
    if streamlit_process and streamlit_process.poll() is None:
        streamlit_process.terminate()
        streamlit_process.wait(timeout=5)
        print_success("Streamlit UI stopped")
    
    print_success("All services stopped successfully")

def main():
    """Main launcher function"""
    print_header("Financial RAG Assistant Launcher")
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites check failed. Please resolve issues and try again.")
        sys.exit(1)
    
    print_success("All prerequisites met!")
    
    mcp_process = None
    streamlit_process = None
    
    try:
        # Start MCP server
        print("\n")
        mcp_process = start_mcp_server()
        
        if mcp_process is None:
            print_warning("Continuing without MCP server (you can start it from the UI)")
        
        # Start Streamlit
        print("\n")
        streamlit_process = start_streamlit()
        
        if streamlit_process is None:
            print_error("Failed to start Streamlit UI")
            cleanup(mcp_process, None)
            sys.exit(1)
        
        # Print success message
        print_header("🚀 Application Started Successfully!")
        print_info("Services running:")
        if mcp_process:
            print_success("  MCP Server: http://localhost:8000")
        print_success("  Streamlit UI: http://localhost:8501")
        print("\n")
        print_warning("Press Ctrl+C to stop all services")
        print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if mcp_process and mcp_process.poll() is not None:
                print_warning("MCP Server has stopped unexpectedly")
                mcp_process = None
            
            if streamlit_process and streamlit_process.poll() is not None:
                print_error("Streamlit UI has stopped unexpectedly")
                break
    
    except KeyboardInterrupt:
        print("\n")
        print_info("Received shutdown signal...")
    
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
    
    finally:
        cleanup(mcp_process, streamlit_process)

if __name__ == "__main__":
    main()
