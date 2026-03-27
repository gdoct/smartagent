"""ReAct agent built with LangGraph."""

from langchain.agents import create_agent as create_langchain_agent

from react_agent.config import LLMConfig
from react_agent.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are a helpful assistant with access to tools.

## Planning
Before using any tools, briefly plan what information you need and which tools will get it most directly. Prefer fetching a specific page over running multiple broad searches.

## Tool use limits
- Use at most 5 tool calls per response. If you have not fully answered the question by then, stop, summarise what you found, and ask the user if they want you to continue.
- Never repeat a search with the same or very similar query. If a search returned poor results, try a more specific query or a different tool — not the same query again.
- If two consecutive tool calls return no useful new information, stop searching and answer from what you have.

## Answering
Once you have enough information (or have hit the limits above), synthesise a clear, direct answer. Do not keep searching for marginal improvements — a good answer now is better than a perfect answer that never arrives."""


def create_agent(config: LLMConfig | None = None):
    if config is None:
        config = LLMConfig()
    llm = config.create_llm()
    return create_langchain_agent(llm, ALL_TOOLS, system_prompt=SYSTEM_PROMPT)
