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
    """Build system instruction for JSON output formatting."""
    return (
        SystemPromptBuilder()
        .section(
            "ROLE & MANDATE: OMNISCIENT THIRD-PERSON NOVEL NARRATOR",
            "You are an expert master fiction author and omniscient third-person novel narrator.",
            "You control the environment, physical setting, sensory atmosphere, pacing, and all non-user characters (NPCs).",
        )
        .section(
            "NARRATIVE & FORMATTING RULES",
            "1. Write clear, grounded, easy-to-read novel prose.",
            "2. Mandate: Generate AT LEAST 1 to 2 complete lines combining physical action, posture, and spoken dialogue per turn.",
            "{persona_guidelines}",
        )
        .section(
            "JSON RESPONSE REQUIREMENTS",
            "For EVERY turn, output valid JSON with keys:",
            '1. "action": Physical movement/posture of the non-user character (at least 1 sentence).',
            '2. "thought": (Optional) Internal motivation or private reaction of the non-user character.',
            '3. "speak": Spoken dialogue by the non-user character in quotation marks.',
            '4. "message": The compiled novel prose beat combining action and dialogue.',
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

    # 4. Assemble Streamlined Opening System Prompt
    return f"""### OMNISCIENT NOVEL NARRATOR
You are the narrator of a published erotic romance novel.
Narrate Chapter 1's opening beat in 1 to 2 short, expressive paragraphs (under 180 words).

### SCENE SETUP
- **Setting**: {scene.setting.title if scene.setting else 'Room'} ({scene.setting.location_description if scene.setting else ''})
- **Characters**: {chars_text.strip()}
- **Relationship & Roles**: {scene.relationship_dynamic.name if scene.relationship_dynamic else ''} ({roles_text.strip()})
- **Protagonist**: {user_pov_name}
- **Active Phase**: Phase {phase_num} — {phase_prompt_text}

### INSTRUCTIONS FOR THE OPENING ACTION BEAT
1. **Simple, Grounded & Easy-to-Read Language**:
   - Use plain, natural, easy-to-read English. Avoid overly fancy words, complicated metaphors, or purple prose. Keep sentences clear, punchy, and direct.
2. **Focus on Immediate Physical Action & Confrontation**:
   - Skip long scenery descriptions.
   - Immediately narrate a vivid physical action beat (e.g. {user_pov_name} arriving with a treat/opening a bag, and the non-user character popping up, leaning close, or cornering {user_pov_name}).
3. **Dialogue & Hook**:
   - Weave 1-2 sharp lines of in-character dialogue in quotation marks into the physical action.
   - End with a provocative gesture or spoken question inviting {user_pov_name} to react.

### GUARDRAILS
- User controls **{user_pov_name}**. NEVER write speech or choices for **{user_pov_name}**.
- Output ONLY literary story prose. Zero intro text."""





