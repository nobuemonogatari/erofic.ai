# Core AI Chat Engine – V1 Requirements (Updated)

## 1. Objective
Build a headless, event-driven chat engine that simulates human conversational behavior. The system supports event triggers, relative time-aware context management, multiple sequential messages, and structured LLM responses without relying on a persistent, database-backed background loop.

## 2. Core Architecture: Event-Driven
The engine operates on discrete events. It wakes up, executes bounded logic, and spins down.

**Event Triggers:**
1.  **User Input:** The user sends a message via the API.
2.  **Autonomous Re-Ping:** An in-memory timer elapses (30 seconds of user silence).

**Execution Cycle (Per Trigger):**
1. Fetch `Session` and `Message` history from SQLite.
2. Cancel any pending in-memory re-ping timers for the session.
3. Append time elapsed context.
4. Call the LLM with a strict JSON schema requirement.
5. Parse the LLM's chosen actions (`speak` actions).
6. Save new messages and schedule a new 30-second re-ping timer.
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

## 4. LLM Interface & Action Schema
To achieve autonomy, the LLM returns structured JSON containing chosen `speak` actions.

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
    }
  ]
}
```
*Notes:*
- **Multiple `speak` actions**: Supported in a single turn so the assistant can send multiple short, natural text messages in sequence.
- **Silence (No speak)**: If the LLM has nothing to say, it can respond with an empty actions array `{"actions": []}`.

## 5. Context Management (V1)
*   **Method:** Simple Sliding Window.
*   **Rule:** Retain the System Prompt and JSON format rules at index 0, and append the latest messages (up to 20 messages).
*   **Time & Event Context:** Inject a system message at the very end of the payload list stating the trigger type and time elapsed since the last message (e.g. *"SYSTEM EVENT [AUTONOMOUS_RE_PING]: 30 seconds have elapsed since your last action. The user has not replied."*).

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
*   **Scheduling**: In-memory `asyncio` Timer Handles.

## 8. Guardrails & Safety
*   **Default 30s Wake-Up**: The engine automatically schedules a 30-second re-ping timer after every execution cycle.
*   **Single Timer Invariant**: At any time, at most 1 in-memory timer exists per session.
*   **Timer Auto-Cancellation**: Any existing timer for a session is automatically cancelled whenever a new event triggers.
*   **Recursion Limit**: The assistant cannot send more than 3 consecutive messages without user intervention to prevent infinite loops.
*   **Fallback & Tag Sanitization**: If the LLM outputs malformed JSON or includes XML/HTML tags in content, the system safely sanitizes or catches the error and schedules a 10s recovery retry timer.
