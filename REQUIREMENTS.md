# Core AI Chat Engine – V1 Requirements

## 1. Objective
Build a headless, event-driven chat engine that simulates human conversational behavior. The system supports event triggers, time-aware context management, multiple sequential messages, and structured LLM actions without relying on a continuous, blocking loop.

## 2. Core Architecture: Event-Driven
The engine operates on discrete events. It wakes up, executes bounded logic, and spins down.

**Event Triggers:**
1.  **User Input:** The user sends a message via the API.
2.  **Scheduled Trigger:** A background event/timer elapses.

**Execution Cycle (Per Trigger):**
1. Fetch `Session` and `Message` history from SQLite.
2. Auto-cancel any existing pending timers for the session.
3. Append the current system time and time elapsed context.
4. Call the LLM with a strict JSON schema requirement.
5. Parse the LLM's chosen actions (`speak` and/or `set_timer`).
6. Save new messages and set new timer if requested.
7. Exit.

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
To achieve autonomy, the LLM returns structured JSON containing chosen actions (`speak` and `set_timer`).

**Required LLM Output Schema:**
```json
{
  "actions": [
    {
      "type": "speak",
      "content": "First short text message."
    },
    {
      "type": "speak",
      "content": "Second follow-up text message."
    },
    {
      "type": "set_timer",
      "delay_seconds": 30
    }
  ]
}
```
*Notes:*
- **Multiple `speak` actions**: Supported in a single turn so the assistant can send multiple short, natural text messages in sequence.
- **`set_timer` action**: Schedules an engine wake-up event. `delay_seconds` must be between **10 and 60 seconds**.

## 5. Context Management (V1)
*   **Method:** Simple Sliding Window.
*   **Rule:** Retain the System Prompt, append the latest `N` messages (up to 20 messages) fitting the context window.
*   **Time Injection:** Before sending context to the LLM, inject a system message stating the current time and the time elapsed since the last message (e.g., *"System: It is currently 2:00 PM. The user has not replied in 4 hours."*).

## 6. API Design (FastAPI)
*   `POST /sessions` → Create a new chat session.
*   `GET /sessions` → Fetch all chat sessions.
*   `POST /sessions/{id}/message` → Save user message immediately and dispatch event processor asynchronously in background (non-blocking).
*   `GET /sessions/{id}/messages` → Fetch chat history (UI polls for new assistant messages).

## 7. Tech Stack
*   **Language:** Python 3.11+
*   **Framework:** FastAPI (REST API & orchestration)
*   **Database:** SQLite (using SQLAlchemy Async + `aiosqlite`)
*   **LLM Integration:** `openai` python SDK (supports OpenAI, Ollama, and any OpenAI-compatible endpoint).
*   **Background Tasks:** Async background worker.

## 8. Guardrails & Safety
*   **Default 60s Wake-Up Fallback**: If the LLM completes a turn without calling `set_timer`, the engine automatically schedules a default 60-second wake-up timer (`DEFAULT_WAKEUP_TIMER_SECONDS = 60`).
*   **Single Pending Timer Invariant**: At any time, at most 1 pending timer can exist per session.
*   **Timer Auto-Cancellation**: Any existing pending timer for a session is automatically marked `cancelled` whenever a new event occurs or a new timer is set.
*   **Idempotency**: Tasks must be marked `completed` before execution to prevent double-firing.
*   **Recursion Limit**: The assistant cannot send more than 3 consecutive messages without user intervention to prevent infinite loops.
*   **Fallback & Tag Sanitization**: If the LLM outputs malformed JSON or includes XML/HTML tags in content, the system safely sanitizes or catches the error and waits for the next user input.
