from typing import Any

from langgraph.graph import END

AGENT_ROUTES = {
    "work_items": "work_items",
    "users": "users",
    "rag": "rag",
    "generation": "generation",
}


def route_after_supervisor(state: dict[str, Any]) -> str:
    """
    Select the next node based on the Supervisor decision.

    Specialist requests go to their respective agents.
    Clarifications, errors, and invalid routes go to response.
    """

    status = state.get("status")

    if status in ("error", "needs_clarification"):
        return "response"

    next_agent = state.get("next_agent")

    if not isinstance(next_agent, str):
        return "response"

    destination = AGENT_ROUTES.get(next_agent.strip().lower())

    if destination is None:
        return "response"

    return destination


def route_after_agent(state: dict[str, Any]) -> str:
    """End the workflow after a specialist agent responds."""

    return END
