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
from app.services.nestjs_publishing_service import (
    NestJSPublishingService,
)
from uuid import uuid4

logger = logging.getLogger(__name__)


class GenerationAgent:

    def __init__(
        self,
        llm=None,
        publishing_service: NestJSPublishingService | None = None,
    ):
        self.llm = llm or ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            use_responses_api=True,
        )

        self.intent_llm = self.llm.with_structured_output(GenerationIntent)

        self.publishing_service = publishing_service or NestJSPublishingService()

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

        # Step 3: Generate a unique publishing operation ID.
        publish_id = str(uuid4())

        # Step 4: Publish automatically through NestJS.
        publishing_result = await self.publishing_service.publish_generated_work_items(
            proposal=proposal_data,
            publish_id=publish_id,
        )

        # Step 5: Extract actual publishing results.
        publishing_status = publishing_result.get("status")
        summary = publishing_result.get("summary") or {}

        created_count = summary.get("created", 0)
        reused_count = summary.get("reused", 0)
        failed_count = summary.get("failed", 0)

        # Step 6: Determine the final outcome.
        if (
            publishing_status == "completed"
            and publishing_result.get("success") is True
        ):
            status = "completed"

            agent_response = (
                f"Successfully published {created_count} new "
                f"work item(s) to Azure DevOps. "
                f"{reused_count} existing item(s) were reused."
            )

        elif publishing_status == "partial":
            status = "partial"

            agent_response = (
                f"Publishing partially completed. "
                f"{created_count} item(s) created, "
                f"{reused_count} reused, and "
                f"{failed_count} failed."
            )

        else:
            status = "failed"

            agent_response = (
                "Work-item generation completed, but publishing "
                "to Azure DevOps was unsuccessful. "
                f"{publishing_result.get('message', 'Unknown error')}"
            )

        logger.info(
            "Publishing result: ID=%s, Status=%s, Created=%s, Reused=%s, Failed=%s",
            publish_id,
            status,
            created_count,
            reused_count,
            failed_count,
        )

        return {
            "intent": "generation",
            "work_item_intent": intent.requested_type,
            "proposal": proposal_data,
            "publish_id": publish_id,
            "publishing_result": publishing_result,
            "status": status,
            "error": (
                None if status == "completed" else publishing_result.get("message")
            ),
            "agent_response": agent_response,
        }

    async def __call__(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:

        return await self.execute(
            question=state.get("question", ""),
            messages=state.get("messages", []),
        )
