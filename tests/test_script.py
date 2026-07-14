from cogni import script

OUTLINE = {
    "title": "Rich Dad Poor Dad",
    "author": "Robert Kiyosaki",
    "thesis": "Financial literacy beats income.",
    "key_ideas": [{"title": "Assets vs liabilities", "summary": "Assets feed you."}],
}


def test_build_prompt_is_cognibot_story():
    p = script._build_prompt(OUTLINE, "an honest angle", 8, 14)
    assert "Cognibot" in p
    assert "character" in p.lower()
    assert "verdict" in p.lower() or "judge" in p.lower()
    assert '"character"' in p  # asks the model to return the character object


def test_validate_character_ok():
    data = {"character": {"name": "Ana", "description": "a tired silhouette in a suit"},
            "scenes": []}
    assert script._validate_character(data) == {
        "name": "Ana", "description": "a tired silhouette in a suit"}


def test_validate_character_missing_is_tolerated():
    assert script._validate_character({"scenes": []}) is None
    assert script._validate_character({"character": {"name": ""}}) is None


def test_validate_scenes_still_works():
    data = {"scenes": [{"narration": "n", "on_screen_text": "o", "image_prompt": "i"}]}
    got = script._validate(data)
    assert got[0] == {"narration": "n", "on_screen_text": "o", "image_prompt": "i"}


def test_structure_prompt_is_cognibot_character_arc():
    p = script._build_structure_prompt(OUTLINE, "angle", 5, 7, 30)
    assert "Cognibot" in p
    assert "protagonist" in p.lower() or "character" in p.lower()
    assert '"character"' in p and '"chapters"' in p


def test_chapter_prompt_threads_character():
    ch = {"title": "The Trap", "focus": "sets up the problem"}
    p = script._build_chapter_prompt(
        OUTLINE, "angle", {"name": "Dana", "description": "nurse in scrubs, seen from behind"},
        ch, 1, 6, [], 10, 14,
    )
    assert "Dana" in p
    assert "scrubs" in p
    assert "beat" in p.lower()
