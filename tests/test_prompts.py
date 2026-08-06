from app.engine.prompts import SystemPromptBuilder, build_system_json_instruction, SYSTEM_JSON_INSTRUCTION


def test_system_prompt_builder():
    builder = SystemPromptBuilder("Test Title")
    builder.section("Rules", "- Rule 1", "- Rule 2")
    builder.section("Persona", "Role: {role}")

    res = builder.build(role="Assistant")

    expected = (
        "=== TEST TITLE ===\n\n"
        "RULES:\n"
        "- Rule 1\n"
        "- Rule 2\n\n"
        "PERSONA:\n"
        "Role: Assistant"
    )
    assert res == expected


def test_system_json_instruction_formatting():
    formatted = SYSTEM_JSON_INSTRUCTION.format(persona_guidelines="3. Custom persona")
    assert "SPEAKER IDENTIFICATION & DIALOGUE RULES:" in formatted
    assert "CONVERSATION & DIALOGUE GUIDELINES:" in formatted
    assert "3. Custom persona" in formatted
    assert "JSON RESPONSE REQUIREMENTS:" in formatted
