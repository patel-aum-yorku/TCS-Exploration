"""
FastMCP HTTP Server for financial calculations.
Runs as a standalone HTTP service that agents can call.
"""
from fastmcp import FastMCP
from mcp_server.calculators import FinancialCalculator
import json

# Initialize FastMCP server
mcp = FastMCP("Financial Calculator Server")

@mcp.tool()
def calculate_liquidity_ratios(rag_data: str) -> str:
    """
    Calculate liquidity ratios (Current Ratio and Quick Ratio) from financial data.
    
    Args:
        rag_data: Text containing financial statement data from RAG agent
    
    Returns:
        JSON string with calculated ratios and interpretations
    """
    calculator = FinancialCalculator()
    
    # Extract values from RAG data
    values = calculator.extract_financial_values(rag_data)
    
    results = {
        "extracted_values": values,
        "ratios": []
    }
    
    # Calculate Current Ratio
    if values["current_assets"] and values["current_liabilities"]:
        current_ratio = calculator.calculate_current_ratio(
            values["current_assets"],
            values["current_liabilities"]
        )
        results["ratios"].append(current_ratio)
    else:
        results["ratios"].append({
            "ratio_name": "Current Ratio",
            "error": "Missing required data: current_assets or current_liabilities"
        })
    
    # Calculate Quick Ratio
    if values["current_assets"] and values["inventory"] and values["current_liabilities"]:
        quick_ratio = calculator.calculate_quick_ratio(
            values["current_assets"],
            values["inventory"],
            values["current_liabilities"]
        )
        results["ratios"].append(quick_ratio)
    else:
        results["ratios"].append({
            "ratio_name": "Quick Ratio",
            "error": "Missing required data: current_assets, inventory, or current_liabilities"
        })
    
    return json.dumps(results, indent=2)

@mcp.tool()
def calculate_leverage_ratios(rag_data: str) -> str:
    """
    Calculate leverage ratios (Debt-to-Equity and Debt Ratio) from financial data.
    
    Args:
        rag_data: Text containing financial statement data from RAG agent
    
    Returns:
        JSON string with calculated ratios and interpretations
    """
    calculator = FinancialCalculator()
    
    # Extract values from RAG data
    values = calculator.extract_financial_values(rag_data)
    
    results = {
        "extracted_values": values,
        "ratios": []
    }
    
    # Calculate Debt-to-Equity Ratio
    if values["total_debt"] and values["shareholders_equity"]:
        dte_ratio = calculator.calculate_debt_to_equity(
            values["total_debt"],
            values["shareholders_equity"]
        )
        results["ratios"].append(dte_ratio)
    else:
        results["ratios"].append({
            "ratio_name": "Debt-to-Equity Ratio",
            "error": "Missing required data: total_debt or shareholders_equity"
        })
    
    # Calculate Debt Ratio
    if values["total_debt"] and values["total_assets"]:
        debt_ratio = calculator.calculate_debt_ratio(
            values["total_debt"],
            values["total_assets"]
        )
        results["ratios"].append(debt_ratio)
    else:
        results["ratios"].append({
            "ratio_name": "Debt Ratio",
            "error": "Missing required data: total_debt or total_assets"
        })
    
    return json.dumps(results, indent=2)

@mcp.tool()
def calculate_all_ratios(rag_data: str) -> str:
    """
    Calculate all financial ratios (liquidity and leverage) from financial data.
    
    Args:
        rag_data: Text containing financial statement data from RAG agent
    
    Returns:
        JSON string with all calculated ratios and interpretations
    """
    calculator = FinancialCalculator()
    
    # Extract values from RAG data
    values = calculator.extract_financial_values(rag_data)
    
    results = {
        "extracted_values": values,
        "liquidity_ratios": [],
        "leverage_ratios": []
    }
    
    # Liquidity Ratios
    if values["current_assets"] and values["current_liabilities"]:
        current_ratio = calculator.calculate_current_ratio(
            values["current_assets"],
            values["current_liabilities"]
        )
        results["liquidity_ratios"].append(current_ratio)
    
    if values["current_assets"] and values["inventory"] and values["current_liabilities"]:
        quick_ratio = calculator.calculate_quick_ratio(
            values["current_assets"],
            values["inventory"],
            values["current_liabilities"]
        )
        results["liquidity_ratios"].append(quick_ratio)
    
    # Leverage Ratios
    if values["total_debt"] and values["shareholders_equity"]:
        dte_ratio = calculator.calculate_debt_to_equity(
            values["total_debt"],
            values["shareholders_equity"]
        )
        results["leverage_ratios"].append(dte_ratio)
    
    if values["total_debt"] and values["total_assets"]:
        debt_ratio = calculator.calculate_debt_ratio(
            values["total_debt"],
            values["total_assets"]
        )
        results["leverage_ratios"].append(debt_ratio)
    
    return json.dumps(results, indent=2)

if __name__ == "__main__":
    # Run server on HTTP
    mcp.run(transport="http", port=8000)