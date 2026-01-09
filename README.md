# Financial RAG Assistant with Multi-Agent Architecture

A production-ready, multi-agent financial analysis system combining multi-modal RAG, real-time market data, and automated financial calculations through Model Context Protocol (MCP).

![Multi-Agent Architecture](docs/architecture-diagram.png)

## 🌟 Key Features

### 🤖 Multi-Agent Orchestration
- **Manager Agent**: Intelligent query decomposition and agent coordination
- **RAG Agent**: Multi-modal document retrieval (text, tables, images)
- **Stock Agent**: Real-time market data and news aggregation
- **Calc Agent**: Financial ratio calculations via MCP
- **Reporter Agent**: Comprehensive analysis synthesis

### 📊 Advanced RAG Pipeline
- **Multi-Modal Processing**: Handles text, tables, and images from PDFs
- **Parent-Child Chunking**: Efficient retrieval with context preservation
- **Semantic Search**: AWS Titan embeddings with pgvector
- **Re-ranking**: Jina Reranker v2 for improved relevance
- **Modality-Specific Thresholds**: Optimized similarity scores

### 🧮 Financial Analysis
- Liquidity Ratios (Current, Quick)
- Leverage Ratios (Debt-to-Equity, Debt Ratio)
- Automatic value extraction from documents
- Contextual interpretations with industry benchmarks

### 💻 Modern UI
- Streamlit-based interactive interface
- Real-time agent activity monitoring
- Document upload and ingestion pipeline
- Chat interface with conversation history

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker (for PostgreSQL)
- AWS Account (Bedrock access)
- Google API Key (Gemini)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/patel-aum-yorku/TCS-Exploration.git
cd TCS-Exploration

# 2. Set up environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# 4. Start PostgreSQL
docker run --name financial-rag-db \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_USER=postgres \
  -p 5432:5432 -d pgvector/pgvector:pg17

# 5. Launch application
./start.sh
# OR
python frontend/launcher.py
```

### First Usage

1. **Upload Documents** (Sidebar → Upload Documents)
   - Select PDF files (10-K reports, financial statements)
   - Click "Save Files"

2. **Run Ingestion Pipeline** (Sidebar → Ingestion Pipeline)
   - Click "Run Ingestion Pipeline"
   - Wait for 4-step process to complete

3. **Ask Questions** (Main Chat Interface)
   - Ensure MCP Server is running (🟢)
   - Type your financial question
   - Watch agents collaborate in real-time

## 📋 Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                  STREAMLIT UI (Frontend)                 │
│         Upload → Ingestion → Chat → Monitoring          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│            LANGGRAPH MULTI-AGENT SYSTEM                  │
│                                                           │
│  ┌────────────────────────────────────────────────┐     │
│  │         🧠 Manager Agent (Gemini 2.5)          │     │
│  │    Query Decomposition & Orchestration         │     │
│  └────────────────────────────────────────────────┘     │
│          │              │              │                 │
│          ▼              ▼              ▼                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │  📚 RAG     │ │ 📈 Stock    │ │ 🧮 Calc     │      │
│  │  Agent      │ │ Agent       │ │ Agent       │      │
│  │  (Gemini)   │ │ (Nova Lite) │ │ (Nova Lite) │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
│          │              │              │                 │
│          └──────────────┼──────────────┘                 │
│                         ▼                                 │
│              ┌──────────────────┐                        │
│              │  📊 Reporter     │                        │
│              │  Final Synthesis │                        │
│              └──────────────────┘                        │
└─────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ Vector   │   │  Yahoo   │   │   MCP    │
  │   DB     │   │ Finance  │   │  Server  │
  │(pgvector)│   │   API    │   │  (HTTP)  │
  └──────────┘   └──────────┘   └──────────┘
```

### Technology Stack

**LLM & Orchestration**
- LangChain & LangGraph for agent orchestration
- Google Gemini 2.5 Flash (Manager, RAG)
- AWS Nova Lite (Stock, Calc - cost-optimized)

**Vector Store & Database**
- PostgreSQL with pgvector extension
- AWS Titan Embeddings v2
- Parent-child document storage

**MCP (Model Context Protocol)**
- FastMCP for HTTP server
- Custom financial calculator tools
- Async communication

**Frontend**
- Streamlit for UI
- Real-time agent monitoring
- File upload and ingestion

**Data Processing**
- PyMuPDF for PDF parsing
- LLM-based summarization
- Multi-modal content extraction

## 📁 Project Structure

