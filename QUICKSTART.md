# Quick Start Guide - Financial RAG Assistant

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
Create `.env` file in project root:
```env
GOOGLE_API_KEY=your_google_api_key_here
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### 3. Start the Application
```bash
python frontend/launcher.py
```

That's it! The application will:
- ✅ Check all prerequisites
- ✅ Start MCP server (port 8000)
- ✅ Start Streamlit UI (port 8501)
- ✅ Open browser automatically

---

## 📋 Prerequisites

### Required Services

1. **PostgreSQL with pgvector**
```bash
docker run --name financial-rag-db \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_USER=postgres \
  -p 5432:5432 -d pgvector/pgvector:pg17
```

2. **Python 3.10+**
```bash
python --version  # Should be 3.10 or higher
```

3. **API Keys**
- Google API Key (for Gemini)
- AWS Credentials (for Bedrock)

---

## 🎯 First Time Setup

### Step 1: Start Services
```bash
# Terminal 1: Start PostgreSQL (if not using Docker)
# See above Docker command

# Terminal 2: Launch application
python frontend/launcher.py
```

### Step 2: Upload Documents
1. Open http://localhost:8501
2. Click "Browse files" in sidebar
3. Select your PDF files (10-K reports, etc.)
4. Click "💾 Save Files"

### Step 3: Run Ingestion
1. Click "🚀 Run Ingestion Pipeline" in sidebar
2. Wait for 4 steps to complete:
   - Database initialization
   - PDF parsing (extracts text, tables, images)
   - Summary generation (LLM-powered)
   - Vector database loading
3. See success message when complete

### Step 4: Ask Questions
1. Ensure MCP Server shows 🟢 (green)
2. Type your question in the chat
3. Click "🚀 Submit"
4. Watch agents work in real-time
5. Get comprehensive analysis

---

## 💡 Example Usage

### Example 1: Financial Ratios
**Query:** "Calculate the liquidity and leverage ratios for NVDA based on their 10-K"

**What happens:**
1. 🧠 Manager routes to RAG agent
2. 📚 RAG agent retrieves balance sheet data
3. 🧠 Manager routes to Calc agent
4. 🧮 Calc agent calculates ratios via MCP
5. 📊 Reporter synthesizes final analysis

### Example 2: Stock Analysis
**Query:** "What is NVDA's current stock price and recent performance?"

**What happens:**
1. 🧠 Manager routes to Stock agent
2. 📈 Stock agent fetches Yahoo Finance data
3. 📊 Reporter formats market analysis

### Example 3: Comprehensive Analysis
**Query:** "Provide a comprehensive financial analysis of NVDA"

**What happens:**
1. 🧠 Manager coordinates all agents
2. 📚 RAG agent retrieves 10-K data
3. 📈 Stock agent gets market data
4. 🧮 Calc agent computes ratios
5. 📊 Reporter creates full report

---

## 🛠️ Troubleshooting

### Issue: MCP Server Won't Start
```bash
# Check if port is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Start manually
python frontend/start_mcp.py
```

### Issue: Database Connection Failed
```bash
# Check PostgreSQL is running
docker ps | grep financial-rag-db

# Check connection
psql -h localhost -U postgres -d financial_rag_db
```

### Issue: Ingestion Pipeline Fails
- **Check AWS credentials:** `aws sts get-caller-identity`
- **Check Google API key:** Verify in `.env` file
- **Check disk space:** `df -h`
- **Check logs:** Look at terminal output

### Issue: Agent Query Timeout
- Increase timeout in `frontend/config.py`
- Check MCP server is responding: `curl http://localhost:8000/tools`
- Verify documents are loaded: Check database

---

## 🎓 Advanced Usage

### Manual Component Control

**Start Only MCP Server:**
```bash
python frontend/start_mcp.py
```

**Start Only Streamlit:**
```bash
streamlit run frontend/app.py
```

**Run Ingestion Pipeline (CLI):**
```bash
# Parse PDFs
python -c "from backend.ingestion.parser import PDFParser; PDFParser().process_all()"

# Generate summaries
python -c "from backend.ingestion.summarizer import MultiModalSummarizer; import asyncio; s = MultiModalSummarizer(); asyncio.run(s.process_all_documents())"

# Load to database
python -c "from backend.retrieval.loader import DataLoader; DataLoader().load_all_documents()"
```

