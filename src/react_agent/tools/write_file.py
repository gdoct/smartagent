"""File writing tool."""

from langchain_core.tools import tool


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
