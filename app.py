"""
Streamlit UI for Multi-Agent Financial Analysis System
"""
import streamlit as st
import os
import sys
from pathlib import Path
import subprocess
import time
from datetime import datetime
import io

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_orchestrator import initialize_system
from ingest_hybrid import main as ingest_main

# --- CONFIG ---
DOCS_FOLDER = "Docs"
INDEX_FOLDER = "faiss_index_hybrid"

# Page config
st.set_page_config(
    page_title="Financial Analysis AI",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if "manager_agent" not in st.session_state:
    st.session_state.manager_agent = None
if "index_ready" not in st.session_state:
    st.session_state.index_ready = os.path.exists(INDEX_FOLDER)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = {}

def save_uploaded_file(uploaded_file):
    """Save uploaded PDF to Docs folder"""
    if not os.path.exists(DOCS_FOLDER):
        os.makedirs(DOCS_FOLDER)
    
    file_path = os.path.join(DOCS_FOLDER, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def process_documents():
    """Run the ingestion pipeline"""
    try:
        with st.spinner("🔄 Processing documents and creating embeddings..."):
            # Run ingest_hybrid.py
            ingest_main()
            st.session_state.index_ready = True
            return True
    except Exception as e:
        st.error(f"Error processing documents: {str(e)}")
        return False

def initialize_agents():
    """Initialize the agent system"""
    try:
        with st.spinner("🤖 Initializing AI agents..."):
            manager_agent, mcp_client = initialize_system()  # Unpack the tuple
            st.session_state.manager_agent = manager_agent
            st.session_state.mcp_client = mcp_client  # Store mcp_client if needed later
            return True
    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        return False

def capture_agent_execution(prompt):
    """
    Capture agent execution details for display in UI
    """
    from contextlib import redirect_stdout, redirect_stderr
    
    # Capture stdout/stderr to get debug info
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    execution_log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": prompt,
        "agents_called": [],
        "tools_used": [],
        "documents_retrieved": [],
        "calculations_performed": [],
        "execution_time": 0,
        "raw_output": "",
        "detailed_steps": []
    }
    
    start_time = time.time()
    
    try:
        # Capture the agent execution output
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            response = st.session_state.manager_agent(prompt)
        
        execution_log["execution_time"] = round(time.time() - start_time, 2)
        execution_log["raw_output"] = stdout_buffer.getvalue()
        
        # Parse the output to extract detailed agent information
        raw_output = stdout_buffer.getvalue()
        
        # Parse for RAG agent activity
        if "🔍 RAG Query:" in raw_output:
            execution_log["agents_called"].append("RAG Agent")
            execution_log["tools_used"].append("retrieve_financial_documents")
            execution_log["detailed_steps"].append("🔍 RAG Agent queried for document retrieval")
            
            # Extract the actual query
            import re
            query_match = re.search(r'🔍 RAG Query: (.+)', raw_output)
            if query_match:
                execution_log["detailed_steps"].append(f"   → Query: '{query_match.group(1)}'")
        
        # Parse for document retrieval details
        if "📄 Retrieved" in raw_output and "documents" in raw_output:
            doc_matches = re.findall(r'📄 Retrieved (\d+) documents', raw_output)
            if doc_matches:
                count = doc_matches[0]
                execution_log["documents_retrieved"].append(f"{count} documents found")
                execution_log["detailed_steps"].append(f"📄 Retrieved {count} relevant documents from FAISS index")
                
                # Extract document details
                doc_detail_matches = re.findall(r'Document \d+: (.+?) \(Page (.+?)\)', raw_output)
                for doc, page in doc_detail_matches[:3]:  # Show first 3 documents
                    execution_log["detailed_steps"].append(f"   → {doc} (Page {page})")
        
        # Parse for MCP agent activity
        if "Tool #1: calculate_ratio" in raw_output or "MCP_Agent" in raw_output:
            execution_log["agents_called"].append("MCP Agent")
            execution_log["tools_used"].append("Financial calculations")
            execution_log["detailed_steps"].append("🧮 MCP Agent called for financial calculations")
            
            # Extract calculation details
            if "calculate_ratio" in raw_output:
                execution_log["calculations_performed"].append("Current ratio calculation")
                execution_log["detailed_steps"].append("   → Tool: calculate_ratio")
            if "compare_periods" in raw_output:
                execution_log["calculations_performed"].append("Period comparison")
                execution_log["detailed_steps"].append("   → Tool: compare_periods")
        
        # Parse for Manager agent decisions
        if "Tool #1: query_rag_agent" in raw_output:
            execution_log["detailed_steps"].insert(0, "🎯 Manager Agent routing query to RAG Agent")
        if "Tool #2: query_mcp_agent" in raw_output or "Tool #1: query_mcp_agent" in raw_output:
            execution_log["detailed_steps"].insert(0, "🎯 Manager Agent routing query to MCP Agent")
        
        return response, execution_log
        
    except Exception as e:
        execution_log["execution_time"] = round(time.time() - start_time, 2)
        execution_log["error"] = str(e)
        execution_log["detailed_steps"].append(f"❌ Error occurred: {str(e)}")
        return f"Error: {str(e)}", execution_log

def display_execution_details(execution_log):
    """Display agent execution details in an expandable section"""
    with st.expander("🤔 **Thinking Process & Agent Activity**", expanded=False):
        
        # Execution flow section
        if execution_log['detailed_steps']:
            st.markdown("**🔄 Execution Flow:**")
            for step in execution_log['detailed_steps']:
                st.markdown(f"{step}")
            st.markdown("---")
        
        # Summary statistics in columns
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.markdown("**⏱️ Performance**")
            st.metric("Execution Time", f"{execution_log['execution_time']}s")
            st.markdown(f"🕐 **Started:** {execution_log['timestamp']}")
        
        with col2:
            st.markdown("**🤖 Agents & Tools**")
            if execution_log['agents_called']:
                for agent in execution_log['agents_called']:
                    st.markdown(f"✅ {agent}")
            else:
                st.markdown("ℹ️ No agents detected")
                
            if execution_log['tools_used']:
                st.markdown("**Tools Used:**")
                for tool in execution_log['tools_used']:
                    st.markdown(f"  🛠️ {tool}")
        
        with col3:
            st.markdown("**📊 Results**")
            if execution_log['documents_retrieved']:
                for doc in execution_log['documents_retrieved']:
                    st.markdown(f"📄 {doc}")
            
            if execution_log['calculations_performed']:
                for calc in execution_log['calculations_performed']:
                    st.markdown(f"🧮 {calc}")
        
        # Raw execution log (collapsed by default)
        if execution_log.get('raw_output'):
            with st.expander("🔍 **Detailed Debug Log**", expanded=False):
                st.code(execution_log['raw_output'], language="text")
        
        # Error details if any
        if execution_log.get('error'):
            st.error(f"**Error:** {execution_log['error']}")

# --- UI LAYOUT ---

st.title("📊 Financial Analysis AI System")
st.markdown("*Multi-Agent RAG System for 10-K Document Analysis*")

# Sidebar for document management
with st.sidebar:
    st.header("📁 Document Management")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload 10-K PDF Documents",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more 10-K financial documents"
    )
    
    if uploaded_files:
        st.write(f"📄 {len(uploaded_files)} file(s) selected")
        
        if st.button("🚀 Process & Index Documents", type="primary"):
            # Save uploaded files
            for uploaded_file in uploaded_files:
                file_path = save_uploaded_file(uploaded_file)
                st.success(f"✅ Saved: {uploaded_file.name}")
            
            # Process documents
            if process_documents():
                st.success("✅ Documents indexed successfully!")
                st.balloons()
            else:
                st.error("❌ Failed to process documents")
    
    st.divider()
    
    # System status
    st.header("⚙️ System Status")
    
    if st.session_state.index_ready:
        st.success("✅ Index Ready")
    else:
        st.warning("⚠️ No index found. Upload documents first.")
    
    if st.session_state.manager_agent:
        st.success("✅ Agents Initialized")
    else:
        st.info("ℹ️ Agents not initialized")
        if st.session_state.index_ready:
            if st.button("Initialize Agents"):
                if initialize_agents():
                    st.success("✅ Agents ready!")
                    st.rerun()
    
    st.divider()
    
    # Export options
    st.header("📥 Export Options")
    
    if st.session_state.chat_history:
        # Prepare full conversation for export
        full_conversation = ""
        for message in st.session_state.chat_history:
            role = "**User:**" if message["role"] == "user" else "**AI Assistant:**"
            full_conversation += f"{role}\n{message['content']}\n\n"
        
        # Download as markdown
        st.download_button(
            label="📄 Download as Markdown",
            data=full_conversation,
            file_name=f"financial_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )
    else:
        st.info("No conversation to export yet.")
    
    st.divider()
    
    # Clear chat
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.session_state.agent_logs = {}
        st.rerun()
    
    # Info section
    with st.expander("ℹ️ About This System"):
        st.markdown("""
        **Multi-Agent Architecture:**
        
        1. **RAG Agent**: Retrieves information from documents
        2. **MCP Tool Agent**: Performs financial calculations
        3. **Manager Agent**: Orchestrates and routes queries
        
        **Capabilities:**
        - Document Q&A from 10-K filings
        - Financial ratio calculations
        - Period-over-period comparisons
        - Hybrid retrieval (tables + text)
        
        **Features:**
        - Real-time agent execution tracking
        - Detailed thinking process display
        - Performance metrics
        - Debug logging
        """)

# Display chat history
for i, message in enumerate(st.session_state.chat_history):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show execution details for assistant messages
        if message["role"] == "assistant" and i in st.session_state.agent_logs:
            display_execution_details(st.session_state.agent_logs[i])

# Chat input
if prompt := st.chat_input("Ask a question about the financial documents..."):
    
    # Check if system is ready
    if not st.session_state.index_ready:
        st.error("⚠️ Please upload and process documents first!")
        st.stop()
    
    if not st.session_state.manager_agent:
        st.error("⚠️ Please initialize agents first!")
        st.stop()
    
    # Add user message to chat
    st.session_state.chat_history.append({
        "role": "user",
        "content": prompt
    })
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response from manager agent with execution tracking
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analyzing..."):
            try:
                # Capture agent execution details
                response, execution_log = capture_agent_execution(prompt)
                
                # Store execution log
                message_index = len(st.session_state.chat_history)
                st.session_state.agent_logs[message_index] = execution_log
                
                # Display execution details first (as thinking process)
                display_execution_details(execution_log)
                
                # Then display the main response
                st.markdown("---")
                st.markdown("### 📋 **Final Analysis**")
                st.markdown(str(response))
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": str(response)
                })
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Example queries
with st.expander("💡 Example Queries"):
    st.markdown("""
    **Document Retrieval (RAG Agent):**
    - "What was the total revenue for the year?"
    - "Summarize the risk factors mentioned"
    - "What are the company's main business segments?"
    
    **Calculations (MCP Tool Agent):**
    - "Calculate current ratio with assets 500000 and liabilities 300000"
    - "Compare revenue of 1000000 this year vs 800000 last year"
    
    **Hybrid Queries (Both Agents):**
    - "Find total assets and liabilities, then calculate the debt ratio"
    - "Get Q1 and Q2 revenue figures and show the growth rate"
    """)

# Footer
st.divider()
st.markdown("*Built with AWS Strands Agents, FastMCP, and Amazon Bedrock*")
