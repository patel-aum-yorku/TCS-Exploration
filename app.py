"""
Streamlit UI for Multi-Agent Financial Analysis System
"""
import streamlit as st
import os
import sys
from pathlib import Path
import subprocess
import time

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
    
    # Clear chat
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
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
        """)

# Main chat interface
st.header("💬 Chat Interface")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata" in message:
            with st.expander("🔍 View Details"):
                st.json(message["metadata"])

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
    
    # Get response from manager agent
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analyzing..."):
            try:
                # Call the agent directly (not .execute())
                response = st.session_state.manager_agent(prompt)
                
                # Display answer
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
