from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator

class AgentState(TypedDict):
    """The shared memory of the system."""
    query: str
    messages: List[Dict[str, str]]  # Log of conversation
    
    # -- Agent Outputs --
    rag_data: Optional[str]
    stock_data: Optional[Dict]
    calc_data: Optional[str]  # Added for MCP agent calculations
    
    # -- Routing --
    next_step: str  # 'rag', 'stock', 'calc', 'report'