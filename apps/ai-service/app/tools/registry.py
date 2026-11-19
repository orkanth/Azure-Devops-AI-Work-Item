from app.tools.common.date_tools import get_current_date
from app.tools.common.calculator_tools import add_numbers

from app.tools.azure_devops.user_tools import get_users
from app.tools.azure_devops.work_item_tools import (
    assign_work_item,
    get_work_item_by_id,
    get_work_items,
    update_work_item,
)


def get_all_tools():
    """
    Return all tools available to DevFlow AI.
    """

    return [
        get_current_date,
        add_numbers,
        get_users,
        get_work_items,
        get_work_item_by_id,
        assign_work_item,
        update_work_item,
    ]
