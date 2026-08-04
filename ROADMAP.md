# Project Roadmap & Implementation Tasks (Updated)

This document outlines the roadmap for the **Core AI Chat Engine**.

---

## Phase 1: Project Setup & Environment Setup

- [x] **Task 1.1: Project Directory Structure**
  - Create directory layout: `app/`, `app/api/`, `app/core/`, `app/db/`, `app/engine/`, `app/models/`, `app/scheduler/`, `tests/`.
  - Add `__init__.py` files across all packages.

- [x] **Task 1.2: Dependency & Configuration Management**
  - Setup configuration management using `pydantic-settings`.

---

## Phase 2: Data Layer & Database Models

- [x] **Task 2.1: Database Engine & Session Setup**
  - Set up SQLite database engine and session factory.

- [x] **Task 2.2: Database Models**
  - Implement `SessionModel` and `MessageModel`.

- [x] **Task 2.3: Database Initialization & CRUD Utilities**
  - Initialize database schemas and implement CRUD helper functions for session/message creation and retrieval.

---

## Phase 3: LLM Interface & Schema Engine

- [x] **Task 3.1: LLM Response Schemas**
  - Define simple `LLMResponse` Pydantic schema class.

- [x] **Task 3.2: Context Management & Delineated Notices**
  - Implement simplified, chronologically ordered sliding window history builder. Appends a trailing event notice with relative time elapsed.

- [x] **Task 3.3: OpenAI Client Integration**
  - Wrap OpenAI SDK using structured JSON mode and error-resilient validations.

---

## Phase 4: Core Event Engine & Guardrails

- [x] **Task 4.1: Guardrails & Safety Rules**
  - Implement recursion limits checking to prevent infinite chatbot loops.

- [x] **Task 4.2: Event Processor**
  - Execute event cycles (user inputs and re-pings), saving the assistant message, and scheduling background re-ping timers.

---

## Phase 5: In-Memory Scheduler

- [x] **Task 5.1: In-Memory TimerManager**
  - Implement `TimerManager` storing `asyncio.TimerHandle` objects per session. Schedules 30s re-pings after successful executions (or 10s retries on failure).

---

## Phase 6: FastAPI Application & API Endpoints

- [x] **Task 6.1: API Routers & Schemas**
  - Implement session and message HTTP entry points.

- [x] **Task 6.2: Main App Lifespan Handler**
  - Register in-memory re-ping callbacks on lifespan startup.

---

## Phase 7: Testing & Verification

- [x] **Task 7.1: Unit & Integration Tests**
  - Verify database operations, context building, guardrails, API integration, locking, and in-memory scheduling.
