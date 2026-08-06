import inspect
import re
from typing import Any, Callable


class SystemPromptBuilder:
    """A clean, fluent builder for constructing structured system prompts.
    
    Supports:
    - Multi-line clean triple-quote raw strings (auto dedented/trimmed)
    - Structured sections with titles and line bullet points
    - Template variable interpolation via format() or build(key=val)
    """

    def __init__(self, title: str | None = None):
        self._title = title
        self._sections: list[tuple[str, list[str]]] = []

    def section(self, header: str, *lines: str) -> "SystemPromptBuilder":
        """Add a section with a header title and one or more line items or text blocks."""
        cleaned_lines = [line.rstrip() for line in lines if line is not None]
        self._sections.append((header.strip(), cleaned_lines))
        return self

    def add_line(self, header: str, line: str) -> "SystemPromptBuilder":
        """Add a single line to an existing section, or create the section if it doesn't exist."""
        for h, lines in self._sections:
            if h == header.strip():
                lines.append(line.rstrip())
                return self
        return self.section(header, line)

    def raw_block(self, text: str) -> "SystemPromptBuilder":
        """Add a raw multi-line text block, auto-dedented."""
        dedented = inspect.cleandoc(text).strip()
        self._sections.append(("", [dedented]))
        return self

    def build(self, **kwargs: Any) -> str:
        """Render the complete prompt string formatted with optional keyword arguments."""
        blocks: list[str] = []

        if self._title:
            blocks.append(f"=== {self._title.upper()} ===")

        for header, lines in self._sections:
            content = "\n".join(lines)
            if header:
                blocks.append(f"{header.upper()}:\n{content}")
            else:
                blocks.append(content)

        raw_prompt = "\n\n".join(blocks)
        if kwargs:
            return raw_prompt.format(**kwargs)
        return raw_prompt


def prompt_template(text: str, **kwargs: Any) -> str:
    """Utility helper to clean up multi-line triple-quoted prompt strings and optional formatting.
    
    Automatically strips common leading indentation while preserving inner layout.
    """
    cleaned = inspect.cleandoc(text).strip()
    if kwargs:
        return cleaned.format(**kwargs)
    return cleaned


def build_system_json_instruction() -> str:
    """Build default system instruction for JSON output response formatting using SystemPromptBuilder."""
    return (
        SystemPromptBuilder()
        .section(
            "SPEAKER IDENTIFICATION & DIALOGUE RULES",
            "- Messages with role 'user' are spoken by the HUMAN USER.",
            "- Messages with role 'assistant' are spoken by YOU (the assistant).",
            "- Messages with role 'system' are environment or timer notifications.",
            "- CRITICAL RULE: NEVER reply to or answer your own previous 'assistant' messages. Only respond to the latest 'user' input or system context.",
        )
        .section(
            "CONVERSATION & DIALOGUE GUIDELINES",
            "1. Speak naturally, expressively, and engagingly like a real human.",
            "2. DO NOT spam messages. Never repeat your previous questions or rephrase them in slightly different words.",
            "{persona_guidelines}",
        )
        .section(
            "JSON RESPONSE REQUIREMENTS",
            "For EVERY single turn, you MUST output valid JSON with exactly one key:",
            '1. "message": The conversational message you want to send right now. Do not prefix your message with roles or headers (e.g. do NOT write \'assistant: hello\').',
        )
        .section(
            "EXAMPLES",
            "Example 1:\n{{\n  \"message\": \"Yes, master... how may I serve you right now?\"\n}}\n",
            "Example 2:\n{{\n  \"message\": \"I have finished cleaning your room, master. Shall I prepare some tea for you now?\"\n}}\n",
            "Example 3:\n{{\n  \"message\": \"Welcome back, master! I was waiting for you to return.\"\n}}",
        )
        .build()
    )


# Default JSON system instruction string for backwards-compatibility
SYSTEM_JSON_INSTRUCTION = build_system_json_instruction()
