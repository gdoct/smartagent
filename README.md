# react-agent

[![Tests](https://github.com/gdoct/smartagent/actions/workflows/tests.yml/badge.svg)](https://github.com/gdoct/smartagent/actions/workflows/tests.yml)
[![Lint](https://github.com/gdoct/smartagent/actions/workflows/lint.yml/badge.svg)](https://github.com/gdoct/smartagent/actions/workflows/lint.yml)
[![CodeQL](https://github.com/gdoct/smartagent/actions/workflows/codeql.yml/badge.svg)](https://github.com/gdoct/smartagent/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/github/gdoct/smartagent/branch/main/graph/badge.svg?token=GIygrwT6jP)](https://codecov.io/github/gdoct/smartagent)

A ReAct (Reasoning + Acting) agent powered by LangGraph. It connects to any OpenAI-compatible API and comes with built-in tools for shell execution, file I/O, web search, and more.

## Quickstart

```bash
# create a virtual environment and install
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# configure your LLM provider
cp config.example.yaml config.yaml   # then edit config.yaml

# run the agent
react-agent
# or
python -m react_agent
```

## Configuration

Copy `config.example.yaml` to `config.yaml` and set your values:

```yaml
llm:
  model: ""                            # leave empty for the server's default
  base_url: "http://localhost:1234/v1" # LM Studio, Ollama, OpenAI, etc.
  api_key: "lm-studio"
  temperature: 0.0
```

CLI flags override the config file:

```bash
react-agent --model gpt-4 --base-url https://api.openai.com/v1 --api-key sk-...
```

## Built-in tools

| Tool | Description |
|------|-------------|
| `shell` | Execute a shell command |
| `read_file` | Read a file |
| `write_file` | Write a file |
| `calculator` | Evaluate a math expression |
| `python` | Run a Python script |
| `web_fetch` | Fetch raw HTML from a URL |
| `web_text` | Fetch a URL and extract visible text |
| `duckduckgo_search` | Search the web via DuckDuckGo |
| `current_date` | Get today's date |
| `current_time` | Get the current time |

## Project structure

```
src/react_agent/
    __init__.py      # package root
    __main__.py      # python -m react_agent entry point
    agent.py         # agent creation
    cli.py           # interactive CLI with streaming
    config.py        # YAML-based LLM configuration
    tools.py         # tool definitions
tests/
    test_agent.py
    test_cli.py
    test_config.py
    test_tools.py
```

## Tests

```bash
python -m pytest
python -m pytest --cov   # with coverage
```

## License

MIT
