"""Web page download tool."""

from langchain_core.tools import tool


@tool
def web_fetch(url: str) -> str:
    """Download a web page and return the raw HTML.

    Args:
        url: The URL to fetch.
    """
    import requests

    try:
        resp = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ReactAgent/1.0)"},
        )
        resp.raise_for_status()
        return resp.text[:100_000]  # cap at 100k chars
    except requests.RequestException as e:
        return f"Error: {e}"
