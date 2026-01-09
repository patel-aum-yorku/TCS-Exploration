import operator
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os
import re
import json
from agents.mcp_client import MCPClient

# Set environment variables BEFORE any other imports
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTHONUNBUFFERED"] = "1"

from agents.state import AgentState
from agents.tools import (
    retrieve_financial_docs, 
    get_stock_price, 
    search_financial_news
)


load_dotenv()

# Initialize LLMs based on specifications
# Manager and RAG: Gemini 2.5 Flash
manager_llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

rag_llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    temperature=0.1,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Stock and Calc: Nova Lite (fast and cost-effective)
stock_llm = ChatBedrock(
    model_id="amazon.nova-lite-v1:0",
    region_name="us-east-1", 
    model_kwargs={"temperature": 0}
)

calc_llm = ChatBedrock(
    model_id="amazon.nova-lite-v1:0",
    region_name="us-east-1", 
    model_kwargs={"temperature": 0}
)

# ---------------------------------------------------------
# 1. MANAGER NODE - SINGLE DECISION MAKER
# ---------------------------------------------------------
def manager_node(state: AgentState):
    """
    Manager makes ONE routing decision at a time.
    Uses agent completion flags to avoid recursion.
    """
    query = state["query"]
    rag_data = state.get("rag_data")
    stock_data = state.get("stock_data") 
    calc_data = state.get("calc_data")
    
    # Check which agents have completed
    agents_completed = {
        "rag": rag_data is not None,
        "stock": stock_data is not None,
        "calc": calc_data is not None
    }
    
    print(f"\n🧠 Manager Status: RAG={agents_completed['rag']}, Stock={agents_completed['stock']}, Calc={agents_completed['calc']}")
    
    # If all needed agents are done OR we have at least one substantial result, generate report
    completed_count = sum(agents_completed.values())
    
    if completed_count >= 2:  # At least 2 agents have returned data
        print("✅ Manager: Sufficient data collected, generating report")
        return {"next_step": "report"}
    
    # Determine next agent to call based on query and what's missing
    routing_prompt = f"""You are a financial analysis coordinator. Analyze the query and determine which ONE agent to call next.

USER QUERY: {query}

AGENT STATUS:
- RAG Agent (10-K documents): {'✅ COMPLETED' if agents_completed['rag'] else '❌ NOT CALLED'}
- Stock Agent (market data): {'✅ COMPLETED' if agents_completed['stock'] else '❌ NOT CALLED'}
- Calc Agent (financial ratios): {'✅ COMPLETED' if agents_completed['calc'] else '❌ NOT CALLED'}

ROUTING RULES:
1. If query mentions "10-K", "financial statements", "revenue breakdown", "business segments" → call RAG (if not done)
2. If query mentions "stock price", "current price", "market data", "news" → call Stock (if not done)
3. If query mentions "calculate", "ratio", "liquidity", "leverage", "debt-to-equity", "current ratio" → call Calc (if not done)
4. If query asks for "comprehensive analysis" or "complete picture" → ensure all 3 agents are called
5. Calc agent REQUIRES rag_data to extract financial values from, so call RAG before Calc
6. If at least TWO agents have returned data, you can proceed to 'report'
7. NEVER call an agent that's already completed

Respond with ONLY ONE WORD: rag, stock, calc, or report"""

    response = manager_llm.invoke([HumanMessage(content=routing_prompt)])
    next_step = response.content.strip().lower()
    
    # Prevent calling already-completed agents
    if next_step == "rag" and agents_completed["rag"]:
        next_step = "report"
    elif next_step == "stock" and agents_completed["stock"]:
        next_step = "report"
    elif next_step == "calc" and agents_completed["calc"]:
        next_step = "report"
    
    # Prevent calc from being called before RAG (it needs financial data)
    if next_step == "calc" and not agents_completed["rag"]:
        print("⚠️ Manager: Calc requires RAG data first, routing to RAG")
        next_step = "rag"
    
    print(f"🎯 Manager Decision: Routing to '{next_step}'")
    return {"next_step": next_step}

