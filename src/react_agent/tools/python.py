"""Python script execution tool."""

import subprocess

from langchain_core.tools import tool


@tool
def python(script: str) -> str:
    """Create and execute a Python script.

    The script is written to a temporary file and executed with the system Python
    interpreter. Both stdout and stderr are captured and returned.

    Args:
        script: The Python source code to execute.
    """
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
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
