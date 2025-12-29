# TCS Exploration: Multi-Agent Financial Analysis System

A sophisticated multi-agent system for analyzing 10-K financial documents using AWS Strands Agents, RAG (Retrieval-Augmented Generation), and MCP (Model Context Protocol) tools.

## 🏗️ Architecture

### Multi-Agent Design
- **RAG Agent**: Retrieves information from indexed financial documents using FAISS vector store
- **MCP Tool Agent**: Performs financial calculations using FastMCP server tools
- **Manager Agent**: Orchestrates between RAG and MCP agents based on query type

### Key Technologies
- **AWS Strands Agents**: Multi-agent orchestration framework
- **Amazon Bedrock**: LLM inference (Claude Sonnet) and embeddings (Titan V2)
- **FAISS**: Vector database for document retrieval
- **FastMCP**: Tool server for financial calculations
- **Streamlit**: Web UI for interactive analysis

## 📋 Prerequisites

### AWS Setup
1. **AWS Account** with Bedrock access
2. **AWS CLI** configured with appropriate credentials
3. **IAM permissions** for Bedrock runtime access
4. **Bedrock models enabled**:
   - `amazon.titan-embed-text-v2:0` (embeddings)
   - `anthropic.claude-3-5-sonnet-20241022-v2:0` (LLM)

### Python Environment
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install boto3 langchain-aws langchain-community
pip install faiss-cpu pdfplumber streamlit
pip install strands-agents fastmcp
```

### Environment Variables (macOS fix)
```bash
# Fix OpenMP library conflict on macOS
export KMP_DUPLICATE_LIB_OK=TRUE
```

## 📁 Project Structure

```
TCS-Exploration/
├── agent_orchestrator.py    # Main multi-agent system
├── mcp_server.py            # FastMCP financial tools server
├── ingest_hybrid.py         # Document processing & indexing
├── app.py                   # Streamlit web interface
├── Docs/                    # PDF documents folder
└── faiss_index_hybrid/      # Generated FAISS index
```

## 🚀 Quick Start

### 1. Document Processing
Place your 10-K PDF files in the `Docs/` folder, then run:

```bash
python ingest_hybrid.py
```

This creates a hybrid index that preserves:
- **Tables**: Converted to Markdown format (kept whole)
- **Text**: Split into 1000-character chunks with 100-character overlap

### 2. CLI Testing
Test the multi-agent system directly:

```bash
python agent_orchestrator.py
```

Sample test queries:
- "What are the company's main business segments?" (RAG)
- "Calculate current ratio if assets are 500000 and liabilities are 300000" (MCP)
- "Find total assets and liabilities, then calculate debt ratio" (Hybrid)

### 3. Web Interface
Launch the Streamlit app:

```bash
streamlit run app.py
```

Features:
- Document upload and processing
- Real-time agent initialization
- Interactive chat interface
- Example query suggestions

## 🛠️ Core Components

### RAG Agent (`agent_orchestrator.py`)
```python
@tool
def retrieve_financial_documents(query: str) -> str:
    """Retrieve relevant financial information from indexed 10-K documents."""
    # Uses FAISS retriever with k=5 similarity search
    # Returns formatted results with source citations
```

### MCP Tools Server (`mcp_server.py`)
```python
@mcp.tool()
def calculate_ratio(metric_name: str, numerator: float, denominator: float) -> dict:
    """Calculate financial ratios with interpretation."""

@mcp.tool()
def compare_periods(metric_name: str, current_value: float, previous_value: float) -> dict:
    """Compare financial metrics across time periods."""

@mcp.tool()
def extract_metrics(text: str) -> dict:
    """Extract financial keywords from text."""
```

### Manager Agent Orchestration
```python
# Decision logic for routing queries:
# Document retrieval → RAG Agent
# Calculations → MCP Agent  
# Both needed → Sequential execution
```

### Hybrid Document Processing (`ingest_hybrid.py`)
```python
# Strategy 1: Extract tables as Markdown (preserve structure)
tables = page.find_tables()
md_table = table_to_markdown(table_data)

# Strategy 2: Extract text and split normally
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
```

## 💡 Usage Examples

### Document Retrieval Queries
```
"What was the total revenue mentioned in the document?"
"Summarize the risk factors section"
"What are the company's main business segments?"
```

### Financial Calculation Queries
```
"Calculate the current ratio if assets are 500000 and liabilities are 300000"
"Compare revenue of 1000000 this year vs 800000 last year"
"Extract financial metrics from this text: [financial statement text]"
```

### Hybrid Queries (RAG + MCP)
```
"Find total assets and liabilities, then calculate the debt ratio"
"Get Q1 and Q2 revenue figures and show the growth rate"
"Retrieve balance sheet data and compute current ratio"
```

## 🔧 Configuration

### AWS Bedrock Settings (`agent_orchestrator.py`)
```python
INDEX_FOLDER = "faiss_index_hybrid"
BEDROCK_REGION = "us-east-1" 
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
```

### Document Processing Settings (`ingest_hybrid.py`)
```python
DOCS_FOLDER = "Docs"
INDEX_FOLDER = "faiss_index_hybrid"
# Text chunking: 1000 chars, 100 overlap
# Tables: Preserved whole as Markdown
```

## 🐛 Troubleshooting

### OpenMP Library Conflict (macOS)
```bash
export KMP_DUPLICATE_LIB_OK=TRUE
python agent_orchestrator.py
```

### MCP Server Connection Issues
1. Ensure MCP server starts properly:
   ```bash
   python mcp_server.py
   ```
   Look for: "✅ Server ready for MCP connections"

2. Check agent initialization:
   ```
   ✅ Loaded 3 tools from MCP server
   ✅ MCP_Agent created (using MCP server tools)
   ```

### FAISS Index Issues
```bash
# Recreate index if corrupted
rm -rf faiss_index_hybrid/
python ingest_hybrid.py
```

### Bedrock Access Issues
- Verify AWS credentials: `aws sts get-caller-identity`
- Enable required models in AWS Bedrock console
- Check IAM permissions for `bedrock:InvokeModel`

## 🎯 Key Features

- **Hybrid RAG**: Preserves table structure while enabling text search
- **Multi-Agent Orchestration**: Intelligent routing between specialized agents
- **MCP Integration**: Standardized tool protocol for financial calculations
- **AWS Bedrock**: Enterprise-grade LLM and embeddings
- **Interactive UI**: Streamlit interface for easy document analysis
- **Robust Error Handling**: Graceful fallbacks and detailed logging

## 📊 Performance Notes

- **Embedding Model**: Titan V2 optimized for financial documents
- **Retrieval**: Top-5 similarity search with source citations
- **Chunking Strategy**: Balanced for tables (whole) vs text (chunked)
- **Agent Context**: Specialized prompts for domain expertise

## 🔮 Future Enhancements

- [ ] Multi-document comparison capabilities
- [ ] Advanced financial ratio analysis
- [ ] Time series analysis tools
- [ ] Export functionality for reports
- [ ] Integration with additional data sources

---

**Built with AWS Strands Agents, FastMCP, and Amazon Bedrock**
