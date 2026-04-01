"""FastAPI web UI for the react agent."""

import json
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from react_agent.agent import create_agent
from react_agent.config import LLMConfig

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"

app = FastAPI()
_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        cfg = LLMConfig.from_yaml(_CONFIG_PATH) if _CONFIG_PATH.exists() else LLMConfig.from_yaml()
        _agent = create_agent(cfg)
    return _agent


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
async def index():
    return _HTML


@app.post("/chat")
async def chat(req: ChatRequest):
    async def stream():
        agent = _get_agent()
        current_tool_calls: dict = {}
        try:
            async for event in agent.astream(
                {"messages": [("user", req.message)]},
                stream_mode="messages",
            ):
                msg, _metadata = event

                if msg.type == "AIMessageChunk":
                    reasoning = msg.additional_kwargs.get("reasoning_content", "")
                    if reasoning:
                        yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning})}\n\n"
                    if msg.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': msg.content})}\n\n"

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
                    matched_id = next(
                        (k for k, v in current_tool_calls.items() if v["name"] == msg.name),
                        next(iter(current_tool_calls), None),
                    )
                    if matched_id is not None:
                        tc = current_tool_calls.pop(matched_id)
                        try:
                            args = json.loads(tc["args_str"])
                        except (json.JSONDecodeError, ValueError):
                            args = {"raw": tc["args_str"]}
                        result = msg.content
                        if len(result) > 2000:
                            result = result[:2000] + "\n… (truncated)"
                        yield f"data: {json.dumps({'type': 'tool', 'name': tc['name'], 'args': args, 'result': result})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

        yield 'data: {"type":"done"}\n\n'

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def run():
    import uvicorn

    host, port = "0.0.0.0", 8000
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--host" and i + 1 < len(args):
            host = args[i + 1]
        elif a == "--port" and i + 1 < len(args):
            port = int(args[i + 1])

    uvicorn.run("react_agent.web:app", host=host, port=port)


_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ReAct Agent</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #f0f2f5;
    height: 100dvh;
    display: flex;
    flex-direction: column;
  }
  #log {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .bubble {
    max-width: min(75%, 720px);
    padding: 0.55rem 0.85rem;
    border-radius: 14px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 0.95rem;
  }
  .user   { align-self: flex-end;   background: #0b7de0; color: #fff; }
  .agent  { align-self: flex-start; background: #fff;    border: 1px solid #dde1e7; color: #111; }
  .agent.empty { display: none; }
  details.think {
    align-self: flex-start;
    max-width: min(75%, 720px);
    background: #f7f7f7;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 0.4rem 0.7rem;
    font-size: 0.82rem;
  }
  details.think summary {
    cursor: pointer;
    font-style: italic;
    color: #bbb;
    user-select: none;
    list-style: none;
  }
  details.think summary::before { content: "▶ "; font-size: 0.7rem; }
  details.think[open] summary::before { content: "▼ "; }
  details.think pre {
    margin-top: 0.4rem;
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 0.78rem;
    color: #aaa;
    font-family: inherit;
    max-height: 200px;
    overflow-y: auto;
  }
  details.tool {
    align-self: flex-start;
    max-width: min(75%, 720px);
    background: #fffbe6;
    border: 1px solid #f0c040;
    border-radius: 10px;
    padding: 0.4rem 0.7rem;
    font-size: 0.82rem;
    color: #555;
  }
  details.tool summary {
    cursor: pointer;
    font-weight: 600;
    color: #92610a;
    user-select: none;
    list-style: none;
  }
  details.tool summary::before { content: "▶ "; font-size: 0.7rem; }
  details.tool[open] summary::before { content: "▼ "; }
  details.tool pre {
    margin-top: 0.4rem;
    white-space: pre-wrap;
    word-break: break-all;
    font-size: 0.78rem;
    color: #444;
    background: #fdf6dc;
    padding: 0.4rem;
    border-radius: 6px;
  }
  .label { font-size: 0.7rem; color: #999; margin-top: 0.1rem; }
  .error-bubble {
    align-self: flex-start;
    max-width: min(75%, 720px);
    padding: 0.55rem 0.85rem;
    border-radius: 14px;
    background: #fff0f0;
    border: 1px solid #f5c6c6;
    color: #c0392b;
    font-size: 0.9rem;
  }
  #bar {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: #fff;
    border-top: 1px solid #dde1e7;
  }
  #msg {
    flex: 1;
    padding: 0.55rem 0.85rem;
    border: 1px solid #ccc;
    border-radius: 20px;
    font-size: 0.95rem;
    outline: none;
    resize: none;
    max-height: 120px;
    overflow-y: auto;
  }
  #msg:focus { border-color: #0b7de0; }
  #send {
    padding: 0.55rem 1.1rem;
    background: #0b7de0;
    color: #fff;
    border: none;
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.95rem;
    font-weight: 600;
    white-space: nowrap;
  }
  #send:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
