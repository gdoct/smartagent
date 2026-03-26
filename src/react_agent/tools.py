"""Tools for the react agent."""

import math
import subprocess

from langchain_core.tools import tool


@tool
def shell(command: str) -> str:
    """Execute a shell command and return its output.

    Args:
        command: The shell command to execute.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.returncode != 0:
            output += f"\nSTDERR:\n{result.stderr}" if result.stderr else ""
            output += f"\nReturn code: {result.returncode}"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30 seconds"


@tool
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read.
    """
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: file not found: {path}"
    except PermissionError:
        return f"Error: permission denied: {path}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating it if it doesn't exist.

    Args:
        path: Path to the file to write.
        content: Content to write to the file.
    """
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except PermissionError:
        return f"Error: permission denied: {path}"


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


@tool
def python(script: str) -> str:
    """Create and execute a Python script.

    The script is written to a temporary file and executed with the system Python
    interpreter. Both stdout and stderr are captured and returned.

    Args:
        script: The Python source code to execute.
    """
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as f:
        f.write(script)
        script_path = f.name

    try:
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        if result.returncode != 0:
            output += f"\nReturn code: {result.returncode}"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: script timed out after 60 seconds"
    finally:
        os.unlink(script_path)


@tool
def web_fetch(url: str) -> str:
    """Download a web page and return the raw HTML.

    Args:
        url: The URL to fetch.
    """
    import requests

    try:
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; ReactAgent/1.0)"
        })
        resp.raise_for_status()
        return resp.text[:100_000]  # cap at 100k chars
    except requests.RequestException as e:
        return f"Error: {e}"


@tool
def web_text(url: str) -> str:
    """Download a web page and return only the visible text (HTML stripped).

    Args:
        url: The URL to fetch and extract text from.
    """
    import requests
    from bs4 import BeautifulSoup

    try:
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; ReactAgent/1.0)"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove non-visible elements
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        return text[:50_000]  # cap at 50k chars
    except requests.RequestException as e:
        return f"Error: {e}"


@tool
def duckduckgo_search(query: str) -> str:
    """Search the web using DuckDuckGo.

    Args:
        query: The search query.
    """
    from ddgs import DDGS

    try:
        results = DDGS().text(query, max_results=10)
        if not results:
            return "No results found."
        lines = []
        for r in results:
            lines.append(f"**{r['title']}**\n{r['href']}\n{r.get('body', '')}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@tool
def current_date() -> str:
    """Return the current date in YYYY-MM-DD format."""
    from datetime import date
    return date.today().isoformat()


@tool
def current_time() -> str:
    """Return the current local time in HH:MM:SS format."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

ALL_TOOLS = [shell, read_file, write_file, calculator, python, duckduckgo_search, web_fetch, web_text, current_date, current_time]
