
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.work_items import EpicProposal



SYSTEM_PROMPT = """
    You are an experienced business analyst, software architect,
    and technical delivery planner.

    Convert the user's business requirement into a structured,
    platform-independent software delivery work-item hierarchy.

    HIERARCHY:
    1. Create one clear Epic representing the overall business objective.
    2. Group related capabilities into Features.
    3. Put User Stories under their relevant Features.
    4. Define meaningful acceptance criteria for every User Story.
    5. Put implementation Tasks under their relevant User Stories.

    GENERATION RULES:
    1. Use clear, actionable titles and descriptions.
    2. User Stories should describe functionality from the perspective of an end user or business stakeholder.
    3. Acceptance criteria must be specific, testable and measurable.
    4. Tasks must be technically useful and actionable.
    5. Group related implementation activities logically.
    6. Avoid unnecessary duplication across Features and Stories.
    7. Do not invent business requirements unsupported by the user's request.
    8. If technical details are missing, make reasonable assumptions only when necessary and identify them clearly.
    9. Keep the hierarchy suitable for publishing to different project management platforms.
    10. Return a complete structured proposal, not a summary.

    IMPORTANT:
    Do not include platform-specific identifiers or fields.
    Do not assume Azure DevOps or Jira.
    Return the proposal using the requested structured schema.
    Return the proposal in a valid JSON format that matches the Epic Proposal schema, including all nested Features, User Stories, and Tasks.
"""



async def generate_work_item_proposal(
    requirement: str,
) -> EpicProposal:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    if not settings.openai_model:
        raise ValueError("OPENAI_MODEL is not configured.")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": requirement,
                },
            ],
            response_format=EpicProposal,
        )

        result = response.choices[0].message.parsed

        if result is None:
            raise ValueError(
                "The AI did not return a valid work-item proposal."
            )

        return result

    finally:
        await client.close()