# ---------------------------------------------------------
# 2. ENHANCED RAG AGENT - BATCH QUERY EXECUTION
# ---------------------------------------------------------
def rag_node(state: AgentState):
    """
    RAG agent executes 2-3 reformulated queries IN ONE CALL.
    This prevents recursion by completing all searches before returning.
    """
    query = state["query"]
    
    print("\n📚 RAG Agent: Analyzing query and reformulating for multi-query search...")
    
    # Step 1: LLM generates 2-3 focused search queries
    reformulation_prompt = f"""You are a RAG specialist analyzing financial queries. Your task is to generate 2-3 focused search queries for vector database retrieval.

USER QUERY: {query}

TASK:
Generate 2-3 distinct search queries that will retrieve the most relevant financial information from 10-K documents and related filings:
1. Remove conversational elements
2. Each query should target a different aspect of the information need
3. Focus on balance sheet items if the query involves calculations (current assets, liabilities, debt, equity, etc.)

Now generate queries for: "{query}"

Respond in this format:
QUERY_1: [first focused query]
QUERY_2: [second focused query]
QUERY_3: [third focused query]"""

    reformulation_response = rag_llm.invoke([HumanMessage(content=reformulation_prompt)])
    reformulation_text = reformulation_response.content.strip()
    
    # Parse the reformulated queries
    search_queries = []
    for line in reformulation_text.split('\n'):
        if line.startswith('QUERY_'):
            query_text = line.split(':', 1)[1].strip() if ':' in line else None
            if query_text:
                search_queries.append(query_text)
    
    # Fallback if parsing fails
    if not search_queries:
        search_queries = [query]
    
    print(f"📝 RAG Agent: Generated {len(search_queries)} search queries")
    for i, sq in enumerate(search_queries, 1):
        print(f"   Query {i}: '{sq}'")
    
    # Step 2: Execute ALL searches and collect results
    all_results = []
    
    for i, search_query in enumerate(search_queries[:3], 1):  # Limit to 3 queries
        print(f"\n🔎 RAG Agent: Executing search {i}/{len(search_queries[:3])}")
        try:
            # This calls your MultiModalRetriever with reranking
            result = retrieve_financial_docs.invoke(search_query)
            
            # Add query context to results
            result_with_context = f"\n--- Search Query {i}: '{search_query}' ---\n{result}"
            all_results.append(result_with_context)
            
        except Exception as e:
            print(f"   ⚠️ RAG Agent: Search {i} failed: {e}")
            all_results.append(f"Search query '{search_query}' failed: {e}")
    
    # Step 3: Combine all results into a single comprehensive response
    if all_results:
        combined_results = "\n\n=== MULTI-QUERY RETRIEVAL RESULTS ===\n".join(all_results)
        
        # Optional: Use LLM to synthesize/deduplicate if results are too long
        if len(combined_results) > 8000:  # Token limit consideration
            synthesis_prompt = f"""Synthesize the following search results, removing duplicates and organizing by topic:

{combined_results}

Provide a structured summary that:
1. Groups similar information together
2. Removes redundant content
3. Preserves all unique financial data and metrics (especially balance sheet items)
4. Maintains source attribution"""
            
            synthesis_response = rag_llm.invoke([HumanMessage(content=synthesis_prompt)])
            combined_results = synthesis_response.content
    else:
        combined_results = "No relevant documents found in any search query."
    
    print(f"✅ RAG Agent: Completed all searches, returning {len(all_results)} result sets")
    
    return {"rag_data": combined_results}

# ---------------------------------------------------------
# 3. ENHANCED STOCK AGENT
# ---------------------------------------------------------
def stock_node(state: AgentState):
    """Fetches stock price data and recent financial news"""
    query = state["query"]
    
    print("\n📈 Stock Agent: Extracting ticker and searching market data...")
    
    # Extract ticker symbol
    extraction_prompt = f"""Extract the company ticker symbol from this query. If not explicit, infer from company name.

Query: {query}

Common tickers: NVDA (Nvidia), AAPL (Apple), MSFT (Microsoft), GOOGL (Google), AMZN (Amazon), TSLA (Tesla)

Respond with ONLY the ticker symbol (e.g., NVDA)"""

    extraction_response = stock_llm.invoke([HumanMessage(content=extraction_prompt)])
    ticker = extraction_response.content.strip().upper()
    
    # Fallback
    if len(ticker) > 5 or not ticker.isalpha():
        ticker = "NVDA"
    
    print(f"📊 Stock Agent: Using ticker '{ticker}'")
    
    try:
        # Fetch stock data
        stock_data = get_stock_price.invoke(ticker)
        
        # Create focused news query
        news_query = f"{ticker} earnings revenue financial results stock"
        news_data = search_financial_news.invoke(news_query)
        
        combined_info = {
            "ticker": ticker,
            "price_data": stock_data,
            "recent_news": news_data
        }
        
        print(f"✅ Stock Agent: Retrieved data for {ticker}")
        
    except Exception as e:
        print(f"⚠️ Stock Agent Error: {e}")
        combined_info = {"error": f"Failed to fetch data for {ticker}: {e}"}
    
    return {"stock_data": combined_info}

