
from app.tools.common.date_tools import get_current_date
from app.tools.common.calculator_tools import add_numbers

from app.tools.azure_devops.user_tools import get_users
from app.tools.azure_devops.work_item_tools import get_work_items


def get_all_tools():
    """
    Return all tools available to DevFlow AI.
    """

    return [
        get_current_date,
        add_numbers,
        get_users,
        get_work_items,
    ]
