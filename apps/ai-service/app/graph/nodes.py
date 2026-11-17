from typing import Any, Callable


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

    async def work_items_node(state: dict[str, Any]) -> dict[str, Any]:
        return await work_items_agent(state)

    async def users_node(state: dict[str, Any]) -> dict[str, Any]:
        return await users_agent(state)

    async def rag_node(state: dict[str, Any]) -> dict[str, Any]:
        question = state.get("question")
        project_id = state.get("project_id")

        if not isinstance(question, str) or not question.strip():
            return {
                "status": "error",
                "error": "A question is required for document search.",
                "agent_response": "Please provide a question.",
            }

        if not isinstance(project_id, str) or not project_id.strip():
            return {
                "status": "error",
                "error": "A project_id is required for document search.",
                "agent_response": "Please specify the project.",
            }

        try:
            result = await rag_agent.answer_question(
                question=question,
                project_id=project_id,
            )

            return {
                "agent_response": result["answer"],
                "sources": result.get("sources", []),
                "status": "success",
                "error": None,
            }

        except Exception:
            import logging

            logging.getLogger(__name__).exception("RAG node execution failed.")

            return {
                "status": "error",
                "error": "Document question answering failed.",
                "agent_response": (
                    "I couldn't answer the question using the project documents."
                ),
                "sources": [],
            }

    async def generation_node(state: dict[str, Any]) -> dict[str, Any]:
        if generation_agent is None:
            return {
                "status": "error",
                "error": "Generation Agent is not configured.",
                "agent_response": ("Work-item generation is currently unavailable."),
            }

        return await generation_agent(state)

    return {
        "supervisor": supervisor_node,
        "work_items": work_items_node,
        "users": users_node,
        "rag": rag_node,
        "generation": generation_node,
    }
