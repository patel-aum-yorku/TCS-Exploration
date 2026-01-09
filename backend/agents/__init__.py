"""MCP Server package for financial calculations"""
from mcp_server.server import mcp
from mcp_server.calculators import FinancialCalculator

__all__ = ['mcp', 'FinancialCalculator']