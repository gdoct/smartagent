"""DuckDuckGo web search tool."""

from langchain_core.tools import tool


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
