from typing import Annotated, Literal, Optional, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages

def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push atau pop status dialog."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    dialog_state: Annotated[
        list[
            Literal[
                "supervisor",
                "customer_service",
                "hotel_agent",
                "flight_agent",
                "tour_agent",
            ]
        ],
        update_dialog_stack,
    ]
    user_context: Optional[Dict[str, Any]]