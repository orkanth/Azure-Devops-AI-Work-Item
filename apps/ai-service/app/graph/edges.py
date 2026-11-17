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
    Select the specialist agent based on the Supervisor decision.
    """

    status = state.get("status")

    # Do not route after an error or clarification response.
    if status in ("error", "needs_clarification"):
        return END

    next_agent = state.get("next_agent")

    if not isinstance(next_agent, str):
        return END

    destination = AGENT_ROUTES.get(next_agent.strip().lower())

    if destination is None:
        return END

    return destination


def route_after_agent(state: dict[str, Any]) -> str:
    """
    End the workflow after a specialist agent responds.

    The caller receives the result, including any errors or
    clarification requests.
    """

    return END
