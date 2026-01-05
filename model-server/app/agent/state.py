import operator
from typing import Annotated, List, TypedDict


class AgentState(TypedDict):
    messages: Annotated[List[dict], operator.add]
    current_intent: str
    final_response: str
    temperature: float
