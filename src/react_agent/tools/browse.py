"""Browse a URL using a real Firefox browser with stealth settings."""

from langchain_core.tools import tool


@tool
def browse(url: str) -> str:
    """Navigate to a URL in a real Firefox browser and return the visible text.

    Use this instead of web_fetch/web_text when a site requires JavaScript
    rendering or blocks simple HTTP requests (bot detection).

    Args:
        url: The URL to navigate to.
    """
    from react_agent.tools._browser_session import browser_session

    try:
        page = browser_session.get_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(2000)

        title = page.title()
        final_url = page.url

        text = page.evaluate("""
            () => {
                for (const el of document.querySelectorAll(
                    'script, style, noscript, svg, [aria-hidden="true"]'
                )) {
                    el.remove();
                }
                return document.body.innerText;
            }
        """)

        text = text.strip()
        if len(text) > 50_000:
            text = text[:50_000] + "\n... (truncated)"

        return f"URL: {final_url}\nTitle: {title}\n\n{text}"
    except Exception as e:
        return f"Error browsing {url}: {e}"
    finally:
        browser_session.release()
