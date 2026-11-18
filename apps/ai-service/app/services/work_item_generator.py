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
You are DevFlow AI, an experienced business analyst and
software delivery architect.

Generate a structured work-item proposal from the user's
business or technical requirement.

REQUESTED ROOT TYPE:
{work_item_type}

STRICT HIERARCHY RULES:

Follow these parent-child relationships exactly.

1. Epic
   Epic
   ├── Feature
   │   └── User Story
   │       └── Task
   └── Feature
       └── User Story
           └── Task

2. Feature
   Feature
   └── User Story
       └── Task

3. User Story
   User Story
   └── Task

4. Task
   Task only. No children.

5. Bug
   Bug only. No children.

PARENT-CHILD VALIDATION RULES:

- An Epic can contain Features, User Stories, Tasks or Bugs.
- A Feature can contain User Stories, Tasks or Bugs.
- A User Story can contain Tasks or Bugs.
- A Task cannot contain children.
- A Bug cannot contain children.

CRITICAL SIBLING RULES:

- Multiple Features belonging to the same Epic MUST be
  direct children of that Epic.
- Features must be siblings, never children of other Features.
- Multiple User Stories belonging to the same Feature MUST
  be direct children of that Feature.
- User Stories must not be nested under other User Stories.
- Multiple Tasks belonging to the same User Story MUST
  be direct children of that User Story.
- Tasks must not be nested under other Tasks.
- Never create a child whose type is not allowed under
  its immediate parent.
- Never invent additional hierarchy levels.

GENERATION RULES:

1. Generate only the requested root work-item type.
2. Preserve the requested business requirement.
3. Use clear, actionable titles and descriptions.
4. User Stories should describe functionality from the
   perspective of an end user or business stakeholder.
5. Include specific, testable acceptance criteria.
6. Tasks must describe actionable implementation work.
7. Group related activities logically.
8. Avoid unnecessary duplication.
9. Do not invent unsupported business requirements.
10. Do not create unnecessary children.
11. If the requirement explicitly requests multiple Features,
    create them as siblings under the same Epic.
12. If the requirement explicitly requests multiple User Stories,
    create them as siblings under their relevant Feature.
13. If the requirement explicitly requests multiple Tasks,
    create them as siblings under their relevant User Story.
14. Preserve parent_reference when explicitly provided.
15. Never invent parent IDs or parent names.

OUTPUT REQUIREMENTS:

- Return a valid WorkItemGenerationProposal.
- requested_type must match the requested root type.
- Every root item must have the requested type.
- Every child must obey the parent-child validation rules.
- Return the complete hierarchy, not a summary.
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
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": requirement.strip(),
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
