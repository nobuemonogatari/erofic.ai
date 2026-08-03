# Project Roadmap & Implementation Tasks

This document outlines the step-by-step roadmap for building the **Core AI Chat Engine (V1)**. Each phase consists of discrete, self-contained tasks formatted as TODO checkboxes. CLI coding agents can pick up tasks sequentially to implement the full specification detailed in [REQUIREMENTS.md](REQUIREMENTS.md).

---

## Phase 1: Project Setup & Environment Setup

- [x] **Task 1.1: Project Directory Structure**
  - Create directory layout: `app/` (core source code), `app/api/`, `app/core/`, `app/db/`, `app/engine/`, `app/models/`, `app/scheduler/`, `tests/`.
  - Add `__init__.py` files across all Python packages.

- [x] **Task 1.2: Dependency & Configuration Management**
  - Create `requirements.txt` or `pyproject.toml` with dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pydantic-settings`, `openai`, `apscheduler`, `pytest`, `httpx`).
  - Create `app/core/config.py` using `pydantic-settings` to manage environment variables (e.g., `DATABASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `LOG_LEVEL`).
  - Create `.env.example` file.

---

## Phase 2: Data Layer & Database Models

- [x] **Task 2.1: Database Engine & Session Setup**
  - Implement `app/db/session.py` setting up SQLite database engine and session factory (`sqlalchemy` async or sync session).

- [x] **Task 2.2: Database Models**
  - Implement `app/models/session.py`: `Session` model (`id` UUID primary key, `system_prompt` text, `created_at`, `updated_at`).
  - Implement `app/models/message.py`: `Message` model (`id` UUID, `session_id` FK, `role` enum (`user`, `assistant`, `system`), `content` text, `timestamp`).
  - Implement `app/models/task.py`: `ScheduledTask` model (`id` UUID, `session_id` FK, `execute_at` timestamp, `status` enum (`pending`, `completed`, `cancelled`)).
  - Implement `app/db/base.py` importing all models for metadata creation.

- [x] **Task 2.3: Database Initialization & CRUD Utilities**
  - Implement `app/db/init_db.py` to create tables on startup.
  - Implement `app/db/crud.py` with helper functions for creating/fetching sessions, creating/fetching messages, creating/updating/fetching pending scheduled tasks.

---

## Phase 3: LLM Interface & Schema Engine

- [ ] **Task 3.1: LLM Action Schemas**
  - Implement `app/engine/schema.py` defining Pydantic models for structured actions:
    - `SpeakAction` (`type="speak"`, `content`)
    - `ScheduleAction` (`type="schedule"`, `content`, `delay_seconds`)
    - `LLMActionResponse` (`actions`: list of actions)

- [ ] **Task 3.2: Context Management & Time Injection**
  - Implement `app/engine/context.py`:
    - Sliding window helper retaining the system prompt and latest $N$ messages fitting token/message limits.
    - System time injector injecting current ISO timestamp and time elapsed since last message (e.g. *"System: It is currently 2:00 PM. The user has not replied in 4 hours."*).

- [ ] **Task 3.3: OpenAI Client Integration**
  - Implement `app/engine/llm.py` wrapping the `openai` SDK.
  - Enforce JSON mode / structured output schema request.
  - Add error handling and fallback parsing for malformed JSON responses.

---

## Phase 4: Core Event Engine & Guardrails

- [ ] **Task 4.1: Guardrails & Safety Rules**
  - Implement `app/engine/guardrails.py`:
    - Recursion check: Count consecutive `assistant` messages since the last `user` message. Abort/raise if count $\ge 3$.
    - Idempotency validation helper for scheduled tasks.

- [ ] **Task 4.2: Event Processor**
  - Implement `app/engine/processor.py` executing the trigger cycle:
    1. Fetch session and message history.
    2. Inject time-awareness into context.
    3. Invoke LLM client for structured actions.
    4. Validate response against guardrails (recursion limit).
    5. Save `speak` actions as `assistant` messages to DB.
    6. Insert `schedule` actions as `ScheduledTask` records with `execute_at = now() + delay_seconds`.

---

## Phase 5: Scheduler & Background Execution Worker

- [ ] **Task 5.1: Background Worker Engine**
  - Implement `app/scheduler/worker.py` using `APScheduler` or Asyncio polling loop checking `ScheduledTask` every 1 second.
  - Enforce idempotency: Mark task status as `completed` atomically *before* invoking the event processor.
  - Trigger event processor for tasks where `status == 'pending'` and `execute_at <= now()`.

---

## Phase 6: FastAPI Application & API Endpoints

- [ ] **Task 6.1: API Routers & Schemas**
  - Implement request/response Pydantic schemas in `app/api/schemas.py`:
    - `SessionCreateRequest`, `SessionResponse`
    - `MessageCreateRequest`, `MessageResponse`
  - Implement `app/api/routes.py`:
    - `POST /sessions` -> Create session.
    - `POST /sessions/{id}/message` -> Post user message & trigger event processor.
    - `GET /sessions/{id}/messages` -> Fetch full message history.

- [ ] **Task 6.2: Main App Assembly & Lifecycle**
  - Implement `app/main.py`:
    - FastAPI app instance with CORS/middleware.
    - Router registration.
    - Lifespan handler starting background scheduler on startup and stopping on shutdown.

---

## Phase 7: Testing & Verification

- [ ] **Task 7.1: Unit & Integration Tests**
  - `tests/test_db.py`: CRUD operations for Session, Message, and ScheduledTask.
  - `tests/test_context.py`: Sliding window truncation & time injection logic.
  - `tests/test_guardrails.py`: Recursion limit (max 3 assistant messages) enforcement.
  - `tests/test_api.py`: FastAPI endpoints testing using `TestClient` or `httpx.AsyncClient`.
  - `tests/test_scheduler.py`: End-to-end test simulating scheduled background double-texting.
