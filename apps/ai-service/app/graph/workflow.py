from typing import Any

from langgraph.graph import END, StateGraph

from app.graph.state import DevFlowState
from app.graph.nodes import create_graph_nodes
from app.graph.edges import route_after_supervisor


def build_workflow(
    supervisor_agent: Any,
    work_items_agent: Any,
    users_agent: Any,
    rag_agent: Any,
    generation_agent: Any | None = None,
    checkpointer: Any | None = None,
):
    """
    Build and compile the DevFlow AI LangGraph workflow.

    Args:
        supervisor_agent: Routes the user's request.
        work_items_agent: Handles work-item operations.
        users_agent: Handles independent user operations.
        rag_agent: Answers questions using project documents.
        generation_agent: Generates work-item hierarchies.
        checkpointer: Optional LangGraph checkpoint saver.

    Returns:
        A compiled LangGraph application.
    """

    nodes = create_graph_nodes(
        supervisor_agent=supervisor_agent,
        work_items_agent=work_items_agent,
        users_agent=users_agent,
        rag_agent=rag_agent,
        generation_agent=generation_agent,
    )

    graph = StateGraph(DevFlowState)

    # Register all graph nodes.
    for node_name, node_function in nodes.items():
        graph.add_node(node_name, node_function)

    # Every request starts with the Supervisor.
    graph.set_entry_point("supervisor")

    # Route the Supervisor's decision to the selected specialist.
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "work_items": "work_items",
            "users": "users",
            "rag": "rag",
            "generation": "generation",
            END: END,
        },
    )

    # Specialist agents return their results to the caller.
    graph.add_edge("work_items", END)
    graph.add_edge("users", END)
    graph.add_edge("rag", END)
    graph.add_edge("generation", END)

    return graph.compile(checkpointer=checkpointer)
