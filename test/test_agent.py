"""Tests for agent module."""

from unittest.mock import patch, MagicMock

from react_agent.agent import create_agent, SYSTEM_PROMPT
from react_agent.config import LLMConfig
from react_agent.tools import ALL_TOOLS


class TestSystemPrompt:
    def test_system_prompt_is_nonempty_string(self):
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 0


class TestCreateAgent:
    @patch("react_agent.agent.create_langchain_agent")
    @patch("react_agent.agent.LLMConfig")
    def test_default_config(self, mock_config_cls, mock_create):
        mock_cfg = MagicMock()
        mock_config_cls.return_value = mock_cfg
        mock_llm = MagicMock()
        mock_cfg.create_llm.return_value = mock_llm

        create_agent()

        mock_config_cls.assert_called_once()
        mock_cfg.create_llm.assert_called_once()
        mock_create.assert_called_once_with(mock_llm, ALL_TOOLS, system_prompt=SYSTEM_PROMPT)

    @patch("react_agent.agent.create_langchain_agent")
    def test_custom_config(self, mock_create):
        cfg = MagicMock(spec=LLMConfig)
        mock_llm = MagicMock()
        cfg.create_llm.return_value = mock_llm

        create_agent(cfg)

        cfg.create_llm.assert_called_once()
        mock_create.assert_called_once_with(mock_llm, ALL_TOOLS, system_prompt=SYSTEM_PROMPT)
