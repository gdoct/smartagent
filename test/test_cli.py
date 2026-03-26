"""Tests for cli module."""

import json
from unittest.mock import patch, MagicMock, call

import pytest

from react_agent.cli import print_tool_call, print_tool_result, stream_response, parse_args, main


class TestPrintToolCall:
    @patch("react_agent.cli.console")
    def test_prints_panel(self, mock_console):
        print_tool_call("my_tool", {"key": "value"})
        mock_console.print.assert_called_once()
        panel = mock_console.print.call_args[0][0]
        assert "my_tool" in panel.title


class TestPrintToolResult:
    @patch("react_agent.cli.console")
    def test_prints_panel(self, mock_console):
        print_tool_result("my_tool", "result text")
        mock_console.print.assert_called_once()
        panel = mock_console.print.call_args[0][0]
        assert "my_tool" in panel.title

    @patch("react_agent.cli.console")
    def test_truncates_long_content(self, mock_console):
        long_content = "x" * 3000
        print_tool_result("my_tool", long_content)
        mock_console.print.assert_called_once()
        panel = mock_console.print.call_args[0][0]
        # The panel renderable should contain truncated text
        assert "truncated" in panel.renderable


class TestStreamResponse:
    def _make_ai_chunk(self, content="", tool_call_chunks=None):
        msg = MagicMock()
        msg.type = "AIMessageChunk"
        msg.content = content
        msg.tool_call_chunks = tool_call_chunks or []
        return msg

    def _make_tool_msg(self, name="tool", content="result"):
        msg = MagicMock()
        msg.type = "tool"
        msg.name = name
        msg.content = content
        return msg

    @patch("react_agent.cli.console")
    @patch("react_agent.cli.Live")
    def test_streams_text(self, mock_live_cls, mock_console):
        mock_live = MagicMock()
        mock_live_cls.return_value = mock_live
        mock_live.start = MagicMock()
        mock_live.stop = MagicMock()

        agent = MagicMock()
        chunk = self._make_ai_chunk(content="Hello")
        agent.stream.return_value = [(chunk, {})]

        stream_response(agent, "hi")
        mock_live.start.assert_called_once()
        mock_live.update.assert_called_once()
        mock_live.stop.assert_called_once()

    @patch("react_agent.cli.console")
    @patch("react_agent.cli.Live")
    @patch("react_agent.cli.print_tool_result")
    @patch("react_agent.cli.print_tool_call")
    def test_tool_call_and_result(self, mock_ptc, mock_ptr, mock_live_cls, mock_console):
        mock_live = MagicMock()
        mock_live_cls.return_value = mock_live

        agent = MagicMock()

        # AI chunk with tool call
        tc_chunk = {"id": "tc1", "name": "shell", "args": '{"command": "ls"}'}
        ai_msg = self._make_ai_chunk(content="Let me check", tool_call_chunks=[tc_chunk])
        tool_msg = self._make_tool_msg(name="shell", content="file1.txt")

        agent.stream.return_value = [(ai_msg, {}), (tool_msg, {})]
        stream_response(agent, "list files")

        mock_ptc.assert_called_once_with("shell", {"command": "ls"})
        mock_ptr.assert_called_once_with("shell", "file1.txt")

    @patch("react_agent.cli.console")
    @patch("react_agent.cli.Live")
    @patch("react_agent.cli.print_tool_result")
    @patch("react_agent.cli.print_tool_call")
    def test_tool_call_invalid_json(self, mock_ptc, mock_ptr, mock_live_cls, mock_console):
        mock_live = MagicMock()
        mock_live_cls.return_value = mock_live

        agent = MagicMock()

        tc_chunk = {"id": "tc1", "name": "shell", "args": "not json"}
        ai_msg = self._make_ai_chunk(tool_call_chunks=[tc_chunk])
        tool_msg = self._make_tool_msg()

        agent.stream.return_value = [(ai_msg, {}), (tool_msg, {})]
        stream_response(agent, "test")

        # Should fall back to raw args
        mock_ptc.assert_called_once_with("shell", {"raw": "not json"})

    @patch("react_agent.cli.console")
    def test_no_content_no_live(self, mock_console):
        """When there's no content, Live should not be created."""
        agent = MagicMock()
        ai_msg = self._make_ai_chunk(content="")
        agent.stream.return_value = [(ai_msg, {})]
        # Should not crash
        stream_response(agent, "test")

    @patch("react_agent.cli.console")
    @patch("react_agent.cli.Live")
    @patch("react_agent.cli.print_tool_result")
    @patch("react_agent.cli.print_tool_call")
    def test_tool_call_chunk_accumulation(self, mock_ptc, mock_ptr, mock_live_cls, mock_console):
        """Test accumulating args across multiple chunks for the same tool call."""
        mock_live = MagicMock()
        mock_live_cls.return_value = mock_live

        agent = MagicMock()

        chunk1 = self._make_ai_chunk(tool_call_chunks=[
            {"id": "tc1", "name": "shell", "args": '{"comma'}
        ])
        chunk2 = self._make_ai_chunk(tool_call_chunks=[
            {"id": "tc1", "name": "shell", "args": 'nd": "ls"}'}
        ])
        tool_msg = self._make_tool_msg(name="shell", content="output")

        agent.stream.return_value = [(chunk1, {}), (chunk2, {}), (tool_msg, {})]
        stream_response(agent, "test")

        mock_ptc.assert_called_once_with("shell", {"command": "ls"})