</head>
<body>
<div id="log"></div>
<form id="bar" onsubmit="return false">
  <textarea id="msg" rows="1" placeholder="Message the agent…" autofocus></textarea>
  <button id="send" type="submit">Send</button>
</form>
<script>
const log  = document.getElementById('log');
const msg  = document.getElementById('msg');
const send = document.getElementById('send');

function addBubble(cls, text) {
  const el = document.createElement('div');
  el.className = 'bubble ' + cls + (text ? '' : ' empty');
  el.textContent = text;
  log.appendChild(el);
  scrollDown();
  return el;
}

function addTool(name, args, result) {
  const el = document.createElement('details');
  el.className = 'tool';
  const argsStr = JSON.stringify(args, null, 2);
  el.innerHTML =
    `<summary>${name}</summary>` +
    `<pre><b>args</b>\n${esc(argsStr)}</pre>` +
    `<pre><b>result</b>\n${esc(result)}</pre>`;
  log.appendChild(el);
  scrollDown();
}

function addError(text) {
  const el = document.createElement('div');
  el.className = 'error-bubble';
  el.textContent = 'Error: ' + text;
  log.appendChild(el);
  scrollDown();
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function scrollDown() {
  log.scrollTop = log.scrollHeight;
}

// auto-grow textarea
msg.addEventListener('input', () => {
  msg.style.height = 'auto';
  msg.style.height = msg.scrollHeight + 'px';
});

msg.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
});

send.addEventListener('click', submit);

async function submit() {
  const text = msg.value.trim();
  if (!text || send.disabled) return;

  msg.value = '';
  msg.style.height = 'auto';
  send.disabled = true;
  msg.disabled = true;

  addBubble('user', text);

  let agentEl = null, agentText = '';
  let thinkEl = null, thinkText = '';
  let parseState = 'normal', tagBuf = '';

  function resetStreamState() {
    agentEl = null; agentText = '';
    thinkEl = null; thinkText = '';
    parseState = 'normal'; tagBuf = '';
  }

  function emitNormal(ch) {
    agentText += ch;
    if (!agentEl) { agentEl = addBubble('agent', ''); }
    agentEl.textContent = agentText;
    agentEl.classList.remove('empty');
    scrollDown();
  }

  function emitThink(ch) {
    thinkText += ch;
    if (!thinkEl) {
      thinkEl = document.createElement('details');
      thinkEl.className = 'think';
      thinkEl.innerHTML = '<summary>Thinking…</summary><pre></pre>';
      log.appendChild(thinkEl);
    }
    thinkEl.querySelector('pre').textContent = thinkText;
    scrollDown();
  }

  function processToken(token) {
    for (const ch of token) {
      switch (parseState) {
        case 'normal':
          if (ch === '<') { parseState = 'open_tag'; tagBuf = '<'; }
          else emitNormal(ch);
          break;
        case 'open_tag':
          tagBuf += ch;
          if ('<think>'.startsWith(tagBuf)) {
            if (tagBuf === '<think>') { parseState = 'thinking'; tagBuf = ''; thinkEl = null; thinkText = ''; }
          } else { emitNormal(tagBuf); tagBuf = ''; parseState = 'normal'; }
          break;
        case 'thinking':
          if (ch === '<') { parseState = 'close_tag'; tagBuf = '<'; }
          else emitThink(ch);
          break;
        case 'close_tag':
          tagBuf += ch;
          if ('</think>'.startsWith(tagBuf)) {
            if (tagBuf === '</think>') { parseState = 'normal'; tagBuf = ''; }
          } else { emitThink(tagBuf); tagBuf = ''; parseState = 'thinking'; }
          break;
      }
    }
  }

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });

    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = '';

    outer: while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });

      const lines = buf.split('\\n');
      buf = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const ev = JSON.parse(line.slice(6));

        if (ev.type === 'reasoning') {
          emitThink(ev.content);

        } else if (ev.type === 'token') {
          processToken(ev.content);

        } else if (ev.type === 'tool') {
          resetStreamState();
          addTool(ev.name, ev.args, ev.result);

        } else if (ev.type === 'error') {
          addError(ev.content);

        } else if (ev.type === 'done') {
          break outer;
        }
      }
    }
  } catch (err) {
    addError(err.message);
  }

  send.disabled = false;
  msg.disabled = false;
  msg.focus();
}
</script>
</body>
</html>
"""
