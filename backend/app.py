"""
Streamlit UI for Multi-Agent Financial RAG System
Provides file upload, ingestion pipeline, and chat interface with real-time agent status.
"""
import streamlit as st
import sys
import os
import asyncio
from pathlib import Path
import shutil
import time
from datetime import datetime
import subprocess
import io
from contextlib import redirect_stdout, redirect_stderr

# Add backend to path
# Since app.py is now IN the backend folder, parent is the backend folder itself
backend_path = str(Path(__file__).parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'agent_logs' not in st.session_state:
    st.session_state.agent_logs = []
if 'ingestion_status' not in st.session_state:
    st.session_state.ingestion_status = None
if 'mcp_server_running' not in st.session_state:
    st.session_state.mcp_server_running = False
if 'mcp_process' not in st.session_state:
    st.session_state.mcp_process = None

# Page config
st.set_page_config(
    page_title="Financial RAG Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .status-info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .status-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .agent-log {
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        padding: 0.4rem 0.6rem;
        background-color: #2d2d2d;
        color: #e0e0e0;
        border-left: 3px solid #1f77b4;
        margin: 0.2rem 0;
        border-radius: 3px;
        line-height: 1.4;
    }
    .agent-log-manager {
        border-left-color: #e91e63;
    }
    .agent-log-rag {
        border-left-color: #4caf50;
    }
    .agent-log-stock {
        border-left-color: #ff9800;
    }
    .agent-log-calc {
        border-left-color: #9c27b0;
    }
    .agent-log-reporter {
        border-left-color: #00bcd4;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #1a1a1a;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
        color: #0d47a1;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
        color: #212121;
    }
    /* Fix for markdown content in assistant messages */
    .assistant-message h1, .assistant-message h2, .assistant-message h3,
    .assistant-message h4, .assistant-message p, .assistant-message li,
    .assistant-message strong, .assistant-message em {
        color: #212121 !important;
    }
    /* Scrollable agent logs container */
    .agent-logs-container {
        max-height: 70vh;
        overflow-y: auto;
        padding: 0.5rem;
        background-color: #1a1a1a;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_mcp_server_status():
    """Check if MCP server is running"""
    try:
        import httpx
        import uuid
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Initialize session
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "streamlit-health-check",
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
        
        # FastMCP returns SSE format - check if we got a successful response
        return response.status_code == 200 and (
            "result" in response.text or "data:" in response.text
        )
    except:
        return False

def start_mcp_server():
    """Start the MCP server in background"""
    try:
        import subprocess
        # Since app.py is now IN backend folder, adjust path
        mcp_server_path = Path(__file__).parent / "mcp_server" / "start_server.py"
        process = subprocess.Popen(
            [sys.executable, str(mcp_server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        st.session_state.mcp_process = process
        st.session_state.mcp_server_running = True
        time.sleep(3)  # Wait for server to start
        return True
    except Exception as e:
        st.error(f"Failed to start MCP server: {str(e)}")
        return False

def stop_mcp_server():
    """Stop the MCP server"""
    if st.session_state.mcp_process:
        st.session_state.mcp_process.terminate()
        st.session_state.mcp_process = None
        st.session_state.mcp_server_running = False

def save_uploaded_file(uploaded_file):
    """Save uploaded file to uploads directory"""
    # Since app.py is now IN backend folder, adjust path
    upload_dir = Path(__file__).parent / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def run_ingestion_pipeline(status_container):
    """Run the complete ingestion pipeline"""
    try:
        # Import after path is set - use relative import since backend is in sys.path
        from ingestion.parser import PDFParser
        from ingestion.summarizer import MultiModalSummarizer
        from database.init_db import init_database
        from retrieval.loader import DataLoader
        
        # Step 1: Initialize Database
        status_container.info("🔧 Step 1/4: Initializing database...")
        init_database()
        status_container.success("✅ Database initialized")
        time.sleep(1)
        
        # Step 2: Parse PDFs
        status_container.info("📄 Step 2/4: Parsing PDF documents...")
        parser = PDFParser()
        results = parser.process_all()
        status_container.success(f"✅ Parsed {len(results)} document(s)")
        time.sleep(1)
        
        # Step 3: Summarize content
        status_container.info("🤖 Step 3/4: Generating summaries (this may take a while)...")
        summarizer = MultiModalSummarizer()
        
        # Get all processed documents
        processed_dir = Path(__file__).parent / "data" / "processed"
        doc_folders = [d.name for d in processed_dir.iterdir() if d.is_dir()]
        
        # Run async summarization for each document
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for doc_id in doc_folders:
            loop.run_until_complete(summarizer.process_document(doc_id))
        loop.close()
        
        status_container.success(f"✅ Summaries generated for {len(doc_folders)} document(s)")
        time.sleep(1)
        
        # Step 4: Load into vector database
        status_container.info("💾 Step 4/4: Loading into vector database...")
        loader = DataLoader()
        loader.load_all_documents()
        status_container.success("✅ Data loaded into vector database")
        
        return True, "Ingestion pipeline completed successfully!"
        
    except Exception as e:
        return False, f"Error during ingestion: {str(e)}"

async def run_agent_query(query, status_container, log_container):
    """Run the multi-agent system on a query with detailed logging"""
    try:
        # Import after path is set
        from agents.graph import app
        
        # Clear previous logs
        st.session_state.agent_logs = []
        
        # Create a string buffer to capture print statements
        output_buffer = io.StringIO()
        
        initial_state = {
            "query": query,
            "messages": [],
            "rag_data": None,
            "stock_data": None,
            "calc_data": None,
            "next_step": "start"
        }
        
        config = {"recursion_limit": 20}
        
        # Capture stdout to get all print statements from graph.py
        result = None
        
        # Use redirect_stdout to capture all print statements
        with redirect_stdout(output_buffer):
            async for output in app.astream(initial_state, config=config):
                # Get any new output from buffer
                current_output = output_buffer.getvalue()
                if current_output:
                    # Process each line of output
                    lines = current_output.strip().split('\n')
                    for line in lines:
                        if line.strip() and line not in st.session_state.agent_logs:
                            # Determine log class based on content
                            log_class = "agent-log"
                            if "Manager" in line:
                                log_class += " agent-log-manager"
                            elif "RAG Agent" in line:
                                log_class += " agent-log-rag"
                            elif "Stock Agent" in line:
                                log_class += " agent-log-stock"
                            elif "Calc Agent" in line:
                                log_class += " agent-log-calc"
                            elif "Reporter" in line:
                                log_class += " agent-log-reporter"
                            
                            st.session_state.agent_logs.append(line)
                            log_container.markdown(
                                f'<div class="{log_class}">{line}</div>',
                                unsafe_allow_html=True
                            )
                    
                    # Clear buffer after processing
                    output_buffer.truncate(0)
                    output_buffer.seek(0)
                
                # Check for final result
                for key, value in output.items():
                    if key == "reporter":
                        result = value.get('messages', [None])[0]
        
        return result
        
    except Exception as e:
        log_container.error(f"❌ Error: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        st.session_state.agent_logs.append(f"❌ Error: {error_details}")
        return None

# ============================================================================
# SIDEBAR - DOCUMENT MANAGEMENT
# ============================================================================

with st.sidebar:
    st.markdown("## 📁 Document Management")
    
    # MCP Server Control
    st.markdown("### 🖥️ MCP Server")
    mcp_status = check_mcp_server_status()
    
    if mcp_status:
        st.success("🟢 MCP Server Running")
        if st.button("🛑 Stop MCP Server"):
            stop_mcp_server()
            st.rerun()
    else:
        st.warning("🔴 MCP Server Offline")
        if st.button("▶️ Start MCP Server"):
            if start_mcp_server():
                st.success("MCP Server started!")
                time.sleep(2)
                st.rerun()
    
    st.markdown("---")
    
    # File Upload Section
    st.markdown("### 📤 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF files (10-K, Financial Reports)",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload financial documents to be processed"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) selected")
        
        if st.button("💾 Save Files", type="primary"):
            with st.spinner("Saving files..."):
                for file in uploaded_files:
                    save_uploaded_file(file)
                st.success(f"Saved {len(uploaded_files)} file(s) to uploads folder")
    
    st.markdown("---")
    
    # Ingestion Pipeline Section
    st.markdown("### ⚙️ Ingestion Pipeline")
    st.caption("Processes uploaded documents through: Parse → Summarize → Load")
    
    if st.button("🚀 Run Ingestion Pipeline", type="primary"):
        status_container = st.empty()
        
        with st.spinner("Running ingestion pipeline..."):
            success, message = run_ingestion_pipeline(status_container)
            
            if success:
                st.session_state.ingestion_status = {
                    'success': True,
                    'message': message,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.success(message)
            else:
                st.session_state.ingestion_status = {
                    'success': False,
                    'message': message,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.error(message)
    
    # Show last ingestion status
    if st.session_state.ingestion_status:
        st.markdown("---")
        st.markdown("### 📋 Last Ingestion")
        status = st.session_state.ingestion_status
        if status['success']:
            st.success(f"✅ {status['message']}")
        else:
            st.error(f"❌ {status['message']}")
        st.caption(f"⏰ {status['timestamp']}")
    
    st.markdown("---")
    
    # System Info
    st.markdown("### ℹ️ System Info")
    
    # Check uploaded files
    # Since app.py is now IN backend folder, adjust path
    upload_dir = Path(__file__).parent / "data" / "uploads"
    if upload_dir.exists():
        pdf_files = list(upload_dir.glob("*.pdf"))
        st.info(f"📄 {len(pdf_files)} file(s) in uploads")
    
    # Check processed documents
    # Since app.py is now IN backend folder, adjust path
    processed_dir = Path(__file__).parent / "data" / "processed"
    if processed_dir.exists():
        doc_folders = [d for d in processed_dir.iterdir() if d.is_dir()]
        st.info(f"✅ {len(doc_folders)} document(s) processed")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.session_state.agent_logs = []
        st.rerun()

# ============================================================================
# MAIN CONTENT - CHAT INTERFACE
# ============================================================================

# Header
st.markdown('<div class="main-header">📊 Financial RAG Assistant</div>', unsafe_allow_html=True)
st.markdown("Ask questions about financial documents, stock data, and get comprehensive analysis with calculated ratios.")

# Create two columns for chat and agent logs
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💬 Chat Interface")
    
    # Chat history display
    chat_container = st.container()
    with chat_container:
        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(
                        f'<div class="chat-message user-message"><strong>You:</strong><br>{message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    # Use st.markdown for assistant messages to properly render markdown
                    st.markdown(
                        f'<div class="chat-message assistant-message"><strong>Assistant:</strong></div>',
                        unsafe_allow_html=True
                    )
                    st.markdown(message["content"])
        else:
            st.info("👋 Welcome! Ask me anything about financial documents, stock prices, or request ratio calculations.")
    
    # Query input
    with st.form(key="query_form", clear_on_submit=True):
        user_query = st.text_area(
            "Your Question:",
            placeholder="e.g., Calculate the liquidity and leverage ratios for NVDA based on their 10-K",
            height=100,
            key="user_input"
        )
        
        col_a, col_b, col_c = st.columns([1, 1, 3])
        with col_a:
            submit_button = st.form_submit_button("🚀 Submit", type="primary")
        with col_b:
            example_button = st.form_submit_button("Examples")
    
    # Example queries
    if example_button:
        st.markdown("### 📝 Example Queries")
        examples = [
            "Calculate the liquidity and leverage ratios for NVDA based on their 10-K",
            "What is NVDA's current stock price and recent performance?",
            "Provide a comprehensive financial analysis of NVDA",
            "What are NVDA's main revenue sources according to their 10-K?",
            "Calculate the current ratio and debt-to-equity ratio for NVDA"
        ]
        for i, ex in enumerate(examples, 1):
            st.code(f" {ex}")

with col2:
    st.markdown("### 🔍 Agent Activity")
    agent_log_container = st.container()
    
    with agent_log_container:
        if st.session_state.agent_logs:
            # Display all logs in a scrollable container
            logs_html = '<div class="agent-logs-container">'
            for log in st.session_state.agent_logs:
                # Determine log class based on content
                log_class = "agent-log"
                if "Manager" in log or "🧠" in log:
                    log_class += " agent-log-manager"
                elif "RAG Agent" in log or "📚" in log:
                    log_class += " agent-log-rag"
                elif "Stock Agent" in log or "📈" in log:
                    log_class += " agent-log-stock"
                elif "Calc Agent" in log or "🧮" in log:
                    log_class += " agent-log-calc"
                elif "Reporter" in log or "📊" in log:
                    log_class += " agent-log-reporter"
                
                logs_html += f'<div class="{log_class}">{log}</div>'
            
            logs_html += '</div>'
            st.markdown(logs_html, unsafe_allow_html=True)
        else:
            st.info("Agent activity will appear here during query processing")

# Process query
if submit_button and user_query:
    # Check MCP server
    if not check_mcp_server_status():
        st.error("⚠️ MCP Server is not running. Please start it from the sidebar.")
    else:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_query,
            'timestamp': datetime.now()
        })
        
        # Create status containers
        with col1:
            status_placeholder = st.empty()
            status_placeholder.info("🤔 Processing your query...")
        
        with col2:
            log_placeholder = st.empty()
        
        # Run agent query
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_agent_query(user_query, status_placeholder, log_placeholder))
            loop.close()
            
            if result:
                # Add assistant response to history
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': result,
                    'timestamp': datetime.now()
                })
                status_placeholder.success("✅ Analysis complete!")
                time.sleep(1)
                st.rerun()
            else:
                status_placeholder.error("❌ Failed to generate response")
        
        except Exception as e:
            status_placeholder.error(f"❌ Error: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <small>
            🤖 Multi-Agent Financial RAG System | 
            Powered by LangGraph, AWS Bedrock & Google Gemini | 
            Built with Streamlit
        </small>
    </div>
    """,
    unsafe_allow_html=True
)
