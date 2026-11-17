
from datetime import datetime

from langchain.tools import tool


@tool
def get_current_date() -> str:
    """
    Get the current date and time.

    Use this tool when the user asks about:
    - Today's date
    - Current time
    - Date-related information
    """
    return datetime.now().astimezone().isoformat()
