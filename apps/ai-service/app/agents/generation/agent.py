import logging
from typing import Any

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.agents.generation.prompts import GENERATION_INTENT_PROMPT
from app.schemas.work_items import GenerationIntent
from app.services.work_item_generator import (
    generate_work_item_hierarchy,
)

logger = logging.getLogger(__name__)


class GenerationAgent:

    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            use_responses_api=True,
        )

        self.intent_llm = self.llm.with_structured_output(GenerationIntent)

    async def execute(
        self,
        question: str,
        messages: list[AnyMessage] | None = None,
    ) -> dict[str, Any]:

        if not question or not question.strip():
            raise ValueError("A generation request is required.")

        conversation_messages = [SystemMessage(content=GENERATION_INTENT_PROMPT)]

        if messages:
            conversation_messages.extend(messages)

        conversation_messages.append(HumanMessage(content=question.strip()))

        # Step 1: Understand the user's request.
        intent = await self.intent_llm.ainvoke(conversation_messages)

        logger.info(
            "Generation intent identified: %s",
            intent.requested_type,
        )

        # Step 2: Generate the structured proposal.
        proposal = await generate_work_item_hierarchy(
            requirement=intent.requirement,
            work_item_type=intent.requested_type,
        )

        proposal_data = proposal.model_dump(mode="json")

        # Step 3: Prepare the proposal for user review.
        root_count = len(proposal.items)

        return {
            "intent": "generation",
            "work_item_intent": intent.requested_type,
            "proposal": proposal_data,
            "status": "awaiting_confirmation",
            "error": None,
            "agent_response": (
                f"I generated {root_count} "
                f"{intent.requested_type} work item(s). "
                "Please review the proposal before publishing "
                "it to Azure DevOps."
            ),
        }

    async def __call__(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:

        return await self.execute(
            question=state.get("question", ""),
            messages=state.get("messages", []),
        )
