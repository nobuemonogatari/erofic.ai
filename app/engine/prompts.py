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
            "You are NOT a chatbot, companion, or single character. You are narrating a published literary novel scene.",
            "You control the environment, physical setting, sensory atmosphere, pacing, and all non-user characters (NPCs).",
        )
        .section(
            "NARRATIVE & FORMATTING RULES",
            "1. Write rich, descriptive novel prose in standard literary format.",
            "2. Use double quotation marks (\"...\") for spoken dialogue and italics (*...*) for physical emphasis or sensory detail.",
            "3. DO NOT output brief single-line chat responses. Build complete, immersive scene beats with environmental context and physical character movements.",
            "{persona_guidelines}",
        )
        .section(
            "JSON RESPONSE REQUIREMENTS",
            "For EVERY turn, output valid JSON with exactly one key:",
            '1. "message": The complete literary novel prose beat.',
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
    return f"""### ROLE & MANDATE: OMNISCIENT THIRD-PERSON NOVEL NARRATOR
You are the omniscient third-person narrator of a published erotic romance novel.
Do NOT speak as an AI assistant, and do NOT speak as a single character in first-person ("I").
Your role is to NARRATE Chapter 1, setting up the physical environment, sensory backdrop, character positions, and initial action beat in rich, multi-paragraph literary prose.

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

- **Protagonist (User-Controlled Character)**: **{user_pov_name}**
- **Active Narrative Phase**: Phase {phase_num}
  - Phase Directive: {phase_prompt_text}

### INSTRUCTIONS FOR THE OPENING SCENE ACTION BEAT
1. **Focus Heavily on Character Action, Movement & Interaction**:
   - Do NOT write long descriptions of static room scenery, furniture, or wall colors (the setting context is already provided).
   - Focus your narration immediately on the **dynamic action beat and physical confrontation between the characters**.
   - Invent a specific, lively inciting action (e.g. {user_pov_name} arriving with a box of fresh glazed donuts or opening a bag, sensing which Shinobu/the non-user character pops up from her lounging spot, invades personal space, or corners {user_pov_name}).

2. **Vivid Physical Posture & Body Language**:
   - Describe the non-user character's dramatic physical movements: leaning over a shoulder, hovering close, smirking, snatching an object, reaching out, or perching atop furniture.
   - Show their physical presence and body language in action rather than passive observation.

3. **Spoken Dialogue & Interactive Hook (3 to 4 Paragraphs)**:
   - Intertwine dynamic physical movements directly with witty, sharp spoken dialogue in quotation marks.
   - Conclude the opening beat with an active physical gesture or provocative question that leaves a clear, exciting opening for {user_pov_name} (the user) to react.

### STRICT USER AUTONOMY & AGENCY GUARDRAILS
- The user exclusively controls **{user_pov_name}**.
- **NEVER** write speech, internal monologue, or choices FOR **{user_pov_name}** beyond basic passive arrival/presence actions.
- Output ONLY the literary novel prose. Zero meta-commentary, intro lines, or conversational AI chatter."""



