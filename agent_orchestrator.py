"""
AWS Strands Agents Multi-Agent Orchestration System
Uses MCP server for financial calculations (no duplication!)
"""
import os
from typing import List, Dict, Any
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
import boto3

# --- CONFIG ---
INDEX_FOLDER = "faiss_index_hybrid"
BEDROCK_REGION = "us-east-1"
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"

# Initialize Bedrock client (uses IAM credentials)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=BEDROCK_REGION)


# ===========================
# RAG TOOLS FOR STRANDS AGENT
# ===========================

class RAGContext:
    """Shared context for RAG operations"""
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Global RAG context (will be initialized in setup)
rag_context = None

@tool
def retrieve_financial_documents(query: str) -> str:
    """
    Retrieve relevant financial information from indexed 10-K documents.
    Use this tool when you need to find specific information from company financial reports.
    
    Args:
        query: The question or topic to search for in the documents
    
    Returns:
        Relevant context from financial documents with source citations
    """
    if rag_context is None:
        return "Error: Document index not initialized. Please upload and process documents first."
    
    try:
        # Add debug logging to verify the retriever is working
        print(f"🔍 RAG Query: {query}")
        print(f"🔧 Using retriever: {type(rag_context.retriever)}")
        
        # Make the actual call to FAISS retriever
        docs = rag_context.retriever.invoke(query)  # Changed from get_relevant_documents to invoke
        
        print(f"📄 Retrieved {len(docs)} documents")
        
        if not docs:
            return "No relevant information found in the documents for this query."
        
        # Format retrieved documents with metadata
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', 'Unknown')
            doc_type = doc.metadata.get('type', 'Unknown')
            
            print(f"   Document {i}: {source} (Page {page})")
            
            context_parts.append(
                f"--- Document {i} ---\n"
                f"Source: {source}\n"
                f"Page: {page}\n"
                f"Type: {doc_type}\n"
                f"Content:\n{doc.page_content}\n"
            )
        
        return "\n\n".join(context_parts)
    
    except Exception as e:
        print(f"❌ RAG Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error retrieving documents: {str(e)}"


# ===========================
# STRANDS AGENT DEFINITIONS
# ===========================

def create_rag_agent():
    """
    Create a RAG-focused agent using Strands
    Specializes in retrieving information from financial documents
    """
    system_prompt = """You are a financial document analyst specializing in retrieving and interpreting information from 10-K filings and financial reports.

Your responsibilities:
- Search through indexed financial documents to find relevant information
- Cite specific sources and page numbers when providing information
- Present financial data accurately and clearly
- Always use the retrieve_financial_documents tool to answer questions about document content

When you retrieve documents:
1. Carefully read all retrieved content
2. Synthesize information from multiple sources if needed
3. Cite your sources (document name and page number)
4. If information is not found, clearly state that
"""
    
    rag_agent = Agent(
        name="RAG_Agent",
        model=BedrockModel(),
        tools=[retrieve_financial_documents],
        system_prompt=system_prompt
    )
    
    return rag_agent


def create_mcp_agent():
    """
    Create an MCP tool agent using Strands
    Uses the FastMCP server for financial calculations (NO DUPLICATION!)
    """
    
    print("🔌 Connecting to FastMCP server...")
    
    # Connect to the MCP server
    mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="python",  # or "python3" depending on your system
            args=["mcp_server.py"]
        )
    ))
    
    # Get tools from MCP server using context manager to establish connection
    try:
        # Temporarily open connection to get tools
        with mcp_client:
            mcp_tools = mcp_client.list_tools_sync()
            print(f"✅ Loaded {len(mcp_tools)} tools from MCP server")
            
            # Fix: Use the correct attribute to get tool names
            for tool in mcp_tools:
                # Try different possible attributes for the tool name
                tool_name = getattr(tool, 'name', None) or getattr(tool, 'function_name', None) or str(tool)
                print(f"   - {tool_name}")
        
        # After getting tools, the connection closes but mcp_client retains the tool definitions
        
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to MCP server: {e}")
        print("   Creating agent without MCP tools. Run: python mcp_server.py")
        mcp_tools = []
    
    system_prompt = """You are a financial calculation specialist with expertise in financial ratios, metrics, and period-over-period analysis.

Your responsibilities:
- Perform financial calculations accurately using your available tools
- Calculate ratios like current ratio, debt-to-equity, profit margins
- Compare metrics across time periods
- Provide interpretation and context for calculated values
- Extract and identify financial metrics from text

Available MCP tools:
- calculate_ratio: For computing financial ratios
- compare_periods: For period comparisons and growth rates
- extract_metrics: For identifying metrics in text

Always provide clear explanations of your calculations and what the results mean.
"""
    
    mcp_agent = Agent(
        name="MCP_Agent",
        model=BedrockModel(),
        tools=mcp_tools,
        system_prompt=system_prompt
    )
    
    return mcp_agent, mcp_client


