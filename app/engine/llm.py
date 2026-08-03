import json
import logging
from openai import AsyncOpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.engine.schema import LLMActionResponse

logger = logging.getLogger(__name__)


SYSTEM_JSON_INSTRUCTION = (
    "You must respond with valid JSON matching the following schema:\n"
    "{\n"
    '  "actions": [\n'
    '    {"type": "speak", "content": "<text>"},\n'
    '    {"type": "schedule", "content": "<text>", "delay_seconds": <int>}\n'
    "  ]\n"
    "}\n"
    "You can return multiple actions or an empty list of actions."
)


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def generate_actions(
        self, messages: list[dict[str, str]]
    ) -> LLMActionResponse:
        if not self.client:
            logger.warning("OpenAI API key not configured. Returning empty actions.")
            return LLMActionResponse(actions=[])

        payload_messages = [
            {"role": "system", "content": SYSTEM_JSON_INSTRUCTION}
        ] + messages

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=payload_messages, # type: ignore
                response_format={"type": "json_object"},
                temperature=0.7,
            )

            raw_content = response.choices[0].message.content or "{}"
            parsed_json = json.loads(raw_content)

            return LLMActionResponse.model_validate(parsed_json)

        except (ValidationError, json.JSONDecodeError) as e:
            logger.error(f"Malformed LLM JSON output encountered: {e}")
            return LLMActionResponse(actions=[])
        except Exception as e:
            logger.error(f"Error communicating with LLM API: {e}")
            return LLMActionResponse(actions=[])
