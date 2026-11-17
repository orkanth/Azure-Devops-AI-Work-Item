
from langchain.tools import tool

from app.services.nestjs_client import nestjs_client


@tool
async def get_work_items(
    type: str | None = None,
    state: str | None = None,
    assigned_to: str | None = None,
    priority: int | None = None,
    is_assigned: bool | None = None,
) -> list[dict]:
    """
    Retrieve Azure DevOps work items.

    Optional filters:
    - type: Epic, Feature, User Story, Task or Bug.
    - state: Work item state.
    - assigned_to: Assignee email address.
    - priority: Priority (1, 2, 3 or 4).
    - is_assigned: True for assigned items,
      False for unassigned items.

    Use this tool when users ask about Azure DevOps
    work items or request filtered work-item results.
    """
    return await nestjs_client.get_work_items(
        type=type,
        state=state,
        assigned_to=assigned_to,
        priority=priority,
        is_assigned=is_assigned,
    )
