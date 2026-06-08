# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EulerAgent is a minimal (~3K lines), self-evolving autonomous agent framework that grants LLMs system-level control over a local computer. It supports browser, terminal, filesystem, keyboard/mouse input, screen vision, and mobile devices.

## Architecture

```
EulerAgent/
├── core/                     # Core code modules
│   ├── agentmain.py          # Application entry point
│   ├── agent_loop.py         # Loop engine (~127 lines)
│   ├── ea.py                 # Tool implementations (~589 lines)
│   ├── llm/                  # LLM adapter package (sessions, codecs, tool clients)
│   │   ├── __init__.py       #   public facade
│   │   └── _legacy.py        #   implementation (Strangler split in progress)
│   ├── llmcore.py            # Compat shim → llm package
│   ├── handlers/             # Handler extension point (BaseHandler pattern)
│   └── README.md
├── memory/                   # Layered memory system (L1-L4)
│   ├── *.sop.md              # SOP documents
│   ├── global_mem*.txt       # Global memory
│   ├── skill_search/         # Skill search
│   └── L4_raw_sessions/      # Historical sessions
├── assets/                   # Resource configuration
│   ├── images/, demo/        # Media assets
│   └── *.json                # Schema configs (tools_schema.json, etc.)
├── temp/                     # Runtime temporary files
├── frontends/                # Multiple UI frontends
│   ├── stapp2.py             # Streamlit frontend
│   ├── tuiapp_v2.py          # Textual TUI frontend
│   └── *.py                  # Bot frontends (telegram, qq, wechat, etc.)
└── TMWebDriver.py            # Browser control (root level)
```

**Critical**: `memory/`, `assets/`, `temp/` stay at project root — NOT inside `core/`. The `core/` modules reference them via `../assets`, `../memory`, `../temp` relative paths.

## Core Principles (from CONTRIBUTING.md)

- **Self-documenting code, minimal comments** — If code needs a paragraph to explain, rewrite it
- **Compact and visually uniform** — Fewer lines, consistent style, no fluff
- **Small change radius** — Changing A shouldn't ripple through B, C, D
- **More features → less code** — Good abstractions make the codebase shrink
- **Let it crash by failure radius** — Critical errors fail loud; trivial ones pass silently

## Development Commands

```bash
# Python version: 3.10-3.13 only (NOT 3.14 — incompatible with pywebview)

# Run Streamlit frontend
streamlit run frontends/stapp2.py

# Run TUI frontend
python frontends/tuiapp_v2.py

# Run desktop app
python launch.pyw

# Create virtual environment
uv venv .venv
source .venv/bin/activate

# Install minimal core dependencies
uv pip install requests beautifulsoup4 bottle simple-websocket-server aiohttp

# Install Streamlit UI dependencies
uv pip install streamlit

# Install all frontend dependencies
uv pip install -e ".[all-frontends]"
```

## Key Patterns

### Path References in core/
All paths from `core/` modules to shared directories use parent-relative paths:
```python
script_dir = os.path.dirname(os.path.abspath(__file__))
os.path.join(script_dir, '../assets/...')   # NOT 'assets/...'
os.path.join(script_dir, '../memory/...')   # NOT 'memory/...'
os.path.join(script_dir, '../temp/...')     # NOT 'temp/...'
```

### Agent Initialization
- `core/agentmain.py` contains `EulerAgent` class — the main entry point
- `core/agent_loop.py` contains `agent_runner_loop` — the execution loop
- `core/ea.py` contains `EulerAgentHandler` — tool implementations

### Memory Layers (L1-L4)
| Layer | Purpose |
|-------|---------|
| L1 | Working context |
| L2 | Global memory (shared across sessions) |
| L3 | SOP documents (crystallized skills) |
| L4 | Raw session archives |

## Import Notes

`core/agentmain.py` inserts `core/` itself at the front of `sys.path`, so sibling
modules import by bare name — there is **no** `core.` package prefix anywhere in the repo:

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # core/ becomes top-level
from llmcore import reload_ekeys, LLMSession, ...   # core/llmcore.py (shim → llm package)
from agent_loop import agent_runner_loop            # core/agent_loop.py
from ea import EulerAgentHandler                    # core/ea.py
```

`llmcore` is a compatibility shim; the implementation lives in the `core/llm/` package.

## PR Checklist

- Issue linked or context explained in ≤3 sentences
- Code passes self-check: small change radius, clear abstractions, minimal net lines
- No unnecessary dependencies added
- Paths in `core/` use `../` prefix for memory/assets/temp