class TestParseArgs:
    @patch("sys.argv", ["cli.py"])
    def test_defaults(self):
        args = parse_args()
        assert args.model is None
        assert args.base_url is None
        assert args.api_key is None
        assert args.temperature is None
        assert args.config is None

    @patch("sys.argv", ["cli.py", "--model", "gpt-4", "--base-url", "http://x",
                         "--api-key", "k", "--temperature", "0.5", "--config", "c.yaml"])
    def test_all_args(self):
        args = parse_args()
        assert args.model == "gpt-4"
        assert args.base_url == "http://x"
        assert args.api_key == "k"
        assert args.temperature == 0.5
        assert args.config == "c.yaml"


class TestMain:
    @patch("react_agent.cli.stream_response")
    @patch("react_agent.cli.create_agent")
    @patch("react_agent.cli.console")
    @patch("react_agent.cli.LLMConfig")
    @patch("sys.argv", ["cli.py", "--config", "/dev/null"])
    def test_quit_command(self, mock_config_cls, mock_console, mock_create_agent, mock_stream):
        mock_cfg = MagicMock()
        mock_config_cls.from_yaml.return_value = mock_cfg

        with patch("builtins.input", return_value="quit"):
            main()

        mock_console.print.assert_called()  # prints welcome + goodbye

    @patch("react_agent.cli.stream_response")
    @patch("react_agent.cli.create_agent")
    @patch("react_agent.cli.console")
    @patch("react_agent.cli.LLMConfig")
    @patch("sys.argv", ["cli.py", "--config", "/dev/null"])
    def test_exit_command(self, mock_config_cls, mock_console, mock_create_agent, mock_stream):
        mock_cfg = MagicMock()
        mock_config_cls.from_yaml.return_value = mock_cfg

        with patch("builtins.input", return_value="exit"):
            main()

    @patch("react_agent.cli.stream_response")
    @patch("react_agent.cli.create_agent")
    @patch("react_agent.cli.console")
    @patch("react_agent.cli.LLMConfig")
    @patch("sys.argv", ["cli.py", "--config", "/dev/null"])
    def test_empty_input_skipped(self, mock_config_cls, mock_console, mock_create_agent, mock_stream):
        mock_cfg = MagicMock()
        mock_config_cls.from_yaml.return_value = mock_cfg

        inputs = iter(["", "quit"])
        with patch("builtins.input", side_effect=inputs):
            main()

        mock_stream.assert_not_called()

    @patch("react_agent.cli.stream_response")
    @patch("react_agent.cli.create_agent")
    @patch("react_agent.cli.console")
    @patch("react_agent.cli.LLMConfig")
    @patch("sys.argv", ["cli.py", "--config", "/dev/null"])
    def test_eof_exits(self, mock_config_cls, mock_console, mock_create_agent, mock_stream):
        mock_cfg = MagicMock()
        mock_config_cls.from_yaml.return_value = mock_cfg

        with patch("builtins.input", side_effect=EOFError):
            main()

    @patch("react_agent.cli.stream_response")
    @patch("react_agent.cli.create_agent")
    @patch("react_agent.cli.console")
    @patch("react_agent.cli.LLMConfig")
    @patch("sys.argv", ["cli.py", "--config", "/dev/null"])
    def test_keyboard_interrupt_exits(self, mock_config_cls, mock_console, mock_create_agent, mock_stream):
        mock_cfg = MagicMock()
        mock_config_cls.from_yaml.return_value = mock_cfg

        with patch("builtins.input", side_effect=KeyboardInterrupt):
            main()

    @patch("react_agent.cli.stream_response", side_effect=KeyboardInterrupt)
    @patch("react_agent.cli.create_agent")
    @patch("react_agent.cli.console")
    @patch("react_agent.cli.LLMConfig")
    @patch("sys.argv", ["cli.py", "--config", "/dev/null"])
    def test_keyboard_interrupt_during_stream(self, mock_config_cls, mock_console, mock_create_agent, mock_stream):
        mock_cfg = MagicMock()
        mock_config_cls.from_yaml.return_value = mock_cfg

        inputs = iter(["hello", "quit"])
        with patch("builtins.input", side_effect=inputs):
            main()

    @patch("react_agent.cli.stream_response", side_effect=RuntimeError("boom"))
    @patch("react_agent.cli.create_agent")
    @patch("react_agent.cli.console")
    @patch("react_agent.cli.LLMConfig")
    @patch("sys.argv", ["cli.py", "--config", "/dev/null"])
    def test_stream_error_handled(self, mock_config_cls, mock_console, mock_create_agent, mock_stream):
        mock_cfg = MagicMock()
        mock_config_cls.from_yaml.return_value = mock_cfg

        inputs = iter(["hello", "quit"])
        with patch("builtins.input", side_effect=inputs):
            main()

    @patch("react_agent.cli.stream_response")
    @patch("react_agent.cli.create_agent")
    @patch("react_agent.cli.console")
    @patch("react_agent.cli.LLMConfig")
    @patch("sys.argv", ["cli.py", "--model", "m", "--base-url", "http://u",
                         "--api-key", "k", "--temperature", "0.9", "--config", "/dev/null"])
    def test_cli_args_override_config(self, mock_config_cls, mock_console, mock_create_agent, mock_stream):
        mock_cfg = MagicMock()
        mock_config_cls.from_yaml.return_value = mock_cfg

        with patch("builtins.input", return_value="quit"):
            main()

        assert mock_cfg.model == "m"
        assert mock_cfg.base_url == "http://u"
        assert mock_cfg.api_key == "k"
        assert mock_cfg.temperature == 0.9

    @patch("react_agent.cli.stream_response")
    @patch("react_agent.cli.create_agent")
    @patch("react_agent.cli.console")
    @patch("react_agent.cli.LLMConfig")
    @patch("sys.argv", ["cli.py"])
    def test_default_config_path(self, mock_config_cls, mock_console, mock_create_agent, mock_stream):
        mock_cfg = MagicMock()
        mock_config_cls.from_yaml.return_value = mock_cfg

        with patch("builtins.input", return_value="quit"):
            main()

        # Called without explicit path argument
        mock_config_cls.from_yaml.assert_called_once_with()


class TestMainModule:
    @patch("react_agent.cli.main")
    def test_dunder_main(self, mock_main):
        """Verify __main__.py calls main()."""
        import react_agent.__main__  # noqa: F401
        mock_main.assert_called()
