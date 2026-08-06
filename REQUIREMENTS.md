# Erotica Fiction Engine – Functional Requirements

## 1. Core Vision & User Experience
* **Book-like Immersion**: The system must feel like reading a dialogue-heavy fiction book rather than interacting with a standard AI assistant chat.
* **Initial Genre Focus**: Erotic romance / Erotica fiction (emphasizing physical and emotional tension, intimate pacing, sensory depth, atmospheric descriptions, and seductive/witty banter).
* **High-Capacity Context Support**: Designed to leverage larger context windows (e.g. 16k tokens) to maintain rich character depth, narrative guidelines, active scene setup, and deep story memory.

---

## 2. Story Initialization & Reusable Scene Components
Before a story scene begins, the user goes through an **Initialization Phase** or selects a pre-configured setup. The setup is built from modular, reusable components:

### 2.1 Character Profiles
* Defines individual characters participating in the scene (appearance, personality, vocal style, speech patterns, desires, and behaviors).
* Supports 2 characters initially, with design flexibility for solo or multi-character scenes in the future.

### 2.2 Relationship Dynamics
* Defines the relationship history, balance of power, and emotional/physical tension between the characters.

### 2.3 Setting & Environment
* Defines the scene location, sensory backdrop (lighting, temperature, scents, ambient sounds), and overall atmosphere.

### 2.4 Style & Tone Presets
* Defines the literary flavor, ratio of dialogue to descriptive prose, pacing, and sensory focus (e.g., slow burn, witty banter, intense passion).

### 2.5 Active Scene Configuration
* Combines selected characters, relationship dynamic, setting, and style preset into an active story session.
* Specifies which character the user is playing as the default first-person perspective.

---

## 3. Pre-Loaded Library & Custom Preset Persistence
* **Pre-Loaded Scenarios & Presets**: Ships with a library of curated characters, settings, relationships, style presets, and ready-to-play full scene templates for instant selection.
* **Automatic Custom Recording**: Any custom character, setting, or relationship details created by the user during setup are automatically saved to their library for reuse in future scenes.

---

## 4. Perspective & Character System
* **Default Perspective**: First-Person ("I"). The user acts as their selected main character by default.
* **Dynamic Character Switching**:
  * Users can switch their active POV character on the fly during a scene (e.g., switching from the main character to a partner character, or back).
  * The system adjusts narrative handling so that "I" in user inputs aligns with the currently active character.

---

## 5. Structured Input Types & Slash Commands
* Users can explicitly tag their input mode using simple UI commands or slash shortcuts:
  * **Dialogue**: Spoken words meant to be uttered aloud.
  * **Action**: Physical movements, gestures, or interactions.
  * **Thought / Monologue**: Internal unspoken thoughts of the character.
  * **Scene Setting**: Contextual descriptions of the surroundings, mood, or time shift.
  * **World Event**: External environmental or plot events.
* The system accepts raw user dialogue seamlessly without requiring full prose wrappers.

---

## 6. LLM Narrative & System Prompt Expectations
* **Dialogue-Heavy Literary Prose**: Generates rich, evocative dialogue interwoven with sensory details, vocal beats, and body language.
* **Standard Novel Formatting**: Uses proper quotation marks for spoken dialogue, italics for internal thoughts/emphasis, and natural paragraph breaks.
* **Zero AI Assistant Bleed**: Completely eliminates AI helper tropes ("As an AI...", "How can I help?", meta-summaries, out-of-character comments).
* **Contextual Responsiveness**: Correctly interprets user input categories and character perspective to produce aligned narrative responses.
