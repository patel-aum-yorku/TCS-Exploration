import yfinance as yf
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from retrieval.retriever import MultiModalRetriever

# Initialize tools
retriever_instance = MultiModalRetriever()
search_tool = DuckDuckGoSearchRun()

# --- 1. ENHANCED RAG TOOL WITH BETTER FORMATTING ---
@tool
def retrieve_financial_docs(query: str) -> str:
    """
    Retrieve relevant text, tables, and images from 10-K documents.
    Returns formatted results with titles, summaries, and content previews.
    """
    print(f"      🔍 Executing vector search: '{query}'")
    
    try:
        # Call your improved MultiModalRetriever with reranking
        results = retriever_instance.retrieve(query, top_k=5, rerank_top_n=15)
        
        if not results:
            return f"No relevant documents found for query: '{query}'"
        
        # Format results with clear structure
        formatted_results = []
        
        for i, res in enumerate(results, 1):
            result_section = f"""
{'─'*60}
SOURCE {i} - {res['modality'].upper()}
{'─'*60}
📌 Title: {res['metadata'].get('title', 'Untitled')}
📊 Relevance Score: {res.get('final_score', res.get('rerank_score', 0)):.4f}
📄 Document: {res.get('doc_id', 'Unknown')}

📝 Summary:
{res['summary']}

📋 Content Preview:
{str(res.get('content', ''))[:600]}...
"""
            formatted_results.append(result_section)
        
        # Combine all results
        final_output = f"\n🎯 Retrieved {len(results)} relevant documents for: '{query}'\n"
        final_output += "\n".join(formatted_results)
        
        return final_output
        
    except Exception as e:
        error_msg = f"⚠️ Error during retrieval for '{query}': {str(e)}"
        print(error_msg)
        return error_msg

# --- 2. ENHANCED STOCK TOOL WITH COMPREHENSIVE DATA ---
@tool
def get_stock_price(ticker: str) -> dict:
    """
    Get comprehensive stock data including price, metrics, and historical trends.
    Returns structured dictionary with all relevant market information.
    """
    print(f"      📈 Fetching stock data for: {ticker}")
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data for trend analysis
        hist = stock.history(period="1y")
        
        # Calculate price changes
        current_price = info.get("currentPrice", hist['Close'].iloc[-1] if not hist.empty else None)
        
        # 52-week performance
        week_52_high = info.get("fiftyTwoWeekHigh")
        week_52_low = info.get("fiftyTwoWeekLow")
        
        pct_from_high = None
        if current_price and week_52_high:
            pct_from_high = ((current_price - week_52_high) / week_52_high) * 100
        
        # Build comprehensive data structure
        stock_data = {
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            
            # Price Data
            "current_price": current_price,
            "currency": info.get("currency", "USD"),
            "day_change": info.get("regularMarketChange"),
            "day_change_percent": info.get("regularMarketChangePercent"),
            
            # Volume & Market Cap
            "volume": info.get("volume"),
            "avg_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            
            # 52-Week Range
            "52_week_high": week_52_high,
            "52_week_low": week_52_low,
            "pct_from_52w_high": pct_from_high,
            
            # Valuation Metrics
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            
            # Profitability
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            
            # Dividends
            "dividend_yield": info.get("dividendYield"),
            "dividend_rate": info.get("dividendRate"),
            
            # Other Metrics
            "beta": info.get("beta"),
            "eps": info.get("trailingEps"),
            "forward_eps": info.get("forwardEps"),
            "revenue": info.get("totalRevenue"),
            "revenue_per_share": info.get("revenuePerShare"),
            
            # Analyst Recommendations
            "target_mean_price": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey"),
            "num_analysts": info.get("numberOfAnalystOpinions")
        }
        
        print(f"      ✅ Successfully fetched data for {ticker}")
        return stock_data
        
    except Exception as e:
        error_msg = f"Error fetching stock data for {ticker}: {str(e)}"
        print(f"      ⚠️ {error_msg}")
        return {"ticker": ticker, "error": error_msg}

# --- 3. FINANCIAL NEWS SEARCH TOOL ---
@tool  
def search_financial_news(query: str) -> str:
    """
    Search for recent financial news and analysis using DuckDuckGo.
    Returns summarized news results relevant to the query.
    """
    print(f"      📰 Searching financial news: '{query}'")
    
    try:
        # Enhance query with financial keywords
        enhanced_query = f"{query} financial news stock market latest"
        results = search_tool.run(enhanced_query)
        
        # Limit results to prevent token overflow
        if len(results) > 3000:
            results = results[:3000] + "\n\n... [results truncated for length]"
        
        print(f"      ✅ News search completed")
        return results
        
    except Exception as e:
        error_msg = f"Error searching financial news: {str(e)}"
        print(f"      ⚠️ {error_msg}")
        return error_msg



# Export all tools
agent_tools = [
    retrieve_financial_docs, 
    get_stock_price, 
    search_financial_news
]