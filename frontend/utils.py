"""
Utility functions for the Streamlit frontend
"""
import sys
from pathlib import Path
import subprocess
import time
import httpx

def check_mcp_server():
    """Check if MCP server is running on port 8000"""
    try:
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "utils-health-check",
                    "version": "1.0.0"
                }
            }
        }
        
        # Don't send session ID on initialize - server provides it
        response = httpx.post(
            "http://localhost:8000/mcp",
            json=init_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            timeout=2.0
        )
        
        # Check if response contains session ID header and valid result
        if response.status_code == 200 and response.headers.get("mcp-session-id"):
            # Parse SSE response
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    import json
                    data = json.loads(line[6:])
                    return "result" in data
        return False
    except:
        return False

def check_postgres_db():
    """Check if PostgreSQL database is accessible"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname="financial_rag_db",
            user="postgres",
            password="root",
            host="localhost",
            port="5432"
        )
        conn.close()
        return True
    except:
        return False

def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_uploaded_files_info():
    """Get information about uploaded files"""
    upload_dir = Path(__file__).parent.parent / "backend" / "data" / "uploads"
    if not upload_dir.exists():
        return []
    
    files_info = []
    for file_path in upload_dir.glob("*.pdf"):
        files_info.append({
            'name': file_path.name,
            'size': format_file_size(file_path.stat().st_size),
            'modified': file_path.stat().st_mtime
        })
    
    return sorted(files_info, key=lambda x: x['modified'], reverse=True)

def get_processed_documents_info():
    """Get information about processed documents"""
    processed_dir = Path(__file__).parent.parent / "backend" / "data" / "processed"
    if not processed_dir.exists():
        return []
    
    docs_info = []
    for doc_folder in processed_dir.iterdir():
        if doc_folder.is_dir():
            # Count files in each category
            text_dir = doc_folder / "text"
            tables_dir = doc_folder / "tables"
            images_dir = doc_folder / "images"
            
            text_count = len(list(text_dir.glob("*.md"))) if text_dir.exists() else 0
            tables_count = len(list(tables_dir.glob("*.json"))) if tables_dir.exists() else 0
            images_count = len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0
            
            docs_info.append({
                'name': doc_folder.name,
                'text_chunks': text_count,
                'tables': tables_count,
                'images': images_count,
                'total_items': text_count + tables_count + images_count
            })
    
    return docs_info

def validate_environment():
    """Validate that all required services are available"""
    checks = {
        'MCP Server': check_mcp_server(),
        'PostgreSQL Database': check_postgres_db(),
    }
    return checks

class AgentLogger:
    """Simple logger for agent activities"""
    
    def __init__(self):
        self.logs = []
    
    def log(self, message, level="info"):
        """Add a log entry"""
        self.logs.append({
            'message': message,
            'level': level,
            'timestamp': time.time()
        })
    
    def get_recent(self, count=10):
        """Get recent logs"""
        return self.logs[-count:]
    
    def clear(self):
        """Clear all logs"""
        self.logs = []
