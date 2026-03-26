"""Current time tool."""

from langchain_core.tools import tool


@tool
def current_time() -> str:
    """Return the current local time in HH:MM:SS format."""
    from datetime import datetime

    return datetime.now().strftime("%H:%M:%S")
