import operator
from enum import Enum
from typing import Annotated, List, TypedDict


class Intent(str, Enum):
    ORDER = "ORDER"
    HISTORY = "HISTORY"
    COMPLAINT = "COMPLAINT"
    GREETING = "GREETING"
    MENU_QA = "MENU_QA"
    STORE_INFO = "STORE_INFO"


class AgentState(TypedDict):
    messages: Annotated[List[dict], operator.add]
    cart: Annotated[List[dict], operator.add]
    current_intent: str
    final_response: str
    temperature: float | None
