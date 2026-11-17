
from langchain.tools import tool


@tool
def add_numbers(a: float, b: float) -> float:
    """
    Add two numbers and return their sum.

    Use this tool when the user asks
    to calculate the sum of two numbers.
    """
    return a + b
