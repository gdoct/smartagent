#!/usr/bin/env python3
"""Command-line interface for the react agent."""

import argparse
import json
import readline  # noqa: F401 — enables arrow keys/history in input()
import sys

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from react_agent.agent import create_agent
from react_agent.config import LLMConfig

console = Console()


def print_tool_call(name: str, args: dict):
    args_str = json.dumps(args, indent=2)
    console.print(
        Panel(
            Syntax(args_str, "json", theme="monokai"),
            title=f"Tool Call: [bold yellow]{name}[/bold yellow]",
            border_style="yellow",
        )
    )


def print_tool_result(name: str, content: str):
    if len(content) > 2000:
        content = content[:2000] + "\n... (truncated)"
    console.print(
        Panel(
            content,
            title=f"Tool Result: [bold green]{name}[/bold green]",
            border_style="green",
        )
    )


def stream_response(agent, user_input: str):
    """Stream agent response, printing tokens as they arrive."""
    current_text = ""
    current_tool_calls = {}  # id -> {name, args_str}
    live = None

    for event in agent.stream(
        {"messages": [("user", user_input)]},
        stream_mode="messages",
    ):
        msg, _metadata = event

        # AIMessageChunk with content — stream text token by token
        if msg.type == "AIMessageChunk":
            if msg.content:
                if live is None:
                    live = Live(console=console, refresh_per_second=15)
                    live.start()
                current_text += msg.content
                live.update(
                    Panel(
                        Markdown(current_text), title="Assistant", border_style="cyan"
                    )
                )

            # Accumulate tool call chunks
            for tc_chunk in msg.tool_call_chunks:
                tc_id = tc_chunk.get("id")
                if tc_id and tc_id not in current_tool_calls:
                    current_tool_calls[tc_id] = {
                        "name": tc_chunk.get("name", ""),
                        "args_str": "",
                    }
                if tc_id and tc_chunk.get("args"):
                    current_tool_calls[tc_id]["args_str"] += tc_chunk["args"]

        elif msg.type == "tool":
            # Before printing tool result, flush any pending text/tool calls
            if live is not None:
                live.stop()
                live = None
                current_text = ""

            # Print accumulated tool calls
            for tc_id, tc in current_tool_calls.items():
                try:
                    args = json.loads(tc["args_str"])
                except (json.JSONDecodeError, ValueError):
                    args = {"raw": tc["args_str"]}
                print_tool_call(tc["name"], args)
            current_tool_calls = {}

            print_tool_result(msg.name, msg.content)

    # Flush any remaining streamed text
    if live is not None:
        live.stop()
        current_text = ""


def parse_args():
    parser = argparse.ArgumentParser(description="ReAct Agent CLI")
    parser.add_argument("--model", default=None, help="Override model name")
    parser.add_argument("--base-url", default=None, help="Override API base URL")
    parser.add_argument("--api-key", default=None, help="Override API key")
    parser.add_argument(
        "--temperature", type=float, default=None, help="Override sampling temperature"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config.yaml (default: config.yaml in project root)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    from pathlib import Path

    config_path = Path(args.config) if args.config else None
    config = LLMConfig.from_yaml(config_path) if config_path else LLMConfig.from_yaml()

    # CLI args override config file values
    if args.model is not None:
        config.model = args.model
    if args.base_url is not None:
        config.base_url = args.base_url
    if args.api_key is not None:
        config.api_key = args.api_key
    if args.temperature is not None:
        config.temperature = args.temperature

    agent = create_agent(config)

    console.print(
        Panel(
            f"[bold]ReAct Agent[/bold]\nModel: {config.model}\nType [bold red]quit[/bold red] to exit.",
            border_style="blue",
        )
    )

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            console.print("Goodbye!")
            break

        try:
            stream_response(agent, user_input)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    main()
