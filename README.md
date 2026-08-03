# Core AI Chat Engine (erofic.ai)

A headless, event-driven AI chat engine built with **FastAPI**, **SQLite** (SQLAlchemy 2.0 Async), and **OpenAI's SDK**. Designed to simulate human conversational behavior with event triggers, time-aware context management, and structured LLM actions.

---

## 📚 Project Documentation & References

- **[REQUIREMENTS.md](REQUIREMENTS.md)**: Full project specifications, architecture, data models, LLM action schemas, context management rules, and safety guardrails.
- **[ROADMAP.md](ROADMAP.md)**: Phased task breakdown and completion status (All 7 phases completed!).

---

## ⚡ Core Features & Capabilities

- **Event-Driven Architecture**: Operates on discrete triggers (user message API calls or background timer elapses), executes bounded logic, and spins down.
- **Multiple Sequential Texts**: The LLM can send multiple `speak` actions in a single turn to break up text into natural, human-like short messages.
- **Autonomous Wake-Up Timers (`set_timer`)**: The LLM can set a wake-up timer (`delay_seconds` between 10 and 60 seconds) to re-evaluate context at a future time.
- **Time-Aware Context Engine**: Injects current system time and time elapsed since the last message into every LLM call (e.g. *"System: It is currently 2:00 PM. The user has not replied in 4 hours."*).
- **Safety & Invariant Guardrails**:
  - **Single Pending Timer Invariant**: At any given time, at most 1 pending timer can exist per session.
  - **Timer Auto-Cancellation**: Any existing pending timer for a session is automatically marked `cancelled` whenever a new event occurs or a new timer is set.
  - **Recursion Limit**: Prevents infinite talking loops (max 3 consecutive assistant messages without user intervention).
  - **Idempotency & Fallback**: Atomic status updates mark background tasks as `completed` before execution; safe error handling for malformed LLM responses.

---

## 🛠️ Tech Stack

- **Language**: Python 3.11+ (Python 3.14 compatible)
- **Framework**: FastAPI (REST API & background event orchestration)
- **Database**: SQLite (via SQLAlchemy 2.0 Async + `aiosqlite`)
- **LLM Integration**: OpenAI Python SDK (Structured JSON schemas)
- **Scheduler**: Async Background Worker (1-second polling loop)
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
# On Linux/macOS:
source .venv/bin/activate
# On Windows (cmd/powershell):
# .venv\Scripts\activate
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

To wipe all sessions, messages, and scheduled tasks to start fresh, delete the SQLite database file:

```bash
rm -f sql_app.db
```

The next time you start the app server (`uvicorn app.main:app`), it will automatically create a clean, empty database.

---

## 🏃 Running the Application

Start the FastAPI development server using `uvicorn`:

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
*Response:*
```json
{
  "id": "3f9c6d40-8a12-4c56-b789-0123456789ab",
  "system_prompt": "You are a friendly companion. Keep responses brief.",
  "created_at": "2026-08-03T20:00:00Z",
  "updated_at": "2026-08-03T20:00:00Z"
}
```

### 2. Fetch All Sessions (`GET /sessions`)

```bash
curl -X GET "http://127.0.0.1:8000/sessions"
```

### 3. Send a User Message (`POST /sessions/{id}/message`)

```bash
curl -X POST "http://127.0.0.1:8000/sessions/3f9c6d40-8a12-4c56-b789-0123456789ab/message" \
     -H "Content-Type: application/json" \
     -d '{"content": "Hey there! How are you?"}'
```
*Response:*
```json
{
  "id": "e8d9c0a1-2b3c-4d5e-6f7a-8b9c0d1e2f3a",
  "session_id": "3f9c6d40-8a12-4c56-b789-0123456789ab",
  "role": "user",
  "content": "Hey there! How are you?",
  "timestamp": "2026-08-03T20:01:00Z"
}
```

### 4. Fetch Message History (`GET /sessions/{id}/messages`)

Clients poll this endpoint to view newly created assistant messages and delayed scheduled messages:

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
│   ├── models/       # SQLAlchemy ORM models (Session, Message, ScheduledTask)
│   └── scheduler/    # Background polling worker (app/scheduler/worker.py)
├── tests/            # Test suite (test_db.py, test_context.py, test_engine.py, test_api.py, test_scheduler.py)
├── .env.example      # Example environment configuration
├── pytest.ini        # Pytest configuration
├── README.md         # Project documentation & quickstart guide
├── REQUIREMENTS.md   # Core requirements & specification document
├── ROADMAP.md        # Implementation roadmap & task checklists
└── requirements.txt  # Python package dependencies
```

---

## 📌 Implementation Status

- [x] **Phase 1: Project Setup & Environment Configuration**
- [x] **Phase 2: Data Layer & Database Models** (Session, Message, ScheduledTask & CRUD)
- [x] **Phase 3: LLM Interface & Schema Engine** (Structured actions, context manager, time injection & OpenAI SDK)
- [x] **Phase 4: Core Event Engine & Guardrails** (Event cycle processor & 3-message recursion guardrail)
- [x] **Phase 5: Scheduler & Background Execution Worker** (1-second polling worker with idempotency)
- [x] **Phase 6: FastAPI Web API & Endpoints** (`POST /sessions`, `POST /sessions/{id}/message`, `GET /sessions/{id}/messages`)
- [x] **Phase 7: End-to-End Integration Testing** (12 unit & integration tests passing)
