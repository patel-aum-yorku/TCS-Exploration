"""
Financial calculation tools for MCP server.
Implements liquidity and leverage ratio calculations.
"""
from typing import Dict, Optional
import re

class FinancialCalculator:
    """Handles financial ratio calculations"""
    
    @staticmethod
    def extract_financial_values(rag_data: str) -> Dict[str, Optional[float]]:
        """
        Extract financial values from RAG data using pattern matching.
        Looks for balance sheet items in various formats.
        """
        values = {
            "current_assets": None,
            "current_liabilities": None,
            "inventory": None,
            "total_debt": None,
            "total_assets": None,
            "shareholders_equity": None
        }
        
        # Common patterns for financial data
        patterns = {
            "current_assets": [
                r"current\s+assets[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?",
                r"total\s+current\s+assets[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?"
            ],
            "current_liabilities": [
                r"current\s+liabilities[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?",
                r"total\s+current\s+liabilities[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?"
            ],
            "inventory": [
                r"inventory[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?",
                r"inventories[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?"
            ],
            "total_debt": [
                r"total\s+debt[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?",
                r"long[- ]term\s+debt[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?",
                r"debt[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?"
            ],
            "total_assets": [
                r"total\s+assets[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?"
            ],
            "shareholders_equity": [
                r"shareholders['\s]+equity[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?",
                r"stockholders['\s]+equity[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?",
                r"total\s+equity[:\s]+\$?([\d,]+\.?\d*)\s*(million|billion)?"
            ]
        }
        
        text = rag_data.lower()
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        value_str = match.group(1).replace(",", "")
                        value = float(value_str)
                        
                        # Handle million/billion multipliers
                        if len(match.groups()) > 1 and match.group(2):
                            unit = match.group(2).lower()
                            if "billion" in unit:
                                value *= 1000
                            # Already in millions
                        
                        values[key] = value
                        break
                    except (ValueError, IndexError):
                        continue
                
                if values[key] is not None:
                    break
        
        return values
    
    @staticmethod
    def calculate_current_ratio(current_assets: float, current_liabilities: float) -> Dict:
        """
        Current Ratio = Current Assets / Current Liabilities
        Measures ability to pay short-term obligations.
        """
        if current_liabilities == 0:
            return {"error": "Current liabilities cannot be zero"}
        
        ratio = current_assets / current_liabilities
        
        interpretation = ""
        if ratio >= 2.0:
            interpretation = "Strong liquidity position - company can easily cover short-term obligations"
        elif ratio >= 1.5:
            interpretation = "Healthy liquidity - adequate cushion for short-term liabilities"
        elif ratio >= 1.0:
            interpretation = "Acceptable liquidity - company can meet current obligations"
        else:
            interpretation = "Liquidity concern - may struggle with short-term obligations"
        
        return {
            "ratio_name": "Current Ratio",
            "value": round(ratio, 2),
            "formula": "Current Assets / Current Liabilities",
            "current_assets": current_assets,
            "current_liabilities": current_liabilities,
            "interpretation": interpretation
        }
    
    @staticmethod
    def calculate_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> Dict:
        """
        Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        More conservative liquidity measure.
        """
        if current_liabilities == 0:
            return {"error": "Current liabilities cannot be zero"}
        
        ratio = (current_assets - inventory) / current_liabilities
        
        interpretation = ""
        if ratio >= 1.5:
            interpretation = "Excellent liquidity - strong ability to pay immediate obligations"
        elif ratio >= 1.0:
            interpretation = "Good liquidity - can cover short-term liabilities without selling inventory"
        elif ratio >= 0.75:
            interpretation = "Acceptable liquidity - reasonable short-term financial health"
        else:
            interpretation = "Liquidity risk - may need to sell inventory to meet obligations"
        
        return {
            "ratio_name": "Quick Ratio (Acid-Test)",
            "value": round(ratio, 2),
            "formula": "(Current Assets - Inventory) / Current Liabilities",
            "current_assets": current_assets,
            "inventory": inventory,
            "current_liabilities": current_liabilities,
            "interpretation": interpretation
        }
    
    @staticmethod
    def calculate_debt_to_equity(total_debt: float, shareholders_equity: float) -> Dict:
        """
        Debt-to-Equity Ratio = Total Debt / Shareholders' Equity
        Measures financial leverage.
        """
        if shareholders_equity == 0:
            return {"error": "Shareholders' equity cannot be zero"}
        
        ratio = total_debt / shareholders_equity
        
        interpretation = ""
        if ratio <= 0.5:
            interpretation = "Conservative capital structure - low financial risk"
        elif ratio <= 1.0:
            interpretation = "Balanced capital structure - moderate use of debt"
        elif ratio <= 2.0:
            interpretation = "Leveraged position - higher financial risk but potentially higher returns"
        else:
            interpretation = "Highly leveraged - significant financial risk exposure"
        
        return {
            "ratio_name": "Debt-to-Equity Ratio",
            "value": round(ratio, 2),
            "formula": "Total Debt / Shareholders' Equity",
            "total_debt": total_debt,
            "shareholders_equity": shareholders_equity,
            "interpretation": interpretation
        }
    
    @staticmethod
    def calculate_debt_ratio(total_debt: float, total_assets: float) -> Dict:
        """
        Debt Ratio = Total Debt / Total Assets
        Shows proportion of assets financed by debt.
        """
        if total_assets == 0:
            return {"error": "Total assets cannot be zero"}
        
        ratio = total_debt / total_assets
        
        interpretation = ""
        if ratio <= 0.3:
            interpretation = "Low debt burden - strong asset base with minimal debt"
        elif ratio <= 0.5:
            interpretation = "Moderate debt level - balanced financing structure"
        elif ratio <= 0.7:
            interpretation = "High debt level - substantial portion of assets financed by debt"
        else:
            interpretation = "Very high debt burden - significant financial risk"
        
        return {
            "ratio_name": "Debt Ratio",
            "value": round(ratio, 2),
            "formula": "Total Debt / Total Assets",
            "total_debt": total_debt,
            "total_assets": total_assets,
            "interpretation": interpretation
        }