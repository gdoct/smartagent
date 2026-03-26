"""ReAct agent built with LangGraph."""

from langchain.agents import create_agent as create_langchain_agent

from react_agent.config import LLMConfig
from react_agent.tools import ALL_TOOLS

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "Use them to answer questions and accomplish tasks. "
    "Think step by step and use tools when needed."
)


def create_agent(config: LLMConfig | None = None):
    if config is None:
        config = LLMConfig()
    llm = config.create_llm()
    return create_langchain_agent(llm, ALL_TOOLS, system_prompt=SYSTEM_PROMPT)