def create_manager_agent(rag_agent: Agent, mcp_agent: Agent, mcp_client):
    """
    Create a manager agent using Strands
    Orchestrates between RAG and MCP agents using sub-agents as tools
    """
    
    @tool
    def query_rag_agent(question: str) -> str:
        """
        Query the RAG agent to retrieve information from financial documents.
        Use this when you need to find specific information from 10-K filings or financial reports.
        
        Args:
            question: Question about financial document content
        
        Returns:
            Answer from RAG agent with document citations
        """
        response = rag_agent(question)
        return str(response)
    
    @tool
    def query_mcp_agent(task: str) -> str:
        """
        Query the MCP agent to perform financial calculations or analysis.
        Use this when you need to calculate ratios, compare periods, or analyze metrics.
        The MCP agent has access to specialized financial calculation tools.
        
        Args:
            task: Description of the calculation or analysis needed
        
        Returns:
            Calculation results with interpretation from MCP tools
        """
        try:
            # Use MCP client context manager when calling the agent
            with mcp_client:
                response = mcp_agent(task)
                return str(response)
        except Exception as e:
            return f"Error calling MCP agent: {str(e)}"
    
    system_prompt = """You are an intelligent orchestrator managing specialized financial analysis agents.

You coordinate between two specialized agents:
1. RAG_Agent: Retrieves information from financial documents (10-K filings)
   - Use for: "What was the revenue?", "Show risk factors", "Find cash flow data"

2. MCP_Agent: Performs financial calculations using MCP tools
   - Use for: "Calculate current ratio", "Compare Q1 vs Q2", "Extract metrics from text"

Your decision-making process:
- If the query asks for information FROM documents → use query_rag_agent
- If the query asks for CALCULATIONS or COMPARISONS → use query_mcp_agent
- If the query needs BOTH retrieval AND calculation → use both tools in sequence:
  1. First, query_rag_agent to get data from documents
  2. Then, query_mcp_agent to perform calculations on that data

Examples of both-needed queries:
- "Get total assets and liabilities, then calculate debt ratio"
- "Find revenue figures and calculate growth rate"
- "Retrieve balance sheet data and compute current ratio"

Always provide clear, complete answers by combining results from the appropriate agents.
"""
    
    manager_agent = Agent(
        name="Manager_Agent",
        model=BedrockModel(),
        tools=[query_rag_agent, query_mcp_agent],
        system_prompt=system_prompt
    )
    
    return manager_agent


# ===========================
# SYSTEM INITIALIZATION
# ===========================

def initialize_system():
    """
    Initialize the AWS Strands multi-agent system with MCP integration
    """
    global rag_context
    
    print("🚀 Initializing AWS Strands Multi-Agent System")
    print("=" * 60)
    
    # 1. Setup embeddings
    print("🔧 Setting up embeddings...")
    embeddings = BedrockEmbeddings(
        client=bedrock_runtime,
        model_id=EMBEDDING_MODEL_ID
    )
    print(f"✅ Embeddings initialized: {EMBEDDING_MODEL_ID}")
    
    # 2. Load FAISS index
    print(f"🔧 Loading FAISS index from {INDEX_FOLDER}...")
    if not os.path.exists(INDEX_FOLDER):
        raise ValueError(
            f"❌ FAISS index not found at {INDEX_FOLDER}\n"
            f"Please run: python ingest_hybrid.py"
        )
    
    vectorstore = FAISS.load_local(
        INDEX_FOLDER,
        embeddings,
        allow_dangerous_deserialization=True
    )
    print(f"✅ FAISS index loaded successfully")
    
    # 3. Initialize RAG context
    rag_context = RAGContext(vectorstore)
    print("✅ RAG context initialized")
    
    # 4. Create Strands agents
    print("\n🤖 Creating Strands agents...")
    
    rag_agent = create_rag_agent()
    print(f"✅ {rag_agent.name} created")
    
    mcp_agent, mcp_client = create_mcp_agent()
    print(f"✅ {mcp_agent.name} created (using MCP server tools)")
    
    manager_agent = create_manager_agent(rag_agent, mcp_agent, mcp_client)
    print(f"✅ {manager_agent.name} created")
    
    print("\n" + "=" * 60)
    print("✅ Strands Multi-Agent System Ready!")
    print("   - RAG Agent: Uses FAISS vector store")
    print("   - MCP Agent: Uses FastMCP server tools")
    print("   - Manager: Orchestrates both agents")
    print("=" * 60 + "\n")
    
    return manager_agent, mcp_client


# ===========================
# CLI TESTING
# ===========================

if __name__ == "__main__":
    try:
        manager, mcp_client = initialize_system()
        
        print("🧪 Running test queries...\n")
        
        test_queries = [
            "What are the company's main business segments?",
            "Calculate the current ratio if assets are 200000 and liabilities are 300000",
            "Compare revenue of 800000 this year vs 800000 last year",
            "Find total assets and liabilities, then calculate the debt ratio"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'#' * 60}")
            print(f"TEST {i}/{len(test_queries)}")
            print(f"{'#' * 60}")
            print(f"Query: {query}\n")
            
            # Invoke the manager agent
            result = manager(query)
            
            print(f"\n📊 RESPONSE:")
            print(result)
            
            if i < len(test_queries):
                input("\nPress Enter for next test...")
        
        print(f"\n{'=' * 60}")
        print("✅ All tests complete!")
        print(f"{'=' * 60}")
        
    except KeyboardInterrupt:
        print("\n\n👋 Testing interrupted")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup MCP client if needed
        print("\n🧹 Cleaning up...")