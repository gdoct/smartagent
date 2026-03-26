"""Math calculator tool."""

import math

from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A Python math expression (e.g. '2 + 2', 'math.sqrt(16)').
    """
    try:
        allowed = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
        }
        result = eval(expression, allowed)
        return str(result)
    except Exception as e:
        return f"Error: {e}"
