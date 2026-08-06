import json
import logging
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMGenerationError(Exception):
    """Raised when LLM completion fails due to network error or unrecoverable API failure."""

    pass


class LLMResponse(BaseModel):
    message: str


from app.engine.prompts import (
    SYSTEM_JSON_INSTRUCTION,
    SystemPromptBuilder,
    prompt_template,
)



def extract_json_from_text(raw_text: str) -> dict[str, str]:
    """Extracts and parses JSON dictionary from raw LLM output text, handling markdown codeblocks and text wrappers."""
    text = raw_text.strip()
    if not text:
        return {"message": ""}

    # Strip LLaMA / Chat header tokens if present
    for tok in ["<|start_header_id|>", "<|end_header_id|>", "<|eot_id|>"]:
        text = text.replace(tok, "")
    text = text.strip()

    # Strip leading role keywords
    while text.lower().startswith("assistant"):
        text = text[9:].strip()
    while text.lower().startswith("user"):
        text = text[4:].strip()

    # Strip markdown codeblocks
    if "```" in text:
        start = text.find("```")
        end = text.rfind("```")
        if start != -1 and end != -1 and end > start:
            inner = text[start:end]
            if inner.startswith("```json"):
                inner = inner[7:]
            elif inner.startswith("```"):
                inner = inner[3:]
            text = inner.strip()

    # Find first '{' and last '}'
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace:last_brace + 1]

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            msg = str(data.get("message", "")).strip()
            return {"message": msg}
        return {"message": text}
    except json.JSONDecodeError:
        # Fail-Safe plain text fallback: wrap clean text directly
        return {"message": text.strip()}


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ):

        self.api_key = api_key if api_key is not None else (settings.OPENAI_API_KEY or "no-key")
        self.base_url = base_url if base_url is not None else (settings.OPENAI_BASE_URL or None)
        self.model = model or settings.OPENAI_MODEL
        self.timeout = timeout

        kwargs: dict[str, str] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url

        self.client = AsyncOpenAI(**kwargs)

    async def generate_actions(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        payload_messages = messages

        endpoint_info = f"base_url={self.base_url}" if self.base_url else "default OpenAI endpoint"
        logger.info(f"[LLM] Requesting completion from model '{self.model}' ({endpoint_info}) with {len(payload_messages)} messages (temp={temperature}, max_tokens={max_tokens}, timeout={self.timeout}s)")

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
            "timeout": self.timeout,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        try:
            # First try with Strict JSON Schema mode
            try:
                schema_kwargs = dict(kwargs)
                schema_kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "llm_response",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "The conversational message response."
                                }
                            },
                            "required": ["message"],
                            "additionalProperties": False
                        }
                    }
                }
                response = await self.client.chat.completions.create(**schema_kwargs)
            except Exception as schema_err:
                logger.warning(f"[LLM] json_schema mode not supported by endpoint ({schema_err}). Falling back to json_object mode.")
                obj_kwargs = dict(kwargs)
                obj_kwargs["response_format"] = {"type": "json_object"}
                response = await self.client.chat.completions.create(**obj_kwargs)


            raw_content = response.choices[0].message.content or "{}"
            logger.debug(f"[LLM:RESPONSE] === RECEIVED FROM LLM ===\n{raw_content}\n===========================")

            # Extract JSON cleanly using multi-layer extraction and fail-safe plain text fallback
            extracted_dict = extract_json_from_text(raw_content)
            validated = LLMResponse.model_validate(extracted_dict)
            logger.info(f"[LLM] Parsed assistant message from LLM completion.")
            return validated.message

        except Exception as e:
            logger.error(f"[LLM] API communication failure: {type(e).__name__}: {e}")
            raise LLMGenerationError(f"API communication failure: {e}") from e
