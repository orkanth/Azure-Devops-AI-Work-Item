import logging
from typing import Any, Callable

from langchain_core.messages import AIMessage, HumanMessage

logger = logging.getLogger(__name__)


def _with_conversation_turn(
    state: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Append the current user question and agent response to history."""

    question = state.get("question", "")
    response = result.get("agent_response", "")

    messages = []

    if isinstance(question, str) and question.strip():
        messages.append(HumanMessage(content=question))

    if isinstance(response, str) and response.strip():
        messages.append(AIMessage(content=response))

    return {
        **result,
        "messages": messages,
    }


def create_graph_nodes(
    supervisor_agent: Any,
    work_items_agent: Any,
    users_agent: Any,
    rag_agent: Any,
    generation_agent: Any | None = None,
) -> dict[str, Callable]:
    """
    Create LangGraph nodes from the existing specialist agents.

    The graph coordinates agents; business logic stays inside
    the individual agents and their services.
    """

    async def supervisor_node(state: dict[str, Any]) -> dict[str, Any]:
        return await supervisor_agent(state)

    async def response_node(state: dict[str, Any]) -> dict[str, Any]:
        """Persist Supervisor clarification and error responses."""

        return _with_conversation_turn(
            state,
            {
                "agent_response": state.get("agent_response", ""),
                "status": state.get("status", "error"),
                "error": state.get("error"),
            },
        )

    async def work_items_node(state: dict[str, Any]) -> dict[str, Any]:
        result = await work_items_agent(state)
        return _with_conversation_turn(state, result)

    async def users_node(state: dict[str, Any]) -> dict[str, Any]:
        result = await users_agent(state)
        return _with_conversation_turn(state, result)

    async def rag_node(state: dict[str, Any]) -> dict[str, Any]:
        question = state.get("question")
        project_id = state.get("project_id")

        if not isinstance(question, str) or not question.strip():
            return _with_conversation_turn(
                state,
                {
                    "status": "error",
                    "error": "A question is required for document search.",
                    "agent_response": "Please provide a question.",
                },
            )

        if not isinstance(project_id, str) or not project_id.strip():
            return _with_conversation_turn(
                state,
                {
                    "status": "error",
                    "error": "A project_id is required for document search.",
                    "agent_response": "Please specify the project.",
                },
            )

        try:
            result = await rag_agent.answer_question(
                question=question,
                project_id=project_id,
            )

            return _with_conversation_turn(
                state,
                {
                    "agent_response": result["answer"],
                    "sources": result.get("sources", []),
                    "status": "success",
                    "error": None,
                },
            )

        except Exception:
            logger.exception("RAG node execution failed.")

            return _with_conversation_turn(
                state,
                {
                    "status": "error",
                    "error": "Document question answering failed.",
                    "agent_response": (
                        "I couldn't answer the question using the project documents."
                    ),
                    "sources": [],
                },
            )

    async def generation_node(state: dict[str, Any]) -> dict[str, Any]:
        if generation_agent is None:
            return _with_conversation_turn(
                state,
                {
                    "status": "error",
                    "error": "Generation Agent is not configured.",
                    "agent_response": "Work-item generation is currently unavailable.",
                },
            )

        result = await generation_agent(state)
        return _with_conversation_turn(state, result)

    return {
        "supervisor": supervisor_node,
        "response": response_node,
        "work_items": work_items_node,
        "users": users_node,
        "rag": rag_node,
        "generation": generation_node,
    }
