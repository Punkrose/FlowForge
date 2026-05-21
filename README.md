# FlowForge

> AI-powered browser automation framework — describe what you want in plain English, and FlowForge plans and executes it.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)

---

## Features

- **Natural Language Tasks** — describe browser actions in English; the LLM generates a structured step plan
- **Stealth Browsing** — built on CloakBrowser for anti-detection; falls back to vanilla Playwright with stealth flags
- **Persistent Profiles** — save and reuse browser state (cookies, localStorage) across runs
- **OTP Support** — auto-detect OTP widgets and fetch codes from Gmail
- **Progress Tracking** — JSON-based progress files for resumable tasks and external monitoring
- **REST API** — FastAPI server for remote task submission, status polling, and profile management
- **Any LLM Provider** — works with any OpenAI-compatible API (OpenAI, Anthropic via proxy, local models, etc.)
- **Screenshot Capture** — automatic screenshots at each step for audit trails

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FlowForge Engine                          │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────────────────┐ │
│  │  FlowForge   │   │ BrowserSession│   │     OTPHandler       │ │
│  │ (automator)  │──▶│ (CloakBrowser)│◀──│ (detect / fetch /    │ │
│  │              │   │              │   │  fill)                │ │
│  └──────┬───────┘   └──────────────┘   └───────────────────────┘ │
│         │                                                        │
│  ┌──────▼───────┐   ┌──────────────┐   ┌───────────────────────┐ │
│  │ LLM Planner  │   │ProfileManager│   │    TaskProgress       │ │
│  │ (OpenAI API) │   │ (lock / CRUD)│   │ (JSON persistence)    │ │
│  └──────────────┘   └──────────────┘   └───────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
         │                                           ▲
         ▼                                           │
┌─────────────────┐                        ┌─────────────────────┐
│  REST API (POST  │                        │  GET /api/tasks/{id} │
│  /api/tasks)     │───────────────────────▶│  (status polling)    │
└─────────────────┘                        └─────────────────────┘
```

---

## Quick Start

### Installation

```bash
pip install flowforge

# Or install from source
git clone https://github.com/Punkrose/FlowForge.git
cd FlowForge
pip install -e ".[stealth,gmail]"

# Install browser binaries
playwright install chromium
```

### Environment Setup

```bash
export FLOWFORGE_API_KEY="sk-your-api-key"
export FLOWFORGE_BASE_URL="https://api.openai.com/v1"   # or any OpenAI-compatible endpoint
export FLOWFORGE_MODEL="gpt-4o"
```

### Python Usage

```python
import asyncio
from flowforge import FlowForge

async def main():
    engine = FlowForge(
        api_key="sk-...",
        base_url="https://api.openai.com/v1",
        model="gpt-4o",
    )

    result = await engine.run(
        task_description="Go to https://example.com and take a screenshot",
        headless=True,
    )

    print(f"Status: {result.status.value}")
    print(f"Steps completed: {result.steps_completed}/{len(result.steps)}")

asyncio.run(main())
```

### REST API

```bash
# Start the server
uvicorn flowforge.api.server:app --host 0.0.0.0 --port 8080

# Submit a task
curl -X POST http://localhost:8080/api/tasks \
     -H "Content-Type: application/json" \
     -d '{"task": "Go to https://example.com and extract the page title"}'

# Check status
curl http://localhost:8080/api/tasks/<task-id>

# List profiles
curl http://localhost:8080/api/profiles
```

---

## API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check and stats |
| `POST` | `/api/tasks` | Create and start a task |
| `GET` | `/api/tasks` | List all tasks |
| `GET` | `/api/tasks/{id}` | Get task status and result |
| `DELETE` | `/api/tasks/{id}` | Cancel a running task |
| `GET` | `/api/profiles` | List browser profiles |
| `POST` | `/api/profiles` | Create a new profile |
| `DELETE` | `/api/profiles/{name}` | Delete a profile |

Interactive docs at `http://localhost:8080/docs` (Swagger UI).

### TaskCreate Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `task` | `str` | *required* | Natural language task description |
| `profile` | `str` | `null` | Browser profile name |
| `headless` | `bool` | `true` | Run browser headlessly |
| `max_steps` | `int` | `50` | Maximum plan length |
| `timeout_seconds` | `int` | `300` | Execution timeout |
| `extra_context` | `str` | `null` | Additional planner context |

### Supported Browser Actions

`navigate` · `click` · `type` · `fill` · `select` · `wait` · `wait_for_selector` · `screenshot` · `extract_text` · `scroll` · `press_key` · `hover` · `upload_file` · `evaluate` · `otp_fill` · `assert_text` · `assert_visible`

---

## Project Structure

```
FlowForge/
├── flowforge/
│   ├── __init__.py              # Package init with version
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── automator.py         # Main FlowForge orchestrator
│   │   ├── session.py           # BrowserSession (CloakBrowser wrapper)
│   │   ├── otp_handler.py       # OTP detection and filling
│   │   ├── profile_manager.py   # Profile CRUD with file locking
│   │   └── progress.py          # JSON-based progress tracking
│   ├── api/
│   │   ├── __init__.py
│   │   └── server.py            # FastAPI REST server
│   └── models/
│       ├── __init__.py
│       └── task.py              # Pydantic data models
├── examples/
│   ├── basic_usage.py           # Async Python example
│   └── api_server.py            # Server startup example
├── tests/
│   └── test_progress.py         # Unit tests for progress tracking
├── pyproject.toml               # Package configuration
├── LICENSE                      # MIT License
└── README.md
```

---

## Development

```bash
# Install dev dependencies
pip install -e ".[stealth,gmail,dev]"

# Run tests
pytest

# Lint
ruff check flowforge/

# Type check
mypy flowforge/
```

---

## License

[MIT](LICENSE)