**Test Agent System (CLI):**
```bash
python backend/agents/graph.py
```

### Database Management

**Check Database:**
```bash
python backend/database/check_db.py
```

**Reset Database:**
```bash
# Drop and recreate
docker exec -it financial-rag-db psql -U postgres -c "DROP DATABASE financial_rag_db;"
python backend/database/init_db.py
```

### Development Mode

**Enable Streamlit Debug:**
```bash
export STREAMLIT_DEBUG=true
streamlit run frontend/app.py --server.runOnSave true
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT UI                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Upload     │  │  Ingestion   │  │     Chat     │ │
│  │  Documents   │  │   Pipeline   │  │  Interface   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              LANGGRAPH AGENT SYSTEM                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │            🧠 Manager Agent                       │  │
│  └──────────────────────────────────────────────────┘  │
│        │              │              │                   │
│        ▼              ▼              ▼                   │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐            │
│  │ 📚 RAG  │    │ 📈 Stock│    │ 🧮 Calc │            │
│  │  Agent  │    │  Agent  │    │  Agent  │            │
│  └─────────┘    └─────────┘    └─────────┘            │
│        │              │              │                   │
│        └──────────────┼──────────────┘                   │
│                       ▼                                   │
│              ┌──────────────┐                            │
│              │ 📊 Reporter  │                            │
│              └──────────────┘                            │
└─────────────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Vector   │   │  Yahoo   │   │   MCP    │
    │   DB     │   │ Finance  │   │  Server  │
    │(pgvector)│   │   API    │   │  (HTTP)  │
    └──────────┘   └──────────┘   └──────────┘
```

---

## 📚 Project Structure

```
TCS-Exploration/
├── backend/
│   ├── agents/
│   │   ├── graph.py          # LangGraph workflow
│   │   ├── tools.py          # RAG, Stock tools
│   │   ├── state.py          # Shared state
│   │   └── mcp_client.py     # MCP HTTP client
│   ├── mcp_server/
│   │   ├── server.py         # FastMCP server
│   │   └── calculators.py    # Financial calculators
│   ├── ingestion/
│   │   ├── parser.py         # PDF parsing
│   │   └── summarizer.py     # LLM summarization
│   ├── retrieval/
│   │   ├── loader.py         # Vector DB loading
│   │   └── retriever.py      # Multi-modal retrieval
│   ├── database/
│   │   └── init_db.py        # Database setup
│   └── data/
│       ├── uploads/          # PDF uploads
│       └── processed/        # Extracted content
├── frontend/
│   ├── app.py               # Main Streamlit app
│   ├── launcher.py          # Start script
│   ├── config.py            # Configuration
│   └── utils.py             # Helper functions
├── requirements.txt
├── .env
└── README.md
```

---

## 🎯 Key Features

### Multi-Modal RAG
- Text extraction from PDFs
- Table detection and parsing
- Image extraction and description
- Separate summarization for each modality
- Parent-child chunking strategy

### Multi-Agent System
- **Manager**: Orchestrates agent calls
- **RAG Agent**: Retrieves from 10-K documents
- **Stock Agent**: Fetches real-time market data
- **Calc Agent**: Computes financial ratios via MCP
- **Reporter**: Synthesizes comprehensive analysis

### Financial Calculations (via MCP)
- Current Ratio
- Quick Ratio (Acid-Test)
- Debt-to-Equity Ratio
- Debt Ratio
- Automatic value extraction from documents
- Contextual interpretations

---

## 💰 Cost Optimization

### LLM Usage
- **Manager & RAG**: Gemini 2.5 Flash (low cost)
- **Stock & Calc**: AWS Nova Lite (ultra-low cost)
- **Summarization**: Batched with rate limiting

### Best Practices
1. Process documents in batches
2. Use specific queries (less agent calls)
3. Enable response caching
4. Monitor token usage

---

## 🔒 Security Notes

- Never commit `.env` file
- Use environment variables for secrets
- Rotate API keys regularly
- Restrict database access
- Use HTTPS in production

---

## 📞 Support

For issues:
1. Check logs in terminal
2. Verify all services are running
3. Review troubleshooting section
4. Check database connectivity

---

**Happy Analyzing! 📊🚀**
