
from datetime import datetime

from app.tools.common.date_tools import get_current_date
from app.tools.common.calculator_tools import add_numbers


def test_get_current_date():
    result = get_current_date.invoke({})

    parsed_date = datetime.fromisoformat(result)

    assert isinstance(parsed_date, datetime)


def test_add_numbers():
    result = add_numbers.invoke({
        "a": 10,
        "b": 20
    })

    assert result == 30


def test_add_numbers_with_decimals():
    result = add_numbers.invoke({
        "a": 10.5,
        "b": 20.5
    })

    assert result == 31
