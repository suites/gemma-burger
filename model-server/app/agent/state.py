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
    CANCEL = "CANCEL"
    REMOVE = "REMOVE"


def reduce_cart(left: List[dict], right: List[dict] | None) -> List[dict]:
    if right is None:
        return left
    if any(item.get("command") == "RESET" for item in right):
        return []

    new_cart_map = {item["name"]: dict(item) for item in left}

    for update in right:
        name = update.get("name")
        if not name:
            continue

        qty = update.get("quantity", 0)
        price = update.get("price", 0.0)

        if name in new_cart_map:
            new_cart_map[name]["quantity"] += qty
            if new_cart_map[name]["quantity"] <= 0:
                del new_cart_map[name]
        elif qty > 0:
            new_cart_map[name] = {"name": name, "price": price, "quantity": qty}

    return list(new_cart_map.values())


class AgentState(TypedDict):
    messages: Annotated[List[dict], operator.add]
    cart: Annotated[List[dict], reduce_cart]
    current_intent: str
    final_response: str
    temperature: float | None
