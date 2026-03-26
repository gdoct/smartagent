"""Current date tool."""

from langchain_core.tools import tool


@tool
def current_date() -> str:
    """Return the current date in YYYY-MM-DD format."""
    from datetime import date

    return date.today().isoformat()
