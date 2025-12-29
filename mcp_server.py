"""
FastMCP Server for Financial Analysis Tools
Compatible with AWS Strands Agents via MCP protocol
"""
from fastmcp import FastMCP
from datetime import datetime

# Initialize FastMCP server
mcp = FastMCP("Financial Analysis MCP Server")

@mcp.tool()
def calculate_ratio(metric_name: str, numerator: float, denominator: float) -> dict:
    """
    Calculate financial ratios with interpretation.
    Compatible with Strands Agents MCP integration.
    
    Args:
        metric_name: Name of the ratio
        numerator: Numerator value
        denominator: Denominator value
    
    Returns:
        Dictionary with calculation results
    """
    if denominator == 0:
        return {
            "error": "Division by zero",
            "metric": metric_name,
            "result": None
        }
    
    ratio = numerator / denominator
    
    # Interpretation logic
    interpretation = ""
    if "current" in metric_name.lower() and "ratio" in metric_name.lower():
        interpretation = "Healthy" if ratio >= 1.5 else "Adequate" if ratio >= 1.0 else "Concerning"
    elif "debt" in metric_name.lower() and "equity" in metric_name.lower():
        interpretation = "Conservative" if ratio < 0.5 else "Moderate" if ratio < 1.0 else "Aggressive"
    elif "profit" in metric_name.lower() and "margin" in metric_name.lower():
        interpretation = "Strong" if ratio > 0.15 else "Average" if ratio > 0.05 else "Weak"
    
    return {
        "metric": metric_name,
        "numerator": numerator,
        "denominator": denominator,
        "result": round(ratio, 4),
        "interpretation": interpretation,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
def compare_periods(metric_name: str, current_value: float, previous_value: float) -> dict:
    """
    Compare financial metrics across time periods.
    
    Args:
        metric_name: Name of the metric
        current_value: Current period value
        previous_value: Previous period value
    
    Returns:
        Comparison analysis with growth rate
    """
    if previous_value == 0:
        return {
            "error": "Cannot calculate growth from zero base",
            "metric": metric_name
        }
    
    change = current_value - previous_value
    growth_rate = (change / previous_value) * 100
    trend = "increasing" if change > 0 else "decreasing" if change < 0 else "stable"
    
    return {
        "metric": metric_name,
        "current_value": current_value,
        "previous_value": previous_value,
        "absolute_change": round(change, 2),
        "growth_rate_percent": round(growth_rate, 2),
        "trend": trend,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
def extract_metrics(text: str) -> dict:
    """
    Extract financial keywords from text.
    
    Args:
        text: Financial text to analyze
    
    Returns:
        Dictionary of found metrics
    """
    keywords = [
        "revenue", "profit", "loss", "assets", "liabilities",
        "equity", "cash flow", "debt", "ebitda", "earnings"
    ]
    
    text_lower = text.lower()
    found = [kw for kw in keywords if kw in text_lower]
    
    import re
    numbers = re.findall(r'\$?[\d,]+\.?\d*', text)
    
    return {
        "found_keywords": found,
        "keyword_count": len(found),
        "numbers_found": numbers[:10],
        "text_length": len(text),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Run the MCP server
    import sys
    print("🚀 Starting FastMCP Financial Analysis Server", file=sys.stderr)
    print("📊 Available tools: calculate_ratio, compare_periods, extract_metrics", file=sys.stderr)
    print("✅ Server ready for MCP connections", file=sys.stderr)
    mcp.run(transport="stdio")