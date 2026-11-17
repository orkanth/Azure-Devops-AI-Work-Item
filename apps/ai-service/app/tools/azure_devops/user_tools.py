
from langchain.tools import tool

from app.services.nestjs_client import nestjs_client


@tool
async def get_users(name: str) -> list[dict]:
    """
    Search Azure DevOps users by display name or email address.

    Use this tool to resolve an assignee before
    retrieving work items assigned to that person.

    Returns matching users with their display names
    and email addresses.
    """
    return await nestjs_client.search_users(name)
