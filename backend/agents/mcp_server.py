from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Financial Calculator MCP Server",
    description="HTTP REST API for financial calculations",
    version="1.0.0"
)

# Pydantic models
class GrowthRateRequest(BaseModel):
    current_value: float
    previous_value: float
    periods: int = 1

class ProfitabilityRequest(BaseModel):
    revenue: float = 0
    gross_profit: float = 0
    operating_income: float = 0
    net_income: float = 0
    shareholders_equity: float = 0
    total_assets: float = 0
    cost_of_goods_sold: float = 0

class LiquidityRequest(BaseModel):
    current_assets: float = 0
    current_liabilities: float = 0
    cash_and_equivalents: float = 0
    inventory: float = 0

class LeverageRequest(BaseModel):
    total_debt: float = 0
    total_liabilities: float = 0
    shareholders_equity: float = 0
    total_assets: float = 0
    ebit: float = 0
    interest_expense: float = 0

# Calculation functions
def calculate_growth_rate(current_value: float, previous_value: float, periods: int = 1) -> Dict:
    if previous_value == 0:
        return {"error": "Cannot calculate growth rate: previous value is zero"}
    
    growth = ((current_value - previous_value) / previous_value) * 100
    result = {
        "current_value": current_value,
        "previous_value": previous_value,
        "absolute_change": current_value - previous_value,
        "growth_rate_pct": round(growth, 2),
        "periods": periods
    }
    
    if periods > 1 and current_value > 0:
        cagr = (((current_value / previous_value) ** (1/periods)) - 1) * 100
        result["cagr_pct"] = round(cagr, 2)
    
    return result

def calculate_profitability_ratios(revenue=0, gross_profit=0, operating_income=0, 
                                   net_income=0, shareholders_equity=0, total_assets=0, 
                                   cost_of_goods_sold=0) -> Dict:
    results = {}
    try:
        if revenue > 0:
            if gross_profit > 0:
                results["gross_profit_margin_pct"] = round((gross_profit / revenue) * 100, 2)
            elif cost_of_goods_sold > 0:
                results["gross_profit_margin_pct"] = round(((revenue - cost_of_goods_sold) / revenue) * 100, 2)
        
        if revenue > 0 and operating_income > 0:
            results["operating_margin_pct"] = round((operating_income / revenue) * 100, 2)
        
        if revenue > 0 and net_income > 0:
            results["net_profit_margin_pct"] = round((net_income / revenue) * 100, 2)
        
        if shareholders_equity > 0 and net_income > 0:
            results["return_on_equity_pct"] = round((net_income / shareholders_equity) * 100, 2)
        
        if total_assets > 0 and net_income > 0:
            results["return_on_assets_pct"] = round((net_income / total_assets) * 100, 2)
    except Exception as e:
        results["error"] = f"Calculation error: {str(e)}"
    return results

def calculate_liquidity_ratios(current_assets=0, current_liabilities=0, 
                               cash_and_equivalents=0, inventory=0) -> Dict:
    results = {}
    try:
        if current_liabilities > 0:
            results["current_ratio"] = round(current_assets / current_liabilities, 2)
            quick_assets = current_assets - inventory
            results["quick_ratio"] = round(quick_assets / current_liabilities, 2)
            if cash_and_equivalents > 0:
                results["cash_ratio"] = round(cash_and_equivalents / current_liabilities, 2)
    except Exception as e:
        results["error"] = f"Calculation error: {str(e)}"
    return results

def calculate_leverage_ratios(total_debt=0, total_liabilities=0, shareholders_equity=0,
                              total_assets=0, ebit=0, interest_expense=0) -> Dict:
    results = {}
    try:
        if shareholders_equity > 0:
            if total_debt > 0:
                results["debt_to_equity"] = round(total_debt / shareholders_equity, 2)
            elif total_liabilities > 0:
                results["debt_to_equity"] = round(total_liabilities / shareholders_equity, 2)
        
        if total_assets > 0:
            if total_debt > 0:
                results["debt_ratio"] = round(total_debt / total_assets, 2)
            elif total_liabilities > 0:
                results["debt_ratio"] = round(total_liabilities / total_assets, 2)
        
        if interest_expense > 0 and ebit > 0:
            results["interest_coverage"] = round(ebit / interest_expense, 2)
    except Exception as e:
        results["error"] = f"Calculation error: {str(e)}"
    return results

# REST API Endpoints
@app.get("/")
async def root():
    return {
        "name": "Financial Calculator MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/calculate_growth_rate", "/calculate_profitability_ratios", 
                     "/calculate_liquidity_ratios", "/calculate_leverage_ratios", "/health"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "MCP Server is running"}

@app.post("/calculate_growth_rate")
async def api_calculate_growth_rate(request: GrowthRateRequest):
    try:
        return calculate_growth_rate(request.current_value, request.previous_value, request.periods)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calculate_profitability_ratios")
async def api_calculate_profitability_ratios(request: ProfitabilityRequest):
    try:
        return calculate_profitability_ratios(request.revenue, request.gross_profit, 
                                             request.operating_income, request.net_income,
                                             request.shareholders_equity, request.total_assets,
                                             request.cost_of_goods_sold)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calculate_liquidity_ratios")
async def api_calculate_liquidity_ratios(request: LiquidityRequest):
    try:
        return calculate_liquidity_ratios(request.current_assets, request.current_liabilities,
                                         request.cash_and_equivalents, request.inventory)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calculate_leverage_ratios")
async def api_calculate_leverage_ratios(request: LeverageRequest):
    try:
        return calculate_leverage_ratios(request.total_debt, request.total_liabilities,
                                        request.shareholders_equity, request.total_assets,
                                        request.ebit, request.interest_expense)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Financial Calculator REST API Server...")
    print("📊 Endpoints: /calculate_growth_rate, /calculate_profitability_ratios, /calculate_liquidity_ratios, /calculate_leverage_ratios")
    print("🌐 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