# ---------------------------------------------------------
# 4. MCP CALCULATION AGENT (HTTP Transport)
# ---------------------------------------------------------
async def calc_node(state: AgentState):
    """
    Calculation agent that uses MCP server for financial ratio calculations.
    Requires RAG data to extract financial values.
    """
    query = state["query"]
    rag_data = state.get("rag_data", "")
    
    if not rag_data:
        print("⚠️ Calc Agent: No RAG data available, cannot perform calculations")
        return {"calc_data": "Error: RAG data required for calculations"}
    
    print("\n🧮 Calc Agent: Analyzing query to determine required calculations...")
    
    # Use LLM to determine which calculations are needed
    calc_prompt = f"""Analyze this financial query and determine which financial ratios to calculate.

USER QUERY: {query}

Available calculations:
1. Liquidity Ratios (current ratio, quick ratio) - measure short-term financial health
2. Leverage Ratios (debt-to-equity, debt ratio) - measure financial leverage and risk
3. All Ratios - comprehensive financial health assessment

Respond with ONE of: "liquidity", "leverage", or "all"
"""
    
    response = calc_llm.invoke([HumanMessage(content=calc_prompt)])
    calc_type = response.content.strip().lower()
    
    print(f"🎯 Calc Agent: Determined calculation type: {calc_type}")
    
    # Initialize MCP client
    mcp_client = MCPClient()
    
    try:
        print(f"📡 Calc Agent: Connecting to MCP server and requesting {calc_type} calculations...")
        
        # Call appropriate MCP tool based on query analysis
        if "liquidity" in calc_type:
            result = await mcp_client.calculate_liquidity_ratios(rag_data)
        elif "leverage" in calc_type:
            result = await mcp_client.calculate_leverage_ratios(rag_data)
        else:  # default to all ratios
            result = await mcp_client.calculate_all_ratios(rag_data)
        
        # Parse and format the result
        try:
            result_data = json.loads(result)
            
            # Format the output for the reporter
            formatted_output = "## Financial Ratio Analysis\n\n"
            formatted_output += "### Extracted Financial Values\n"
            
            if "extracted_values" in result_data:
                for key, value in result_data["extracted_values"].items():
                    if value is not None:
                        formatted_output += f"- {key.replace('_', ' ').title()}: ${value:,.2f} million\n"
            
            # Format liquidity ratios
            if "liquidity_ratios" in result_data:
                formatted_output += "\n### Liquidity Ratios\n"
                for ratio in result_data["liquidity_ratios"]:
                    if "error" not in ratio:
                        formatted_output += f"\n**{ratio['ratio_name']}**: {ratio['value']}\n"
                        formatted_output += f"- Formula: {ratio['formula']}\n"
                        formatted_output += f"- Interpretation: {ratio['interpretation']}\n"
            
            # Format leverage ratios
            if "leverage_ratios" in result_data:
                formatted_output += "\n### Leverage Ratios\n"
                for ratio in result_data["leverage_ratios"]:
                    if "error" not in ratio:
                        formatted_output += f"\n**{ratio['ratio_name']}**: {ratio['value']}\n"
                        formatted_output += f"- Formula: {ratio['formula']}\n"
                        formatted_output += f"- Interpretation: {ratio['interpretation']}\n"
            
            # Format single ratios list (from liquidity/leverage only calls)
            if "ratios" in result_data:
                formatted_output += "\n### Calculated Ratios\n"
                for ratio in result_data["ratios"]:
                    if "error" in ratio:
                        formatted_output += f"\n**{ratio['ratio_name']}**: {ratio['error']}\n"
                    else:
                        formatted_output += f"\n**{ratio['ratio_name']}**: {ratio['value']}\n"
                        formatted_output += f"- Formula: {ratio['formula']}\n"
                        formatted_output += f"- Interpretation: {ratio['interpretation']}\n"
            
            print(f"✅ Calc Agent: Successfully calculated {calc_type} ratios")
            
            return {"calc_data": formatted_output}
            
        except json.JSONDecodeError:
            # If result is already formatted string
            return {"calc_data": result}
    
    except Exception as e:
        error_msg = f"Error during MCP calculation: {str(e)}"
        print(f"⚠️ Calc Agent: {error_msg}")
        return {"calc_data": error_msg}
    
    finally:
        await mcp_client.close()

