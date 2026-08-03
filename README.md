# Core AI Chat Engine (erofic.ai)

A headless, event-driven AI chat engine built with FastAPI, SQLite (SQLAlchemy async), and OpenAI's SDK. Designed to simulate human conversational behavior with asynchronous messaging, time awareness, delayed responses, and proactive "double-texting".

---

## 📚 Project Documentation & References

- **[REQUIREMENTS.md](REQUIREMENTS.md)**: Full project specifications, architecture, data models, LLM action schemas, context management rules, and safety guardrails.
- **[ROADMAP.md](ROADMAP.md)**: Phased task breakdown and completion status for developers and CLI coding agents.

---

## 🛠️ Tech Stack

- **Language**: Python 3.11+ (Python 3.14 compatible)
- **Framework**: FastAPI (REST API & background event orchestration)
- **Database**: SQLite (via SQLAlchemy 2.0 Async + `aiosqlite`)
- **LLM Integration**: OpenAI Python SDK (Structured JSON schemas)
- **Scheduler**: APScheduler / Asyncio background worker
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
# On Windows (bash/cmd):
# .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration (.env)

Copy the `.env.example` file to `.env` and set your configuration variables:

```bash
cp .env.example .env
```

Key environment settings (`app/core/config.py`):
- `DATABASE_URL`: Database connection string (default: `sqlite+aiosqlite:///./sql_app.db`)
- `OPENAI_API_KEY`: Your OpenAI API Key (or OpenAI-compatible provider key)
- `OPENAI_MODEL`: LLM model identifier (default: `gpt-4o`)
- `LOG_LEVEL`: Logging verbosity (default: `INFO`)

---

## 🧪 Running Tests

Run the test suite using `pytest`:

```bash
pytest
```

To run tests with detailed output:

```bash
pytest -v
```

---

## 📁 Directory Structure

```text
erofic.ai/
├── app/
│   ├── api/          # FastAPI routers & endpoint schemas
│   ├── core/         # Settings & app configurations (app/core/config.py)
│   ├── db/           # Async database session, initialization, and CRUD helpers
│   ├── engine/       # LLM client, prompt builder, context manager, & safety guardrails
│   ├── models/       # SQLAlchemy ORM models (Session, Message, ScheduledTask)
│   └── scheduler/    # Background polling worker & task execution engine
├── tests/            # Test suite (test_db.py, etc.)
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
- [ ] **Phase 3: LLM Interface & Schema Engine** (In Progress)
- [ ] **Phase 4: Core Event Engine & Guardrails**
- [ ] **Phase 5: Scheduler & Background Execution Worker**
- [ ] **Phase 6: FastAPI Web API & Endpoints**
- [ ] **Phase 7: End-to-End Integration Testing**
