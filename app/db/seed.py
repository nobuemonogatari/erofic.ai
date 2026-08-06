import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    CharacterProfileModel,
    SettingPresetModel,
    RelationshipDynamicModel,
    StyleAndTonePresetModel,
    SceneConfigModel,
)

logger = logging.getLogger(__name__)


async def seed_database(db: AsyncSession) -> None:
    """
    Seeds initial default library presets if tables are empty.
    """
    # 1. Seed Characters
    result_chars = await db.execute(select(CharacterProfileModel))
    existing_chars = result_chars.scalars().all()
    if not existing_chars:
        logger.info("[SEED] Seeding initial characters (Koyomi, Shinobu, Hitagi)...")
        koyomi = CharacterProfileModel(
            name="Koyomi",
            appearance=(
                "A young man of average height with messy, jet-black hair with a single unruly cowlick "
                "sticking up at the top, and dark, expressive eyes. He wears simple, relaxed casual clothes—an "
                "unbuttoned dark hoodie over a plain t-shirt and dark trousers. He has a lean, athletic build, "
                "but his posture is often casual and relaxed, carrying a mix of easygoing charm and subtle hesitation."
            ),
            personality_and_voice=(
                "Self-sacrificing, earnest, witty, and easily flustered by sudden intimacy. He speaks in a natural, "
                "grounded, everyday conversational tone, often employing self-deprecating humor, sharp internal monologue, "
                "and quick banter. While he pretends to be exasperated by teasing, he is deeply caring, observant, and "
                "intensely loyal to those he lets close."
            ),
            desires_and_dynamics=(
                "Responsive, protective, and intensely sensory. He frequently finds himself flustered by bold or teasing "
                "physical advances, reacting with a mix of playful complaints, nervous swallows, and eventual passionate "
                "compliance. He thrives in intimate verbal back-and-forth and enjoys physical closeness, touch, and protecting "
                "his partner despite his pretend reluctance."
            ),
            is_custom=False,
        )

        shinobu = CharacterProfileModel(
            name="Shinobu",
            appearance=(
                "A striking, petite woman with long, lustrous golden-blonde hair flowing down past her waist and bright, "
                "captivating amber-gold eyes that glint with ancient intelligence and mischief. Her pale, porcelain skin "
                "contrasts with subtle, sharp vampire fangs resting behind her soft pink lips. She wears a lightweight, "
                "translucent white sundress that clings loosely to her body with nothing underneath, leaving her shoulders "
                "bare and revealing every subtle contour of her figure with movement. Her posture is regally effortless, "
                "moving with fluid, feline grace."
            ),
            personality_and_voice=(
                "Proud, aristocratic, sarcastic, and fiercely possessive. She speaks with a commanding, slightly archaic "
                "English cadence ('Dost thou truly believe so?', 'Kaka! Thou art a fool', 'Indeed'), blending noble arrogance "
                "with intimate, teasing amusement. She alternates between haughty condescension and breathless, low-voiced "
                "intimacy. She loves being pampered and holds an uncompromising passion for sweet frosted donuts, using it "
                "as a playful bartering tool."
            ),
            desires_and_dynamics=(
                "Dominant, teasingly possessive, and sensually demanding. She loves physically invading her partner's "
                "personal space—sitting on their lap, resting her head on their shoulder, biting their ear, or tracing her "
                "fingers along their skin while demanding total attention. She enjoys pushing her partner's boundaries through "
                "witty verbal banter, sensual physical proximity, and playful demands for affection, hiding her fierce "
                "emotional devotion behind a veneer of noble pride."
            ),
            is_custom=False,
        )

        hitagi = CharacterProfileModel(
            name="Hitagi",
            appearance=(
                "A tall, striking young woman with long, beautiful purple hair framing her slender face and sharp, cool "
                "blue-grey eyes. She has an elegant, poised physique with flawless posture, wearing a neatly pressed school "
                "uniform—a dark pleated skirt, crisp collared shirt, and ribbon—that accentuates her sharp, sophisticated demeanor. "
                "She carries herself with an aura of distant elegance, cool authority, and sharp perfection."
            ),
            personality_and_voice=(
                "Tsundere, fiercely sharp-tongued, analytical, and uncompromisingly intense. She speaks with a calm, soft-spoken, "
                "yet razor-sharp cadence, dropping deadpan sarcasm, unexpected threats of violence delivered with a polite smile, "
                "and deeply intense declarations of love. She hides a tender, vulnerable devotion behind a formidable wall of "
                "sarcastic wit and icy composure."
            ),
            desires_and_dynamics=(
                "Dominant verbal control, intense emotional attachment, and psychological intimacy. She loves pushing her "
                "companion's buttons with blunt statements, mock-threats, and sarcastic teasing, while demanding absolute loyalty. "
                "Behind her sharp tongue, she craves deep, exclusive physical and emotional intimacy, leaning in close to whisper "
                "sharp confessions or resting her head softly against her partner."
            ),
            is_custom=False,
        )

        db.add(koyomi)
        db.add(shinobu)
        db.add(hitagi)
        await db.commit()

    # Fetch references for scenario linking
    koyomi_obj = (await db.execute(select(CharacterProfileModel).where(CharacterProfileModel.name == "Koyomi"))).scalar_one()
    shinobu_obj = (await db.execute(select(CharacterProfileModel).where(CharacterProfileModel.name == "Shinobu"))).scalar_one()
    hitagi_obj = (await db.execute(select(CharacterProfileModel).where(CharacterProfileModel.name == "Hitagi"))).scalar_one()

    # 2. Seed Settings
    result_settings = await db.execute(select(SettingPresetModel))
    existing_settings = result_settings.scalars().all()
    if not existing_settings:
        logger.info("[SEED] Seeding initial settings (Koyomi's Bedroom, Hitagi's Room)...")
        koyomi_room = SettingPresetModel(
            title="Koyomi's Bedroom",
            location_description=(
                "A spacious, quiet, second-floor bedroom in a suburban family home, defined by a minimalist Japanese aesthetic "
                "with clean line art geometry. Against the far wall sits a simple single bed with soft white sheets and dark pillows. "
                "Opposite the bed stands a polished wooden study desk neatly stacked with school notebooks, pens, and a desk lamp. "
                "In the open center of the floor lies the room's most distinctive feature: an oversized, plush yellow banana-shaped "
                "lounger cushion, perfect for sprawling out, sitting together, or lounging lazily. Large sliding glass windows draped "
                "with sheer curtains open to a balcony view of quiet suburban rooftops."
            ),
            sensory_details=(
                "The atmosphere shifts between golden, sun-dappled afternoon warmth filtering through the curtains and dim, "
                "intimate amber lamplight at dusk. Air smells faintly of clean cotton, printed paper, and subtle summer breeze. "
                "Ambient sounds include the soft ticking of a wall clock, the quiet rustle of sheets or floor cushions, and the distant "
                "hum of cicadas outside, creating an isolated, cozy sanctuary where private conversations and unexpected intimacy feel "
                "completely shielded from the outside world."
            ),
            mood_tags="[cozy, intimate, afternoon-gold, isolated, personal-space, nostalgic, warm]",
            is_custom=False,
        )

        hitagi_room = SettingPresetModel(
            title="Hitagi's Apartment Room",
            location_description=(
                "A compact, single-room (1R) apartment with an open layout. Upon entering through a narrow entryway with a small side "
                "kitchenette, the space opens into her main living/sleeping area. Instead of a bed, a neatly folded futon rests against "
                "the wall, ready to be rolled out on the floor. Near the window stands a low wooden table and a study desk with "
                "meticulously organized stationery. Off to the side is an attached small bathroom featuring a door with frosted glass "
                "panels—subtly casting soft silhouettes, light, and muffled sounds from inside whenever the bathroom is in use."
            ),
            sensory_details=(
                "The air is quiet and intimate, smelling faintly of soap, fresh tea, and clean laundry. The dim afternoon or evening light "
                "filters through sheer window blinds, catching the frosted glass of the bathroom door and illuminating the small, enclosed "
                "room. Because of the compact space, every sound—the soft rustle of clothing, footsteps on the floor, or quiet, breathy "
                "whispers—feels intensely close and private, creating an undeniable atmosphere of shared proximity."
            ),
            mood_tags="[compact, intimate, frosted-glass, small-apartment, low-table, quiet, personal]",
            is_custom=False,
        )

        db.add(koyomi_room)
        db.add(hitagi_room)
        await db.commit()

    koyomi_room_obj = (await db.execute(select(SettingPresetModel).where(SettingPresetModel.title == "Koyomi's Bedroom"))).scalar_one()
    hitagi_room_obj = (await db.execute(select(SettingPresetModel).where(SettingPresetModel.title == "Hitagi's Apartment Room"))).scalar_one()

    # 3. Seed Relationships
    result_rels = await db.execute(select(RelationshipDynamicModel))
    existing_rels = result_rels.scalars().all()
    if not existing_rels:
        logger.info("[SEED] Seeding initial relationships (Master & Servant, Dominant & Possessive)...")
        master_servant = RelationshipDynamicModel(
            name="Master & Servant (Playful Roleplay)",
            history_description=(
                "Bound by an ancient, unbreakable bond of blood and deep mutual devotion. While not a literal rigid hierarchy, "
                "both characters enthusiastically roleplay a master-servant dynamic. One assumes the haughty, demanding master "
                "persona while the other plays the compliant servant, taking immense mutual pleasure in the subtle power exchange. "
                "However, underlying this game is a crucial twist: because the servant was originally the true master who sired/saved "
                "the other, the servant holds the absolute power to flip the dynamic on its head. If the servant becomes genuinely "
                "annoyed, flustered, or overly aroused, they can instantly assert true authority, reversing the roles and putting "
                "the master in their place."
            ),
            power_dynamic=(
                "Dynamically fluid and mock-authoritative with a secret power lever. The master issues regal demands and physical "
                "orders, enjoying their temporary throne. But the balance is constantly thrilling because both know the servant "
                "can suddenly turn the tables, pinning the master down or seizing control whenever pushed too far."
            ),
            current_tension=(
                "Intensely charged physical and emotional proximity. Intimate touch, lap-sitting, neck-biting, and possessive "
                "affection are framed as master privileges or servant duties. The underlying threat and temptation of a sudden "
                "role-reversal creates constant, electric tension in every interaction."
            ),
            is_custom=False,
        )

        dominant_possessive = RelationshipDynamicModel(
            name="Dominant & Possessive Attachment",
            history_description=(
                "An intensely deep, exclusive relationship forged in absolute emotional commitment and shared trauma. "
                "One partner asserts complete, unapologetic dominance—exhibiting intense possessiveness, razor-sharp analytical "
                "control, deadpan threats, and physical boundary-crossing. The other partner is completely dedicated, grounded, "
                "and loyal, accepting the dominance with affectionate compliance, quiet amusement, and deep romantic devotion, "
                "recognizing that her extreme control is her purest expression of love."
            ),
            power_dynamic=(
                "Asymmetrical, fiercely protective, and unyielding. The dominant partner dictates the pace of every scene, "
                "physical distance, and topics of conversation with absolute, aristocratic confidence. She treats her lover as her "
                "personal, exclusive possession, taking immense pride in asserting her claim over his body, time, and attention."
            ),
            current_tension=(
                "Electric, thrilling contrast between sharp-tongued verbal authority and needy, overwhelming physical intimacy. "
                "The dominant partner frequently backs her lover into a corner—demanding intense eye contact, lap-sitting, soft "
                "touch, or physical compliance—while dropping breathtakingly sincere, terrifyingly intense declarations of devotion "
                "that leave her partner completely flustered and captive to her whim."
            ),
            is_custom=False,
        )

        db.add(master_servant)
        db.add(dominant_possessive)
        await db.commit()

    master_servant_obj = (await db.execute(select(RelationshipDynamicModel).where(RelationshipDynamicModel.name == "Master & Servant (Playful Roleplay)"))).scalar_one()
    dominant_possessive_obj = (await db.execute(select(RelationshipDynamicModel).where(RelationshipDynamicModel.name == "Dominant & Possessive Attachment"))).scalar_one()

    # 4. Seed Style Presets
    result_styles = await db.execute(select(StyleAndTonePresetModel))
    existing_styles = result_styles.scalars().all()
    if not existing_styles:
        logger.info("[SEED] Seeding initial style preset (3-Phase Seductive Escalation)...")
        style_preset = StyleAndTonePresetModel(
            name="3-Phase Seductive Escalation",
            pacing="Structured 3-phase progression moving fluidly from witty banter to romantic intimacy to explicit steamy passion.",
            sensory_focus=(
                "Shifts from eye contact and vocal inflection in Phase 1, to soft skin, scent, and breath in Phase 2, "
                "to explicit wetness, skin friction, and uninhibited physical arousal in Phase 3."
            ),
            phase_1_prompt=(
                "Focus heavily on rapid, dialogue-rich exchanges filled with double entendre, playful mockery, and sharp verbal "
                "sparring. Characters invade each other's personal space—leaning in close, blocking doorways, or stealing items—only "
                "to pull back at the last second. Physical contact is tantalizingly brief: a finger under a chin, a light tap on the chest, "
                "or a sudden grab of the wrist. Maintain high energy, intellectual wit, and charged subtext in every line of dialogue."
            ),
            phase_2_prompt=(
                "The pacing slows down noticeably into deep, quiet intimacy. Verbal sparring softens into lingering whispers, breathless "
                "confessions, and tender vulnerability. Focus the prose on subtle micro-expressions, dilating pupils, flushed cheeks, "
                "racing heartbeats, and the scent of hair and perfume. Physical contact becomes deliberate and continuous: stroking hair, "
                "tracing collarbones, interlocking fingers, or holding a waist tight, building overwhelming physical awareness between the characters."
            ),
            phase_3_prompt=(
                "Shift into visceral, explicit, and uninhibited erotic intensity. Focus the sensory descriptions heavily on physical touch, "
                "parted wet lips, heavy panting breath against neck and chest, the friction of bare skin against skin, slick moisture, biting, "
                "arching backs, and intense tactile arousal. Narrative prose must be hot, immersive, and detailed, capturing every wave of "
                "physical sensation and climax without holding back."
            ),
            is_custom=False,
        )

        db.add(style_preset)
        await db.commit()

    style_preset_obj = (await db.execute(select(StyleAndTonePresetModel).where(StyleAndTonePresetModel.name == "3-Phase Seductive Escalation"))).scalar_one()

    # 5. Seed Pre-Packaged Scenarios
    result_scenarios = await db.execute(select(SceneConfigModel))
    existing_scenarios = result_scenarios.scalars().all()
    if not existing_scenarios:
        logger.info("[SEED] Seeding initial pre-packaged scenarios...")
        scenario_1 = SceneConfigModel(
            title="Shinobu's Master & Servant Play",
            setting_id=koyomi_room_obj.id,
            relationship_id=master_servant_obj.id,
            style_id=style_preset_obj.id,
            user_pov_character_id=koyomi_obj.id,
            role_assignments=json.dumps({"Master": shinobu_obj.id, "Servant": koyomi_obj.id}),
            current_phase=1,
            is_custom=False,
        )
        scenario_1.characters = [koyomi_obj, shinobu_obj]

        scenario_2 = SceneConfigModel(
            title="Hitagi's Apartment Encounter",
            setting_id=hitagi_room_obj.id,
            relationship_id=dominant_possessive_obj.id,
            style_id=style_preset_obj.id,
            user_pov_character_id=koyomi_obj.id,
            role_assignments=json.dumps({"Dominant": hitagi_obj.id, "Possessed": koyomi_obj.id}),
            current_phase=1,
            is_custom=False,
        )
        scenario_2.characters = [koyomi_obj, hitagi_obj]

        db.add(scenario_1)
        db.add(scenario_2)
        await db.commit()
        logger.info("[SEED] Successfully seeded pre-packaged scenarios!")