```
TCS-Exploration/
├── backend/
│   ├── agents/
│   │   ├── graph.py          # LangGraph workflow definition
│   │   ├── tools.py          # RAG, Stock, News tools
│   │   ├── state.py          # Shared agent state
│   │   ├── mcp_client.py     # MCP HTTP client
│   │   └── start_server.py   # MCP server startup
│   ├── mcp_server/
│   │   ├── server.py         # FastMCP HTTP server
│   │   └── calculators.py    # Financial ratio calculations
│   ├── ingestion/
│   │   ├── parser.py         # PDF parsing (text, tables, images)
│   │   └── summarizer.py     # Multi-modal summarization
│   ├── retrieval/
│   │   ├── loader.py         # Vector DB loading
│   │   └── retriever.py      # Multi-modal retrieval with reranking
│   ├── database/
│   │   ├── init_db.py        # Database schema setup
│   │   └── check_db.py       # Database verification
│   └── data/
│       ├── uploads/          # PDF uploads directory
│       └── processed/        # Extracted content (text/tables/images)
├── frontend/
│   ├── app.py               # Main Streamlit application
│   ├── launcher.py          # Application launcher script
│   ├── start_mcp.py         # MCP server starter
│   ├── config.py            # Configuration settings
│   ├── utils.py             # Helper functions
│   └── README.md            # Frontend documentation
├── requirements.txt         # Python dependencies
├── start.sh                # Quick start script (Unix)
├── QUICKSTART.md           # Detailed setup guide
└── README.md               # This file
```

## 🎯 Usage Examples

### Example 1: Comprehensive Analysis
```
Query: "Provide a comprehensive financial analysis of NVDA"

Workflow:
1. 🧠 Manager → Routes to all agents
2. 📚 RAG Agent → Retrieves 10-K sections
3. 📈 Stock Agent → Fetches current market data
4. 🧮 Calc Agent → Computes financial ratios
5. 📊 Reporter → Synthesizes complete report

Output: Multi-page analysis with:
- Business overview from 10-K
- Current market performance
- Liquidity & leverage ratios
- Risk assessment
- Investment recommendations
```

### Example 2: Financial Ratios
```
Query: "Calculate the liquidity and leverage ratios for NVDA"

Workflow:
1. 🧠 Manager → Routes to RAG then Calc
2. 📚 RAG Agent → Retrieves balance sheet data
3. 🧮 Calc Agent → Extracts values via MCP
4. 🧮 Calc Agent → Computes 4 ratios
5. 📊 Reporter → Formats with interpretations

Output:
- Current Ratio: 2.45 (Strong liquidity)
- Quick Ratio: 2.12 (Excellent position)
- Debt-to-Equity: 0.34 (Conservative)
- Debt Ratio: 0.25 (Low leverage)
```

### Example 3: Market Analysis
```
Query: "What is NVDA's current stock price and recent performance?"

Workflow:
1. 🧠 Manager → Routes to Stock agent
2. 📈 Stock Agent → Yahoo Finance API
3. 📊 Reporter → Formats market summary

Output:
- Current price: $X.XX
- Day change: +X.X%
- 52-week range
- Volume analysis
- Recent news sentiment
```

## 🔧 Configuration

### Environment Variables (`.env`)
```env
# Google Gemini API
GOOGLE_API_KEY=your_google_api_key

# AWS Bedrock
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_DEFAULT_REGION=us-east-1

# Optional: Custom settings
MCP_PORT=8000
STREAMLIT_PORT=8501
DB_HOST=localhost
DB_PORT=5432
DB_NAME=financial_rag_db
```

### Database Configuration
Edit `backend/database/init_db.py` for custom database settings.

### LLM Configuration
Edit `backend/agents/graph.py` to change models:
- Manager: `gemini-2.5-flash` (default)
- RAG: `gemini-2.5-flash` (default)
- Stock/Calc: `amazon.nova-lite-v1:0` (default)

## 📊 Performance & Costs

### Typical Query Costs
- **Simple RAG Query**: $0.001 - $0.005
- **Comprehensive Analysis**: $0.01 - $0.03
- **Document Ingestion** (per 100 pages): $0.50 - $2.00

### Optimization Tips
1. Use Nova Lite for non-complex tasks
2. Enable response caching
3. Batch document processing
4. Use specific queries (fewer agent calls)

## 🧪 Testing

### Run Individual Components
```bash
# Test MCP Server
python backend/mcp_server/start_server.py

# Test Ingestion Pipeline
python backend/ingestion/parser.py
python backend/ingestion/summarizer.py
python backend/retrieval/loader.py

# Test Agent System
python backend/agents/graph.py

# Check Database
python backend/database/check_db.py
```

### Run Full System Test
```bash
# Start all services
./start.sh

# Open browser: http://localhost:8501
# Follow "First Usage" steps above
```

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md) - Detailed setup instructions
- [Frontend Documentation](frontend/README.md) - UI features and usage
- [Architecture Deep Dive](docs/architecture.md) - System design details
- [API Documentation](docs/api.md) - MCP server API reference

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is part of the TCS-Exploration initiative.

## 🙏 Acknowledgments

- **LangChain/LangGraph** - Agent orchestration framework
- **FastMCP** - Model Context Protocol implementation
- **AWS Bedrock** - Cost-effective LLM access
- **Google Gemini** - High-quality language models
- **Streamlit** - Rapid UI development

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for financial analysis automation**
