# 🔧 Troubleshooting Guide

## Quick Diagnostics

Run this first to check system status:
```bash
python check_status.py
```

---

## Common Issues & Solutions

### 1. 🔴 MCP Server Won't Start

**Symptoms:**
- Error: "Address already in use"
- Port 8000 conflict
- Server immediately crashes

**Solutions:**

```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill the process using port 8000
kill -9 <PID>

# Try starting manually to see error
python frontend/start_mcp.py

# Check for Python errors
python -c "from backend.mcp_server.server import mcp; print('OK')"

# Test MCP server endpoint
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"tools/list","params":{}}'
```

**Common Causes:**
- Another MCP server already running
- Port 8000 used by another application
- Missing dependencies (`pip install fastmcp`)
- Import errors in calculators.py

---

### 2. 🗄️ Database Connection Failed

**Symptoms:**
- "Could not connect to database"
- "Connection refused"
- Ingestion pipeline fails

**Solutions:**

```bash
# Check if PostgreSQL is running
docker ps | grep pgvector

# If not running, start it
docker run --name financial-rag-db \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_USER=postgres \
  -p 5432:5432 -d pgvector/pgvector:pg17

# Wait 5 seconds, then test connection
sleep 5
psql -h localhost -U postgres -d postgres -c "SELECT 1"

# If container exists but stopped
docker start financial-rag-db

# Initialize database
python backend/database/init_db.py

# Verify tables exist
python backend/database/check_db.py
```

**Common Causes:**
- Docker not running
- PostgreSQL container stopped
- Wrong credentials in code
- Port 5432 already in use

---

### 3. 📄 Ingestion Pipeline Fails

**Symptoms:**
- Parsing stage fails
- Summarization hangs
- "Rate limit exceeded"
- Out of memory errors

**Solutions:**

**Step 1: Parse Only**
```bash
python -c "from backend.ingestion.parser import PDFParser; p = PDFParser(); p.process_all()"
```

**Step 2: Check AWS Credentials**
```bash
aws sts get-caller-identity
# Should return your AWS account info
```

**Step 3: Check Google API Key**
```bash
echo $GOOGLE_API_KEY
# Should show your API key
```

**Step 4: Test Summarization (small batch)**
```python
# Edit backend/ingestion/summarizer.py
# Change semaphore limit from 5 to 2
self.semaphore = asyncio.Semaphore(2)
```

**Step 5: Clear and Retry**
```bash
# Remove processed data
rm -rf backend/data/processed/*

# Try again
python backend/ingestion/parser.py
```

**Common Causes:**
- API rate limits hit
- Invalid API keys
- Large PDF files (>100 pages)
- Out of disk space
- Network timeout

---

### 4. 🤖 Agent Query Timeout

**Symptoms:**
- "Recursion limit reached"
- Query hangs forever
- No response from agents

**Solutions:**

```bash
# Test agents directly (bypasses UI)
python backend/agents/graph.py

# Check MCP server is responding
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"tools/list","params":{}}'

# Verify documents in database
python -c "
import psycopg2
conn = psycopg2.connect(
    dbname='financial_rag_db',
    user='postgres',
    password='root',
    host='localhost'
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM documents')
print(f'Documents: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM summaries')
print(f'Summaries: {cur.fetchone()[0]}')
"
```

**Increase Timeouts:**

Edit `backend/agents/graph.py`:
```python
# Change from 20 to 30
config = {"recursion_limit": 30}
```

Edit `frontend/config.py`:
```python
# Change from 300 to 600 (10 minutes)
AGENT_TIMEOUT = 600
```

**Common Causes:**
- No documents in database
- MCP server not running
- Network issues with APIs
- Infinite loop in routing

---

### 5. 🌐 Streamlit Won't Start

**Symptoms:**
- "Port 8501 already in use"
- Blank screen
- Module not found errors

**Solutions:**

```bash
# Kill existing Streamlit
pkill -f streamlit

# Check port availability
lsof -i :8501

# Try starting with different port
streamlit run frontend/app.py --server.port 8502

# Reinstall Streamlit
pip install --upgrade streamlit

# Clear Streamlit cache
rm -rf ~/.streamlit/cache
```

**Common Causes:**
- Another Streamlit instance running
- Corrupted cache
- Import errors in app.py
- Port conflict

---

### 6. 💸 API Rate Limit Exceeded

**Symptoms:**
- "429 Too Many Requests"
- Summarization fails halfway
- "Quota exceeded"

**Solutions:**

**For Google Gemini:**
```python
# Edit backend/ingestion/summarizer.py
# Reduce concurrent requests
self.semaphore = asyncio.Semaphore(2)  # From 5 to 2

# Increase retry delay
base_delay = 5  # From 2 to 5
```

**For AWS Bedrock:**
```bash
# Check your quotas
aws service-quotas list-service-quotas \
  --service-code bedrock \
  --query 'Quotas[?QuotaName==`InvokeModel requests per minute`]'

# Request quota increase if needed
```

**Workaround:**
- Process documents one at a time
- Use smaller batch sizes
- Wait between ingestion runs

---

