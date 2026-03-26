"""Tests for config module."""

from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from react_agent.config import LLMConfig, CONFIG_PATH


class TestLLMConfigDefaults:
    def test_default_values(self):
        cfg = LLMConfig()
        assert cfg.model == ""
        assert cfg.base_url == "http://localhost:1234/v1"
        assert cfg.temperature == 0.0
        assert cfg.api_key == "lm-studio"

    def test_custom_values(self):
        cfg = LLMConfig(model="gpt-4", base_url="http://x", temperature=0.5, api_key="k")
        assert cfg.model == "gpt-4"
        assert cfg.base_url == "http://x"
        assert cfg.temperature == 0.5
        assert cfg.api_key == "k"


class TestGetApiKey:
    def test_returns_api_key(self):
        cfg = LLMConfig(api_key="secret")
        assert cfg.get_api_key() == "secret"

    def test_returns_default_api_key(self):
        cfg = LLMConfig()
        assert cfg.get_api_key() == "lm-studio"


class TestFromYaml:
    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            LLMConfig.from_yaml(tmp_path / "nonexistent.yaml")

    def test_loads_full_config(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(
            "llm:\n"
            "  model: my-model\n"
            "  base_url: http://my-url\n"
            "  api_key: my-key\n"
            "  temperature: 0.7\n"
        )
        cfg = LLMConfig.from_yaml(cfg_file)
        assert cfg.model == "my-model"
        assert cfg.base_url == "http://my-url"
        assert cfg.api_key == "my-key"
        assert cfg.temperature == 0.7

    def test_loads_partial_config_uses_defaults(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("llm:\n  model: partial\n")
        cfg = LLMConfig.from_yaml(cfg_file)
        assert cfg.model == "partial"
        assert cfg.base_url == "http://localhost:1234/v1"
        assert cfg.api_key == "lm-studio"
        assert cfg.temperature == 0.0

    def test_loads_empty_yaml_raises(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("")
        with pytest.raises(AttributeError):
            LLMConfig.from_yaml(cfg_file)

    def test_no_llm_key(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("other_key: value\n")
        cfg = LLMConfig.from_yaml(cfg_file)
        assert cfg.model == ""


class TestCreateLlm:
    @patch("react_agent.config.ChatOpenAI")
    def test_create_llm_passes_params(self, mock_chat):
        cfg = LLMConfig(model="m", base_url="http://b", api_key="k", temperature=0.5)
        cfg.create_llm()
        mock_chat.assert_called_once_with(
            model="m",
            base_url="http://b",
            api_key=cfg.get_api_key,
            temperature=0.5,
        )


class TestConfigPath:
    def test_config_path_is_next_to_config_module(self):
        assert CONFIG_PATH.name == "config.yaml"
        assert CONFIG_PATH.parent == Path(__file__).parent.parent / "src" / "react_agent"
