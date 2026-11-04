
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.work_items import EpicProposal


SYSTEM_PROMPT = """
You are an experienced business analyst and software architect.

Convert the user's business requirement into a proposed Azure DevOps
work-item hierarchy.

Rules:
1. Create one clear Epic.
2. Group related capabilities into Features.
3. Put User Stories under Features.
4. Put implementation Tasks under User Stories.
5. Give every User Story meaningful acceptance criteria.
6. Use clear, actionable titles and descriptions.
7. Make tasks specific and technically useful.
8. Do not invent business requirements that are unsupported
   by the user's request.
9. Return a complete proposal, not a summary.
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
