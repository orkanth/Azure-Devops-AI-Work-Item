from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class DevFlowState(TypedDict, total=False):
    # User request
    question: str
    project_id: str
    conversation_id: str

    # Conversation history
    messages: Annotated[list[AnyMessage], add_messages]

    # Supervisor routing
    intent: str
    next_agent: str

    # Work-item request interpretation
    work_item_intent: str
    filters: dict[str, Any]
    assignee_name: str | None
    assignee_email: str | None

    # Agent execution
    tool_results: list[dict[str, Any]]
    agent_response: str

    # RAG
    retrieved_context: str
    sources: list[dict[str, Any]]

    # Workflow status
    status: str
    error: str | None

    clarification_options: list[dict[str, Any]]

    work_item_intent: str
    proposal: dict[str, Any]
