"""LLM configuration for the react agent."""

from dataclasses import dataclass
from pathlib import Path

import yaml
from langchain_openai import ChatOpenAI

CONFIG_PATH = Path(__file__).parent / "config.yaml"


@dataclass
class LLMConfig:
    """Configuration for the LLM provider."""

    model: str = ""
    base_url: str = "http://localhost:1234/v1"
    temperature: float = 0.0
    api_key: str = "lm-studio"

    def get_api_key(self) -> str:
        return self.api_key

    @classmethod
    def from_yaml(cls, path: Path = CONFIG_PATH) -> "LLMConfig":
        """Load configuration from a YAML file."""
        if not path.exists():
            raise FileNotFoundError(
                f"Config file not found: {path}\n"
                "Copy config.example.yaml to config.yaml and fill in your values."
            )
        with open(path) as f:
            data = yaml.safe_load(f)
        llm = data.get("llm", {})
        return cls(
            model=llm.get("model", cls.model),
            base_url=llm.get("base_url", cls.base_url),
            api_key=llm.get("api_key", cls.api_key),
            temperature=llm.get("temperature", cls.temperature),
        )

    def create_llm(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=self.model,
            base_url=self.base_url,
            api_key=self.get_api_key,
            temperature=self.temperature,
            model_kwargs={
                "extra_body": {
                    "enable_thinking": True,
                    "truncate_thinking_history": False,
                }
            },
        )