### 7. 🔑 Invalid API Keys

**Symptoms:**
- "Unauthorized"
- "Invalid API key"
- "Authentication failed"

**Solutions:**

```bash
# Check .env file exists
cat .env

# Verify Google API key format
# Should start with "AIza..."
echo $GOOGLE_API_KEY | grep "^AIza"

# Test Google API
curl "https://generativelanguage.googleapis.com/v1/models?key=$GOOGLE_API_KEY"

# Verify AWS credentials
aws sts get-caller-identity

# Re-export environment variables
source .env
# OR
export $(cat .env | xargs)

# Restart application
```

**Common Causes:**
- Typo in API key
- Expired credentials
- Wrong region for AWS
- API key not activated

---

### 8. 💾 Out of Disk Space

**Symptoms:**
- Ingestion fails silently
- Cannot save uploaded files
- Database errors

**Solutions:**

```bash
# Check disk space
df -h

# Clear processed data (keep originals)
rm -rf backend/data/processed/*/text/*_summary.json
rm -rf backend/data/processed/*/tables/*_summary.json
rm -rf backend/data/processed/*/images/*_summary.json

# Clear old uploads
rm backend/data/uploads/*.pdf

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Clear Docker containers
docker system prune -a
```

---

### 9. 🧮 Calculation Results Incorrect

**Symptoms:**
- Ratios show "Missing required data"
- Values extracted are wrong
- Interpretation seems off

**Solutions:**

**Debug Value Extraction:**
```python
# Test calculator directly
from backend.mcp_server.calculators import FinancialCalculator

# Sample RAG data
test_data = """
Balance Sheet:
Current Assets: $5,000 million
Inventory: $500 million
Current Liabilities: $2,000 million
Total Debt: $3,000 million
Total Assets: $10,000 million
Shareholders Equity: $6,000 million
"""

calc = FinancialCalculator()
values = calc.extract_financial_values(test_data)
print(values)
```

**Improve Pattern Matching:**

Edit `backend/mcp_server/calculators.py` to add more patterns for your document format.

**Common Causes:**
- Different financial statement format
- Values in billions vs millions
- Missing line items in 10-K
- RAG retrieved wrong sections

---

### 10. 🖼️ Images Not Displaying

**Symptoms:**
- Image links broken
- "Image not found"
- Only text/tables retrieved

**Solutions:**

```bash
# Check if images were extracted
ls backend/data/processed/*/images/

# Verify images in database
python -c "
import psycopg2
conn = psycopg2.connect(
    dbname='financial_rag_db',
    user='postgres',
    password='root',
    host='localhost'
)
cur = conn.cursor()
cur.execute(\"SELECT COUNT(*) FROM summaries WHERE modality='image'\")
print(f'Image summaries: {cur.fetchone()[0]}')
"

# Check file permissions
chmod -R 755 backend/data/processed/
```

---

## 🔍 Debug Mode

### Enable Verbose Logging

**For Streamlit:**
```bash
export STREAMLIT_DEBUG=true
streamlit run frontend/app.py --logger.level=debug
```

**For Agents:**
```python
# Edit backend/agents/graph.py
# Add at top:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**For MCP Server:**
```python
# Edit backend/mcp_server/server.py
# Add at top:
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📊 System Health Check

Run comprehensive diagnostics:

```bash
# 1. Check all components
python check_status.py

# 2. Test database
python backend/database/check_db.py

# 3. Test MCP server
curl http://localhost:8000/tools | jq

# 4. Test agents (dry run)
python backend/agents/graph.py

# 5. Check logs
tail -f ~/.streamlit/logs/*.log
```

---

## 🆘 Getting Help

If issues persist:

1. **Collect Information:**
   ```bash
   # System info
   python --version
   docker --version
   
   # Package versions
   pip list | grep -E "streamlit|langchain|fastmcp"
   
   # Error logs
   python check_status.py > status.txt
   ```

2. **Check Documentation:**
   - README.md
   - QUICKSTART.md
   - COMPLETE_OVERVIEW.md
   - frontend/README.md

3. **Common Fixes:**
   - Restart all services
   - Clear cache and retry
   - Update dependencies: `pip install -U -r requirements.txt`
   - Recreate database: Drop and reinitialize

4. **Reset Everything:**
   ```bash
   # Stop all services
   pkill -f streamlit
   pkill -f mcp
   docker stop financial-rag-db
   
   # Clear data
   rm -rf backend/data/processed/*
   rm -rf backend/data/uploads/*
   
   # Restart fresh
   docker start financial-rag-db
   python backend/database/init_db.py
   ./start.sh
   ```

---

## 📞 Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Port conflict | `lsof -i :8000 && kill -9 <PID>` |
| Database down | `docker start financial-rag-db` |
| API error | Check `.env` file |
| MCP offline | `python frontend/start_mcp.py` |
| Streamlit crash | `pkill -f streamlit && streamlit run frontend/app.py` |
| No documents | Run ingestion pipeline |
| Slow queries | Check MCP server running |
| Import errors | `pip install -r requirements.txt` |

---

**Still having issues?** Run `python check_status.py` and fix items marked with ❌
