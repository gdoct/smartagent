"""Web page text extraction tool."""

from langchain_core.tools import tool


@tool
def web_text(url: str) -> str:
    """Download a web page and return only the visible text (HTML stripped).

    Args:
        url: The URL to fetch and extract text from.
    """
    import requests
    from bs4 import BeautifulSoup

    try:
        resp = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ReactAgent/1.0)"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove non-visible elements
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        return text[:50_000]  # cap at 50k chars
    except requests.RequestException as e:
        return f"Error: {e}"
