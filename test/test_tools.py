"""Tests for tools module."""

import subprocess
from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pytest

from react_agent.tools import (
    shell,
    read_file,
    write_file,
    calculator,
    python,
    web_fetch,
    web_text,
    duckduckgo_search,
    current_date,
    current_time,
    ALL_TOOLS,
)


class TestShell:
    def test_successful_command(self):
        result = shell.invoke({"command": "echo hello"})
        assert result == "hello"

    def test_failing_command_includes_stderr(self):
        result = shell.invoke({"command": "ls /nonexistent_dir_12345"})
        assert "STDERR:" in result or "Return code:" in result

    def test_empty_output(self):
        result = shell.invoke({"command": "true"})
        assert result == "(no output)"

    @patch("react_agent.tools.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=30))
    def test_timeout(self, mock_run):
        result = shell.invoke({"command": "sleep 999"})
        assert "timed out" in result

    def test_nonzero_return_code_no_stderr(self):
        result = shell.invoke({"command": "bash -c 'exit 42'"})
        assert "Return code: 42" in result


class TestReadFile:
    def test_read_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("content here")
        result = read_file.invoke({"path": str(f)})
        assert result == "content here"

    def test_file_not_found(self):
        result = read_file.invoke({"path": "/nonexistent_file_12345"})
        assert "file not found" in result

    def test_permission_denied(self, tmp_path):
        f = tmp_path / "noperm.txt"
        f.write_text("x")
        f.chmod(0o000)
        try:
            result = read_file.invoke({"path": str(f)})
            assert "permission denied" in result
        finally:
            f.chmod(0o644)


class TestWriteFile:
    def test_write_new_file(self, tmp_path):
        f = tmp_path / "out.txt"
        result = write_file.invoke({"path": str(f), "content": "hello"})
        assert "Successfully wrote" in result
        assert f.read_text() == "hello"

    def test_overwrite_existing(self, tmp_path):
        f = tmp_path / "out.txt"
        f.write_text("old")
        write_file.invoke({"path": str(f), "content": "new"})
        assert f.read_text() == "new"

    def test_permission_denied(self, tmp_path):
        d = tmp_path / "noperm"
        d.mkdir()
        d.chmod(0o000)
        try:
            result = write_file.invoke({"path": str(d / "file.txt"), "content": "x"})
            assert "permission denied" in result
        finally:
            d.chmod(0o755)


class TestCalculator:
    def test_basic_arithmetic(self):
        assert calculator.invoke({"expression": "2 + 2"}) == "4"

    def test_math_module(self):
        assert calculator.invoke({"expression": "math.sqrt(16)"}) == "4.0"

    def test_builtins(self):
        assert calculator.invoke({"expression": "abs(-5)"}) == "5"
        assert calculator.invoke({"expression": "min(3, 1, 2)"}) == "1"
        assert calculator.invoke({"expression": "max(3, 1, 2)"}) == "3"
        assert calculator.invoke({"expression": "round(3.7)"}) == "4"
        assert calculator.invoke({"expression": "sum([1, 2, 3])"}) == "6"
        assert calculator.invoke({"expression": "pow(2, 3)"}) == "8"

    def test_invalid_expression(self):
        result = calculator.invoke({"expression": "invalid_var"})
        assert "Error:" in result

    def test_syntax_error(self):
        result = calculator.invoke({"expression": "2 +"})
        assert "Error:" in result


class TestPython:
    def test_successful_script(self):
        result = python.invoke({"script": "print('hello world')"})
        assert "hello world" in result

    def test_script_with_stderr(self):
        result = python.invoke({"script": "import sys; sys.stderr.write('warn\\n')"})
        assert "STDERR:" in result
        assert "warn" in result

    def test_script_error(self):
        result = python.invoke({"script": "raise ValueError('boom')"})
        assert "Return code:" in result
        assert "boom" in result

    def test_no_output(self):
        result = python.invoke({"script": "x = 1"})
        assert result == "(no output)"

    def test_timeout(self, tmp_path):
        script_file = tmp_path / "timeout_test.py"
        script_file.write_text("x = 1")

        with patch("react_agent.tools.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=60)):
            with patch("tempfile.NamedTemporaryFile") as mock_tmp:
                mock_ctx = MagicMock()
                mock_ctx.name = str(script_file)
                mock_ctx.write = MagicMock()
                mock_tmp.return_value.__enter__ = MagicMock(return_value=mock_ctx)
                mock_tmp.return_value.__exit__ = MagicMock(return_value=False)
                # The function uses local imports, so we patch at the source
                result = python.invoke({"script": "import time; time.sleep(999)"})
        assert "timed out" in result


class TestWebFetch:
    @patch("requests.get")
    def test_successful_fetch(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "<html>hello</html>"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        result = web_fetch.invoke({"url": "http://example.com"})
        assert result == "<html>hello</html>"

    @patch("requests.get")
    def test_truncates_long_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "x" * 200_000
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        result = web_fetch.invoke({"url": "http://example.com"})
        assert len(result) == 100_000

    @patch("requests.get")
    def test_request_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("connection failed")
        result = web_fetch.invoke({"url": "http://example.com"})
        assert "Error:" in result


class TestWebText:
    @patch("requests.get")
    def test_successful_extraction(self, mock_get):
        html = "<html><body><p>Hello World</p><script>var x=1;</script></body></html>"
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        result = web_text.invoke({"url": "http://example.com"})
        assert "Hello World" in result
        assert "var x=1" not in result

    @patch("requests.get")
    def test_strips_nav_header_footer(self, mock_get):
        html = (
            "<html><body>"
            "<header>Header</header>"
            "<nav>Nav</nav>"
            "<p>Content</p>"
            "<footer>Footer</footer>"
            "<noscript>NoScript</noscript>"
            "<style>.x{}</style>"
            "</body></html>"
        )
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        result = web_text.invoke({"url": "http://example.com"})
        assert "Content" in result
        assert "Header" not in result
        assert "Nav" not in result
        assert "Footer" not in result

    @patch("requests.get")
    def test_truncates_long_text(self, mock_get):
        html = f"<html><body><p>{'x' * 100_000}</p></body></html>"
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        result = web_text.invoke({"url": "http://example.com"})
        assert len(result) <= 50_000

    @patch("requests.get")
    def test_request_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("timeout")
        result = web_text.invoke({"url": "http://example.com"})
        assert "Error:" in result


class TestDuckDuckGoSearch:
    @patch("ddgs.DDGS")
    def test_successful_search(self, mock_ddgs_cls):
        mock_ddgs = MagicMock()
        mock_ddgs.text.return_value = [
            {"title": "Result 1", "href": "http://r1.com", "body": "Body 1"},
            {"title": "Result 2", "href": "http://r2.com", "body": "Body 2"},
        ]
        mock_ddgs_cls.return_value = mock_ddgs
        result = duckduckgo_search.invoke({"query": "test"})
        assert "Result 1" in result
        assert "http://r1.com" in result
        assert "Result 2" in result

    @patch("ddgs.DDGS")
    def test_no_results(self, mock_ddgs_cls):
        mock_ddgs = MagicMock()
        mock_ddgs.text.return_value = []
        mock_ddgs_cls.return_value = mock_ddgs
        result = duckduckgo_search.invoke({"query": "test"})
        assert result == "No results found."

    @patch("ddgs.DDGS")
    def test_result_without_body(self, mock_ddgs_cls):
        mock_ddgs = MagicMock()
        mock_ddgs.text.return_value = [
            {"title": "T", "href": "http://x.com"},
        ]
        mock_ddgs_cls.return_value = mock_ddgs
        result = duckduckgo_search.invoke({"query": "test"})
        assert "T" in result

    @patch("ddgs.DDGS")
    def test_exception(self, mock_ddgs_cls):
        mock_ddgs_cls.side_effect = Exception("API error")
        result = duckduckgo_search.invoke({"query": "test"})
        assert "Error:" in result


class TestCurrentDate:
    def test_returns_iso_format(self):
        result = current_date.invoke({})
        assert result == date.today().isoformat()


class TestCurrentTime:
    def test_returns_time_format(self):
        result = current_time.invoke({})
        # Validate it parses as a time
        datetime.strptime(result, "%H:%M:%S")


class TestAllTools:
    def test_all_tools_list(self):
        assert len(ALL_TOOLS) == 10
        names = {t.name for t in ALL_TOOLS}
        assert names == {
            "shell", "read_file", "write_file", "calculator", "python",
            "duckduckgo_search", "web_fetch", "web_text", "current_date", "current_time",
        }