# ---------------------------------------------------------
# 5. REPORTER NODE - FINAL SYNTHESIS
# ---------------------------------------------------------
def reporter_node(state: AgentState):
    """Generates comprehensive financial analysis report"""
    print("\n📊 Reporter: Synthesizing final comprehensive report...")
    
    query = state["query"]
    rag_context = state.get("rag_data", "No document data available.")
    stock_context = state.get("stock_data", "No stock data available.")
    calc_context = state.get("calc_data", "No calculations performed.")
    
    report_prompt = f"""You are a senior financial analyst creating a comprehensive report for an institutional investor.

USER QUERY: {query}

--- 📚 FINANCIAL DOCUMENTS & 10-K DATA ---
{rag_context}

--- 📈 MARKET DATA & NEWS ---
{stock_context}

--- 🧮 FINANCIAL RATIOS & CALCULATIONS ---
{calc_context}

INSTRUCTIONS:
Create a professional, well-structured financial analysis report that:

1. **Executive Summary**: 2-3 sentence overview answering the core query
2. **Key Findings**: Bullet points of the most important insights
3. **Detailed Analysis**: 
   - Integrate information from all available sources
   - Provide specific numbers, percentages, and metrics
   - Compare trends over time when data is available
   - Contextualize findings (industry benchmarks, historical context)
4. **Financial Health Assessment** (if calc data available):
   - Interpret liquidity ratios (current ratio, quick ratio)
   - Interpret leverage ratios (debt-to-equity, debt ratio)
   - Overall financial position assessment
5. **Data Quality & Limitations**: 
   - Note any missing information
   - Highlight data recency and reliability
6. **Investment Implications** (if relevant):
   - What this means for investors
   - Risk factors to consider

FORMAT REQUIREMENTS:
- Use markdown headers (##, ###)
- Include relevant numbers with context
- Be objective and data-driven
- If data is limited, be explicit about it
- Do not fabricate information
- When presenting ratios, explain what they mean in plain language"""

    response = manager_llm.invoke([HumanMessage(content=report_prompt)])
    
    print("✅ Reporter: Comprehensive report generated")
    return {"messages": [response.content]}

# ---------------------------------------------------------
# 6. BUILD THE GRAPH
# ---------------------------------------------------------
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("manager", manager_node)
workflow.add_node("rag_agent", rag_node) 
workflow.add_node("stock_agent", stock_node)
workflow.add_node("calc_agent", calc_node)
workflow.add_node("reporter", reporter_node)

# Set entry point
workflow.set_entry_point("manager")

# Routing function
def route_next(state):
    return state["next_step"]

# Conditional routing from manager
workflow.add_conditional_edges(
    "manager",
    route_next,
    {
        "rag": "rag_agent",
        "stock": "stock_agent", 
        "calc": "calc_agent",
        "report": "reporter"
    }
)

# All agents return to manager for next decision
workflow.add_edge("rag_agent", "manager")
workflow.add_edge("stock_agent", "manager")  
workflow.add_edge("calc_agent", "manager")

# Reporter is terminal
workflow.add_edge("reporter", END)

# Compile with reasonable recursion limit
app = workflow.compile()

# ---------------------------------------------------------
# 7. EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Test queries
        test_queries = [
            
            "Calculate the liquidity and leverage ratios for NVDA based on their 10-K"
            
        ]
        
        for query in test_queries[:1]:  # Test with first query
            print(f"\n{'='*80}")
            print(f"🚀 QUERY: {query}")
            print(f"{'='*80}")
            
            initial_state = {
                "query": query,
                "messages": [],
                "rag_data": None,
                "stock_data": None, 
                "calc_data": None,
                "next_step": "start"
            }
            
            # Run with recursion limit safety
            config = {"recursion_limit": 20}
            
            try:
                result = None
                async for output in app.astream(initial_state, config=config):
                    for key, value in output.items():
                        if key == "reporter":
                            result = value['messages'][0]
                
                if result:
                    print(f"\n{'='*80}")
                    print("📊 FINAL COMPREHENSIVE ANALYSIS")
                    print(f"{'='*80}\n")
                    print(result)
                    print(f"\n{'='*80}\n")
                    
            except Exception as e:
                print(f"❌ Error during execution: {e}")
                import traceback
                traceback.print_exc()

    asyncio.run(main())