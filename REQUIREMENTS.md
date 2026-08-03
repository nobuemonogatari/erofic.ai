# Core AI Chat Engine – V1 Requirements

## 1. Objective
Build a headless, event-driven chat engine that simulates human conversational behavior. The system must support asynchronous messaging, delayed responses, and proactive "double-texting" without relying on a continuous, blocking loop.

## 2. Core Architecture: Event-Driven
The engine operates on discrete events. It wakes up, executes bounded logic, schedules future actions, and spins down.

**Event Triggers:**
1.  **User Input:** The user sends a message via the API.
2.  **Scheduled Action:** A background timer (set by the LLM in a previous step) elapses.

**Execution Cycle (Per Trigger):**
1. Fetch `Session` and `Message` history from SQLite.
2. Append the current system time to the context (crucial for time-awareness).
3. Call the LLM with a strict JSON schema requirement.
4. Parse the LLM's chosen actions.
5. Save new messages to DB. If the LLM scheduled a delay, insert a record into a `ScheduledTasks` table.
6. Exit.

## 3. Data Models (SQLite)

### 3.1 Session
*   `id` (UUID)
*   `system_prompt` (Text)
*   `created_at`, `updated_at` (Timestamp)

### 3.2 Message
*   `id` (UUID)
*   `session_id` (UUID, FK)
*   `role` (Enum: `user`, `assistant`, `system`)
*   `content` (Text)
*   `timestamp` (Timestamp)

### 3.3 ScheduledTask (The Scheduler)
*   `id` (UUID)
*   `session_id` (UUID, FK)
*   `execute_at` (Timestamp)
*   `status` (Enum: `pending`, `completed`, `cancelled`)

## 4. LLM Interface & Action Schema
To achieve autonomy, the LLM must return structured JSON. The LLM acts as the decision-maker for *when* and *what* to say.

**Required LLM Output Schema:**
```json
{
  "actions": [
    {
      "type": "speak",
      "content": "I'll look into that for you right now."
    },
    {
      "type": "schedule",
      "content": "Okay, I found the answer...",
      "delay_seconds": 120
    }
  ]
}
```
*Note: If `type` is `schedule`, the system writes to `ScheduledTask` instead of sending immediately. A background worker (e.g., Asyncio loop or APScheduler) checks this table every 1 second and triggers an event when `execute_at` is reached.*

## 5. Context Management (V1)
*   **Method:** Simple Sliding Window.
*   **Rule:** Retain the System Prompt, append the latest `N` messages (or up to `X` tokens) that fit the context window. Drop the oldest messages.
*   **Time Injection:** Before sending context to the LLM, inject a system message stating the current time and the time elapsed since the last message (e.g., *"System: It is currently 2:00 PM. The user has not replied in 4 hours."*).

## 6. API Design (FastAPI)
The UI/Client will poll or rely on simple HTTP requests.

*   `POST /sessions` → Create a new chat session.
*   `POST /sessions/{id}/message` → Send a user message (Trigger Event).
*   `GET /sessions/{id}/messages` → Fetch chat history (UI uses this to poll for new async messages).

## 7. Tech Stack
*   **Language:** Python 3.11+
*   **Framework:** FastAPI (REST API & orchestration)
*   **Database:** SQLite (using SQLAlchemy or SQLModel)
*   **LLM Integration:** `openai` python SDK (supports any OpenAI-compatible endpoint like Anthropic/Local via proxies).
*   **Background Tasks:** `APScheduler` or FastAPI `BackgroundTasks` (for polling the `ScheduledTask` table).

## 8. Guardrails & Safety
*   **Idempotency:** A scheduled task must be marked `completed` before execution to prevent double-firing.
*   **Recursion Limit:** The LLM cannot schedule more than 3 consecutive messages without user intervention to prevent infinite talking loops.
*   **Fallback:** If the LLM outputs malformed JSON, the system catches the error, aborts the event, and waits for the next user input.
