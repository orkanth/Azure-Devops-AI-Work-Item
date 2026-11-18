from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.work_items import EpicProposal
from app.schemas.work_items import (
    WorkItemGenerationProposal,
    WorkItemType,
)

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
            raise ValueError("The AI did not return a valid work-item proposal.")

        return result

    finally:
        await client.close()


WORK_ITEM_GENERATION_PROMPT = """
You are DevFlow AI, an enterprise project management assistant.

Generate a structured work-item proposal based on the user's request.

SUPPORTED WORK ITEM TYPES:

1. Epic
   Epic -> Features -> User Stories -> Tasks

2. Feature
   Feature -> User Stories -> Tasks

3. User Story
   User Story -> Tasks

4. Task
   Task only

5. Bug
   Bug only

RULES:

1. Generate only the requested root work-item type.
2. Follow the hierarchy appropriate for that type.
3. Do not create unnecessary children.
4. Use clear, actionable titles and descriptions.
5. User Stories must contain meaningful acceptance criteria.
6. Tasks must describe actionable implementation work.
7. Bugs must describe the problem and expected behaviour.
8. Do not invent requirements unsupported by the request.
9. If the user specifies a parent by name or ID,
   extract that reference into parent_reference.
10. If no parent is specified, parent_reference must be null.
11. Never invent a parent ID.
12. Return a complete structured proposal.

The output must match the WorkItemGenerationProposal schema.

USER REQUEST:

Requested work-item type: {work_item_type}

Requirement:
{requirement}
"""


async def generate_work_item_hierarchy(
    requirement: str,
    work_item_type: WorkItemType,
) -> WorkItemGenerationProposal:
    if not requirement or not requirement.strip():
        raise ValueError("A work-item requirement is required.")

    if work_item_type not in {
        "Epic",
        "Feature",
        "User Story",
        "Task",
        "Bug",
    }:
        raise ValueError("Unsupported work-item type.")

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    if not settings.openai_model:
        raise ValueError("OPENAI_MODEL is not configured.")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = WORK_ITEM_GENERATION_PROMPT.format(
        work_item_type=work_item_type,
        requirement=requirement.strip(),
    )

    try:
        response = await client.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate accurate, structured work-item proposals. "
                        "Never invent parent identifiers or requirements."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format=WorkItemGenerationProposal,
        )

        result = response.choices[0].message.parsed

        if result is None:
            raise ValueError("AI did not return a valid work-item proposal.")

        if result.requested_type != work_item_type:
            raise ValueError(
                "Generated proposal does not match the requested work-item type."
            )

        if any(item.type != work_item_type for item in result.items):
            raise ValueError(
                "Generated root work-item type does not match the request."
            )

        return result

    finally:
        await client.close()
