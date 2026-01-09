"""
Configuration settings for the Financial RAG Assistant UI
"""
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DATA_DIR = BACKEND_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"

# MCP Server settings
MCP_HOST = "localhost"
MCP_PORT = 8000
MCP_BASE_URL = f"http://{MCP_HOST}:{MCP_PORT}"

# Streamlit settings
STREAMLIT_PORT = 8501
STREAMLIT_HOST = "localhost"

# Database settings
DB_CONFIG = {
    "dbname": "financial_rag_db",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": "5432"
}

# UI settings
MAX_CHAT_HISTORY = 50  # Maximum chat messages to keep in memory
MAX_AGENT_LOGS = 100  # Maximum agent logs to keep
CHAT_DISPLAY_LIMIT = 20  # Number of messages to display at once

# File upload settings
ALLOWED_EXTENSIONS = ['pdf']
MAX_FILE_SIZE_MB = 100

# Agent settings
AGENT_TIMEOUT = 300  # 5 minutes timeout for agent queries
RECURSION_LIMIT = 20

# Styling
THEME_COLORS = {
    'primary': '#1f77b4',
    'success': '#28a745',
    'warning': '#ffc107',
    'error': '#dc3545',
    'info': '#17a2b8'
}

# Example queries
EXAMPLE_QUERIES = [
    "Calculate the liquidity and leverage ratios for NVDA based on their 10-K",
    "What is NVDA's current stock price and recent performance?",
    "Provide a comprehensive financial analysis of NVDA",
    "What are NVDA's main revenue sources according to their 10-K?",
    "Calculate the current ratio and debt-to-equity ratio for NVDA",
    "Compare NVDA's debt-to-equity ratio with industry standards",
    "What are the key risks mentioned in NVDA's 10-K filing?",
    "Analyze NVDA's cash flow position",
]
