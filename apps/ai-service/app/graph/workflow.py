from typing import Any

from langgraph.graph import END, StateGraph

from app.graph.state import DevFlowState
from app.graph.nodes import create_graph_nodes
from app.graph.edges import route_after_supervisor
from app.graph.checkpoint import create_checkpointer


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

    # Route the Supervisor's decision.
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "work_items": "work_items",
            "users": "users",
            "rag": "rag",
            "generation": "generation",
            "response": "response",
        },
    )

    # Specialist agents finish the request.
    graph.add_edge("work_items", END)
    graph.add_edge("users", END)
    graph.add_edge("rag", END)
    graph.add_edge("generation", END)

    # Save clarification/error responses before finishing.
    graph.add_edge("response", END)

    return graph.compile(checkpointer=checkpointer or create_checkpointer())
