"""Tools for the react agent."""

from react_agent.tools.browse import browse
from react_agent.tools.calculator import calculator
from react_agent.tools.current_date import current_date
from react_agent.tools.current_time import current_time
from react_agent.tools.duckduckgo_search import duckduckgo_search
from react_agent.tools.python import python
from react_agent.tools.read_file import read_file
from react_agent.tools.shell import shell
from react_agent.tools.web_fetch import web_fetch
from react_agent.tools.web_text import web_text
from react_agent.tools.write_file import write_file

ALL_TOOLS = [
    shell,
    read_file,
    write_file,
    browse,
    calculator,
    python,
    duckduckgo_search,
    web_fetch,
    web_text,
    current_date,
    current_time,
]

__all__ = [
    "ALL_TOOLS",
    "browse",
    "calculator",
    "current_date",
    "current_time",
    "duckduckgo_search",
    "python",
    "read_file",
    "shell",
    "web_fetch",
    "web_text",
    "write_file",
]
