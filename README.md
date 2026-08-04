# Core AI Chat Engine (erofic.ai)

A headless, event-driven AI chat engine built with **FastAPI**, **SQLite** (SQLAlchemy 2.0 Async), and **OpenAI's SDK**. Designed to simulate human conversational behavior with event triggers, time-aware context management, and structured LLM responses.

---

## 📚 Project Documentation & References

- **[REQUIREMENTS.md](REQUIREMENTS.md)**: Full project specifications, architecture, data models, LLM action schemas, context management rules, and safety guardrails.
- **[ROADMAP.md](ROADMAP.md)**: Phased task breakdown and completion status.

---

## ⚡ Core Features & Capabilities

- **Event-Driven Architecture**: Operates on discrete triggers (user message API calls or background timer elapses), executes bounded logic, and spins down.
- **Multiple Sequential Texts**: The LLM can send multiple `speak` actions in a single turn to break up text into natural, human-like short messages.
- **Autonomous In-Memory Re-Pings**: The engine automatically schedules a 30-second background timer after every execution turn. If the user doesn't reply within 30 seconds, it wakes up the LLM to decide whether to send a follow-up check-in or remain silent.
- **Delineated Time & Event Context**: Groups relative elapsed time, triggers, and execution guidelines into a single, unified notice appended to the very end of the LLM context.
- **Safety & Invariant Guardrails**:
  - **Single Active Timer Invariant**: At any given time, at most 1 in-memory timer exists per session.
  - **Timer Auto-Cancellation**: Any existing timer for a session is automatically cancelled whenever a new event triggers.
  - **Recursion Limit**: Prevents infinite talking loops (max 3 consecutive assistant messages without user intervention).
  - **Idempotency & Fallback**: Fast fail recovery (10s retry timer fallback) on LLM call timeouts or exceptions.

---

## 🛠️ Tech Stack

- **Language**: Python 3.11+ (Python 3.14 compatible)
- **Framework**: FastAPI (REST API & background event orchestration)
- **Database**: SQLite (via SQLAlchemy 2.0 Async + `aiosqlite`)
- **LLM Integration**: OpenAI Python SDK (Structured JSON schemas)
- **Scheduler**: In-memory `asyncio` Timer Handles
- **Testing**: `pytest` & `pytest-asyncio`

---

## 🚀 Getting Started

### 1. Prerequisites

Ensure you have Python 3.11+ installed on your system.

### 2. Clone & Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd erofic.ai

# Create a Python virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration (.env)

Copy the `.env.example` file to `.env` and set your OpenAI API Key:

```bash
cp .env.example .env
```

Configuration parameters in `.env`:
- `DATABASE_URL`: Database connection string (`sqlite+aiosqlite:///./sql_app.db`)
- `OPENAI_API_KEY`: API authentication key (`ollama` or OpenAI key)
- `OPENAI_BASE_URL`: OpenAI-compatible endpoint URL (`http://localhost:11434/v1`)
- `OPENAI_MODEL`: LLM model identifier (`huihui_ai/llama3.2-abliterate:3b-instruct` or `gpt-4o`)
- `LOG_LEVEL`: Logging verbosity (`INFO`)

---

## 🗄️ Resetting the Database

To wipe all sessions and messages to start fresh, delete the SQLite database file:

```bash
rm -f sql_app.db
```

The next time you start the app server (`uvicorn app.main:app`), it will automatically create a clean, empty database.

---

## 🏃 Running the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload --port 8000
```

Once running:
- **Interactive OpenAPI / Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 📡 API Usage & Examples

### 1. Create a Chat Session (`POST /sessions`)

```bash
curl -X POST "http://127.0.0.1:8000/sessions" \
     -H "Content-Type: application/json" \
     -d '{"system_prompt": "You are a friendly companion. Keep responses brief."}'
```

### 2. Fetch All Sessions (`GET /sessions`)

```bash
curl -X GET "http://127.0.0.1:8000/sessions"
```

### 3. Send a User Message (`POST /sessions/{id}/message`)

```bash
curl -X POST "http://127.0.0.1:8000/sessions/3f9c6d40-8a12-4c56-b789-0123456789ab/message" \
     -H "Content-Type: application/json" \
     -d '{"content": "Hey there!"}'
```

### 4. Fetch Message History (`GET /sessions/{id}/messages`)

```bash
curl -X GET "http://127.0.0.1:8000/sessions/3f9c6d40-8a12-4c56-b789-0123456789ab/messages"
```

---

## 🧪 Running Tests

Run the full test suite using `pytest`:

```bash
pytest -v
```

---

## 📁 Directory Structure

```text
erofic.ai/
├── app/
│   ├── api/          # FastAPI routers & API schemas (POST /sessions, POST /message, GET /messages)
│   ├── core/         # Settings & app configurations (app/core/config.py)
│   ├── db/           # Async database session, init, and CRUD helpers (app/db/crud.py)
│   ├── engine/       # LLM client, prompt builder, context manager, & safety guardrails
│   ├── models/       # SQLAlchemy ORM models (Session, Message)
│   └── scheduler/    # In-memory timer manager (app/scheduler/manager.py)
├── tests/            # Test suite (test_db.py, test_context.py, test_engine.py, test_api.py, test_lock.py)
├── .env.example      # Example environment configuration
├── pytest.ini        # Pytest configuration
├── README.md         # Project documentation & quickstart guide
├── REQUIREMENTS.md   # Core requirements & specification document
├── ROADMAP.md        # Implementation roadmap & task checklists
└── requirements.txt  # Python package dependencies
```
