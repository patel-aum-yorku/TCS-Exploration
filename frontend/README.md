# Financial RAG Assistant - Frontend

A Streamlit-based user interface for the Multi-Agent Financial RAG System.

## Features

### 📁 Document Management
- **File Upload**: Upload PDF files (10-K reports, financial statements)
- **Ingestion Pipeline**: Process documents through complete pipeline
  - Parse PDFs (extract text, tables, images)
  - Generate summaries for each modality
  - Load into vector database with embeddings

### 💬 Chat Interface
- Interactive chat with multi-agent system
- Real-time agent activity monitoring
- Support for:
  - RAG queries (10-K document retrieval)
  - Stock data queries (real-time market data)
  - Financial ratio calculations (via MCP)
  - Comprehensive financial analysis

### 🖥️ MCP Server Management
- Start/Stop MCP calculation server from UI
- Server status monitoring
- Automatic health checks

### 🔍 Agent Activity Monitoring
- Real-time logs of agent decisions
- Track which agents are called
- See the thought process of the system

## Installation

1. **Install dependencies**:
```bash
pip install streamlit httpx psycopg2-binary
```

2. **Ensure backend is set up**:
   - PostgreSQL database running
   - AWS credentials configured
   - Google API key set

## Usage

### Starting the Application

**Option 1: Manual (Recommended for development)**

1. Start MCP Server (Terminal 1):
```bash
cd frontend
python start_mcp.py
```

2. Start Streamlit UI (Terminal 2):
```bash
cd frontend
streamlit run app.py
```

**Option 2: From Streamlit UI**

1. Start only Streamlit:
```bash
streamlit run frontend/app.py
```

2. Use the "▶️ Start MCP Server" button in the sidebar

### Using the Application

#### 1. Upload Documents
1. Click "Browse files" in the sidebar
2. Select one or more PDF files
3. Click "💾 Save Files"
4. Files are saved to `backend/data/uploads/`

#### 2. Run Ingestion Pipeline
1. After uploading files, click "🚀 Run Ingestion Pipeline"
2. Monitor progress through 4 steps:
   - Database initialization
   - PDF parsing
   - Summary generation
   - Vector database loading
3. Wait for completion (may take several minutes for large documents)

#### 3. Ask Questions
1. Ensure MCP Server is running (green indicator)
2. Type your question in the chat input
3. Click "🚀 Submit"
4. Watch agent activity in the right panel
5. View comprehensive analysis in chat

### Example Queries

- `"Calculate the liquidity and leverage ratios for NVDA based on their 10-K"`
- `"What is NVDA's current stock price and recent performance?"`
- `"Provide a comprehensive financial analysis of NVDA"`
- `"What are NVDA's main revenue sources according to their 10-K?"`
- `"Calculate the current ratio and debt-to-equity ratio for NVDA"`

## Architecture

```
frontend/
├── app.py              # Main Streamlit application
├── utils.py            # Helper functions
├── start_mcp.py        # MCP server startup script
└── README.md           # This file
```

## Features Breakdown

### Sidebar Components

#### MCP Server Control
- **Status Indicator**: Shows if server is running
- **Start/Stop Buttons**: Control server lifecycle
- **Auto-reconnect**: Attempts to reconnect on failure

#### Document Upload
- **Multi-file support**: Upload multiple PDFs at once
- **File validation**: Only accepts PDF files
- **Progress feedback**: Visual confirmation of uploads

#### Ingestion Pipeline
- **4-Step Process**:
  1. Database setup (pgvector extension)
  2. PDF parsing (text, tables, images)
  3. Summary generation (LLM-powered)
  4. Vector database loading (embeddings)
- **Status tracking**: Last ingestion result with timestamp

#### System Information
- **Upload count**: Number of files in uploads folder
- **Processed count**: Number of processed documents
- **Clear chat**: Reset conversation history

### Main Chat Interface

#### Message Display
- **User messages**: Blue background, right-aligned
- **Assistant messages**: Gray background, left-aligned
- **Markdown support**: Rich text formatting in responses
- **Timestamps**: Track conversation timeline

#### Query Input
- **Text area**: Multi-line input for complex queries
- **Submit button**: Send query to agents
- **Examples button**: Show sample queries

### Agent Activity Panel

#### Real-time Logging
- **Manager decisions**: See routing choices
- **Agent calls**: Track RAG, Stock, Calc agents
- **Status updates**: Real-time progress
- **Last 10 logs**: Recent activity history

#### Visual Indicators
- 🧠 Manager Agent
- 📚 RAG Agent
- 📈 Stock Agent
- 🧮 Calc Agent
- 📊 Reporter Agent

## Troubleshooting

### MCP Server Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process if needed
kill -9 <PID>

# Start manually
python frontend/start_mcp.py
```

### Database Connection Error
```bash
# Ensure PostgreSQL is running
docker ps

# Start PostgreSQL if needed
docker run --name financial-rag-db \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_USER=postgres \
  -p 5432:5432 -d pgvector/pgvector:pg17
```

### Ingestion Pipeline Fails
- **Check AWS credentials**: Ensure Bedrock access
- **Check Google API key**: Verify in `.env` file
- **Check file format**: Only PDFs supported
- **Check disk space**: Ensure sufficient storage

### Agent Queries Timeout
- **Check MCP server**: Ensure it's running
- **Check database**: Verify documents are loaded
- **Check LLM access**: Verify API keys
- **Increase recursion limit**: Modify `config` in graph.py

## Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_DEFAULT_REGION=us-east-1
```

### Database Configuration
Modify `backend/database/init_db.py` if needed:

```python
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": "5432"
}
```

## Performance Tips

1. **Start MCP server before queries**: Avoid cold-start delays
2. **Process documents in batches**: Better for large document sets
3. **Use specific queries**: More targeted = faster responses
4. **Clear chat periodically**: Reduce memory usage
5. **Monitor agent logs**: Identify bottlenecks

## Development

### Running in Development Mode
```bash
# Enable debug mode
streamlit run frontend/app.py --server.runOnSave true

# Enable auto-reload
export STREAMLIT_DEBUG=true
streamlit run frontend/app.py
```

### Testing Components Independently
```bash
# Test MCP server
python backend/mcp_server/start_server.py

# Test ingestion pipeline
python backend/ingestion/parser.py
python backend/ingestion/summarizer.py
python backend/retrieval/loader.py

# Test agent graph
python backend/agents/graph.py
```

## Future Enhancements

- [ ] Add document preview in sidebar
- [ ] Support for multiple document sets
- [ ] Export chat history to PDF
- [ ] Add visualizations for financial ratios
- [ ] Support for Excel/CSV uploads
- [ ] Add user authentication
- [ ] Add conversation memory across sessions
- [ ] Add agent performance metrics

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review terminal logs for errors
3. Verify all services are running
4. Check database connectivity

## License

Part of the TCS-Exploration project.
