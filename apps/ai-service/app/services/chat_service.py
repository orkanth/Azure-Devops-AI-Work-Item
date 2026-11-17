import logging
from typing import Any
from uuid import uuid4

from app.agents.supervisor.agent import SupervisorAgent
from app.agents.work_items.agent import WorkItemsAgent
from app.agents.users.agent import UsersAgent
from app.agents.rag.agent import RAGAgent
from app.graph.workflow import build_workflow

logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates DevFlow AI conversations through LangGraph."""

    def __init__(self):
        logger.info("Initializing DevFlow AI chat workflow.")

        self.supervisor_agent = SupervisorAgent()
        self.work_items_agent = WorkItemsAgent()
        self.users_agent = UsersAgent()
        self.rag_agent = RAGAgent()

        # GenerationAgent will be added when implemented.
        self.generation_agent = None

        self.workflow = build_workflow(
            supervisor_agent=self.supervisor_agent,
            work_items_agent=self.work_items_agent,
            users_agent=self.users_agent,
            rag_agent=self.rag_agent,
            generation_agent=self.generation_agent,
        )

        logger.info("DevFlow AI chat workflow initialized.")

    async def chat(
        self,
        question: str,
        conversation_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute a user request using the LangGraph workflow."""

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty.")

        if conversation_id is not None:
            if not isinstance(conversation_id, str) or not conversation_id.strip():
                raise ValueError("Conversation ID cannot be empty.")

        if project_id is not None:
            if not isinstance(project_id, str) or not project_id.strip():
                raise ValueError("Project ID cannot be empty.")

        # Generate a new conversation ID when one isn't supplied.
        conversation_id = conversation_id.strip() if conversation_id else str(uuid4())

        input_state = {
            "question": question.strip(),
            "conversation_id": conversation_id,
        }

        if project_id:
            input_state["project_id"] = project_id.strip()

        config = {
            "configurable": {
                "thread_id": conversation_id,
            }
        }

        try:
            result = await self.workflow.ainvoke(
                input_state,
                config=config,
            )

            return {
                "conversation_id": conversation_id,
                "status": result.get("status", "success"),
                "agent_response": result.get("agent_response", ""),
                "intent": result.get("intent"),
                "filters": result.get("filters", {}),
                "tool_results": result.get("tool_results", []),
                "sources": result.get("sources", []),
                "clarification_options": result.get("clarification_options", []),
                "error": result.get("error"),
            }

        except Exception:
            logger.exception(
                "Chat workflow execution failed. Conversation ID: %s",
                conversation_id,
            )
            raise
