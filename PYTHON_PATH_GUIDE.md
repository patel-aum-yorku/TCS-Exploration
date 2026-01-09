# 🔧 Complete Path Fix Guide - All Pipeline Files Updated# 🔧 Python Path & Virtual Environment Setup Guide



## Problem## Your Current Situation

Ingestion pipeline was not creating folders in `data/processed/` because all three pipeline files were using hardcoded paths with `"backend/"` prefix.

You mentioned:

## Root Cause1. ❌ Can't run `python script.py` - need to use `python -m module.name`

When running from `/Users/.../TCS-Exploration/backend/`:2. ❌ Getting "No module named 'backend'" in Streamlit UI

- ❌ `"backend/data"` → looks for `backend/backend/data` (WRONG!)

- ✅ `"data"` → looks for `backend/data` (CORRECT!)## Solutions Applied



## Files Fixed (3 Pipeline Components)### ✅ Fixed Import Paths

All `frontend/app.py` imports now work correctly:

### 1. Parser - `backend/ingestion/parser.py` (Line 15)- Changed from `from backend.agents.graph` → `from agents.graph`

```python- Same for all other backend imports

# BEFORE: def __init__(self, base_dir: str = "backend/data"):

# AFTER:  def __init__(self, base_dir: str = "data"):### ✅ Why `-m` is Required (and that's OK!)

```

Your Mac's Python setup is actually **correct**. The `-m` flag is the proper way to run modules:

### 2. Summarizer - `backend/ingestion/summarizer.py` (Lines 20, 213)

```python```bash

# BEFORE: def __init__(self, processed_dir: str = "backend/data/processed"):# ❌ DON'T do this for module code:

# AFTER:  def __init__(self, processed_dir: str = "data/processed"):python script.py



# BEFORE: processed_root = Path("backend/data/processed")# ✅ DO this instead:

# AFTER:  processed_root = Path("data/processed")python -m backend.agents.start_server

``````



### 3. Loader - `backend/retrieval/loader.py` (Line 21)## How to Run Your Application

```python

# BEFORE: def __init__(self, processed_dir: str = "backend/data/processed"):### Step 1: Activate Virtual Environment

# AFTER:  def __init__(self, processed_dir: str = "data/processed"):

```Your terminal shows you have a `.venv`. Activate it first:



## ✅ Next Steps```bash

# From project root

### **Streamlit will auto-reload** - Just run the pipeline again!source .venv/bin/activate



1. Go to **"📁 Document Management"** tab# You should see (.venv) in your prompt

2. Click **"▶️ Start Ingestion Pipeline"**```

3. Watch for `data/processed/nvda/` folder creation

### Step 2: Start MCP Server

### Expected Result:

```**Option A: Using module syntax (recommended)**

data/processed/nvda/```bash

├── text/nvda.md# From project root

├── tables/*.jsonpython -m backend.agents.start_server

├── images/*.png```

├── text_summaries.json

├── table_summaries.json**Option B: Using helper script**

└── image_summaries.json```bash

```# From project root

cd frontend

## Summary: 10 Files Fixed Totalpython start_mcp.py

1-7. Import fixes (completed earlier)```

8-10. Path fixes (just completed):

   - ✅ parser.py### Step 3: Start Streamlit UI

   - ✅ summarizer.py

   - ✅ loader.py**In a NEW terminal** (keep MCP server running):



**All paths now correct! 🎉**```bash

# Activate venv
source .venv/bin/activate

# Run Streamlit
cd frontend
streamlit run app.py
```

### Step 4: Test the Application

1. Open http://localhost:8501
2. Check that MCP Server shows 🟢 (green status)
3. Enter query: "Calculate the liquidity and leverage ratios for NVDA"
4. Click Submit
5. Should now work without "No module named 'backend'" error!

## Fixing Python Command (Optional)

If you want `python` to work instead of needing `python3`:

### Check your Python setup:
```bash
which python
which python3
```

### Create an alias:
```bash
# Add to your ~/.zshrc
echo 'alias python=python3' >> ~/.zshrc
source ~/.zshrc
```

Or better - always use the venv:
```bash
# From project root
source .venv/bin/activate
which python  # Should now point to .venv/bin/python
```

## Quick Reference

### Start Everything (One Command)
```bash
# From project root with venv activated
python frontend/launcher.py
```

This will:
1. ✅ Check all prerequisites
2. ✅ Start MCP server on port 8000
3. ✅ Start Streamlit on port 8501
4. ✅ Open browser automatically

### Manual Start (Two Terminals)

**Terminal 1 (MCP Server):**
```bash
source .venv/bin/activate
python -m backend.agents.start_server
```

**Terminal 2 (Streamlit):**
```bash
source .venv/bin/activate
cd frontend
streamlit run app.py
```

## Verification

After starting both services, run this test:

```bash
# In a third terminal
source .venv/bin/activate
python test_frontend_imports.py
```

Should show:
```
✅ agents.graph imported successfully
✅ ingestion.parser imported successfully
✅ ingestion.summarizer imported successfully
✅ database.init_db imported successfully
✅ retrieval.loader imported successfully
✅ agents.mcp_client imported successfully
```

## Common Issues & Solutions

### Issue: "python: command not found"
**Solution:** Use `python3` or activate your venv first

### Issue: "No module named 'backend'"
**Solution:** ✅ FIXED! Updated all imports in `app.py`

### Issue: "No module named 'fastmcp'" (or other packages)
**Solution:** Make sure venv is activated:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: MCP server shows 🔴 red
**Solution:** Start the server first:
```bash
python -m backend.agents.start_server
```

### Issue: Query fails with import error
**Solution:** ✅ FIXED! Now uses correct import paths

## Status After Fixes

| Component | Status | Notes |
|-----------|--------|-------|
| Import paths | ✅ Fixed | No more "No module named 'backend'" |
| MCP server | ✅ Working | Use `-m` flag to start |
| Streamlit UI | ✅ Ready | Should work after restart |
| Agent queries | ✅ Should work | Test with NVDA query |

## Next Steps

1. **Restart Streamlit** (to load fixed code):
   ```bash
   # Press Ctrl+C in Streamlit terminal
   # Then restart:
   streamlit run app.py
   ```

2. **Test a query** in the UI

3. **Check Agent Activity panel** - should show proper logs now!

---

**Your imports are now fixed! Just restart Streamlit and it should work. 🎉**
