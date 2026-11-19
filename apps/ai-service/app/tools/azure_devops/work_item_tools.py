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
    """Retrieve Azure DevOps work items using optional filters."""
    return await nestjs_client.get_work_items(
        type=type,
        state=state,
        assigned_to=assigned_to,
        priority=priority,
        is_assigned=is_assigned,
    )


@tool
async def get_work_item_by_id(work_item_id: int) -> dict:
    """Retrieve one Azure DevOps work item by ID."""
    if work_item_id <= 0:
        raise ValueError("Work item ID must be positive.")

    return await nestjs_client.get_work_item_by_id(work_item_id)


@tool
async def assign_work_item(
    work_item_id: int,
    assigned_to: str,
) -> dict:
    """Assign a work item to a verified Azure DevOps user email."""
    if work_item_id <= 0:
        raise ValueError("Work item ID must be positive.")

    if not assigned_to or "@" not in assigned_to:
        raise ValueError("A valid assignee email is required.")

    return await nestjs_client.assign_work_item(
        work_item_id=work_item_id,
        assigned_to=assigned_to,
    )


@tool
async def update_work_item(
    work_item_id: int,
    updates: dict,
) -> dict:
    """Update supported Azure DevOps work item fields."""
    if work_item_id <= 0:
        raise ValueError("Work item ID must be positive.")

    allowed_fields = {
        "title",
        "description",
        "acceptanceCriteria",
        "state",
        "priority",
        "assignedTo",
    }

    if not updates or not set(updates).issubset(allowed_fields):
        raise ValueError("Invalid or empty work-item updates.")

    return await nestjs_client.update_work_item(
        work_item_id=work_item_id,
        updates=updates,
    )
