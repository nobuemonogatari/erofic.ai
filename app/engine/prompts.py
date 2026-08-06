import inspect
import logging
from typing import Any
from app.models.scene import SceneConfigModel

logger = logging.getLogger(__name__)


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
    """Utility helper to clean up multi-line triple-quoted prompt strings and optional formatting."""
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


def build_opening_scene_system_prompt(scene: SceneConfigModel) -> str:
    """
    Compiles the Master Opening System Prompt for a SceneConfig to generate Chapter 1's Opening Beat.
    """
    # 1. Format Characters Present
    chars_text = ""
    if scene.characters:
        for c in scene.characters:
            chars_text += (
                f"- **{c.name}**:\n"
                f"  - Appearance: {c.appearance}\n"
                f"  - Personality & Voice: {c.personality_and_voice}\n"
                f"  - Desires & Dynamics: {c.desires_and_dynamics}\n"
            )
    else:
        chars_text = "- Unspecified characters\n"

    # 2. Format Role Assignments
    roles_text = ""
    roles_dict = scene.role_assignments_dict if hasattr(scene, "role_assignments_dict") else {}
    if roles_dict:
        for role, char_id in roles_dict.items():
            matched = next((c for c in (scene.characters or []) if c.id == char_id), None)
            char_name = matched.name if matched else char_id
            roles_text += f"- **{role}**: {char_name}\n"
    else:
        roles_text = "- None assigned\n"

    # 3. Determine Active Phase Style Directive
    style_obj = scene.style
    phase_num = scene.current_phase or 1
    phase_prompt_text = ""
    if style_obj:
        if phase_num == 1:
            phase_prompt_text = style_obj.phase_1_prompt or style_obj.pacing
        elif phase_num == 2:
            phase_prompt_text = style_obj.phase_2_prompt or style_obj.pacing
        elif phase_num == 3:
            phase_prompt_text = style_obj.phase_3_prompt or style_obj.pacing
        else:
            phase_prompt_text = style_obj.phase_1_prompt or style_obj.pacing

    user_pov_name = scene.user_pov_character.name if scene.user_pov_character else "Protagonist"

    # 4. Assemble Master Opening System Prompt
    return f"""You are an expert master fiction author opening Chapter 1 of an immersive, dialogue-heavy novel scene.

### SCENE CONFIGURATION
- **Primary Setting**: {scene.setting.title if scene.setting else 'Default Room'}
  - Location Details: {scene.setting.location_description if scene.setting else ''}
  - Sensory Backdrop: {scene.setting.sensory_details if scene.setting else ''}
  - Mood Tags: {scene.setting.mood_tags if scene.setting else ''}

- **Characters Present**:
{chars_text}

- **Relationship Dynamic**: {scene.relationship_dynamic.name if scene.relationship_dynamic else 'Unspecified'}
  - History & Background: {scene.relationship_dynamic.history_description if scene.relationship_dynamic else ''}
  - Power Dynamic: {scene.relationship_dynamic.power_dynamic if scene.relationship_dynamic else ''}
  - Current Tension: {scene.relationship_dynamic.current_tension if scene.relationship_dynamic else ''}

- **Role Assignments**:
{roles_text}

- **Active User POV Character**: **{user_pov_name}**
- **Active Narrative Phase**: Phase {phase_num}
  - Phase Directive: {phase_prompt_text}

### INSTRUCTIONS FOR THE OPENING SCENE BEAT
1. **Third-Person Descriptive Novel Perspective**:
   - Write from a atmospheric third-person novel perspective (referring to the protagonist by name as **{user_pov_name}**).
   - Set up a substantial, evocative opening scene beat (3 to 5 full paragraphs). Do NOT output just a single line of dialogue.

2. **Establish Environment, Physical Actions & Arrival**:
   - Describe the physical space of the room, lighting, sensory details, and initial movements of the characters in the scene.
   - Invent a natural, compelling starting situation or action beat (e.g., {user_pov_name} returning home, setting down bags, or entering the quiet room).
   - Show how the non-user character (e.g. Shinobu, Hitagi) physically makes their entrance or reacts to {user_pov_name}'s presence—their posture, body language, facial expression, clothing, and initial movement.

3. **Dialogue & Hook**:
   - Intertwine vivid physical actions and environmental details with expressive, in-character spoken dialogue.
   - Conclude the opening beat with an active moment, question, or provocative action that leaves a clear opening for the user to respond.

### STRICT USER AUTONOMY GUARDRAILS
- The user plays as **{user_pov_name}**.
- **NEVER** write internal monologue, decisions, or speech FOR **{user_pov_name}** beyond basic passive arrival/presence actions.
- Output ONLY the literary novel prose text. Do NOT include meta-introductions ("Here is the scene setting:") or conversational AI chatter."""

