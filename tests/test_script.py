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


def test_validate_story_ok():
    data = {"story": {
        "protagonist": {"name": "Theo", "description": "tired man in teal", "wound": "watched his dad retire broke"},
        "argument": {"stance": "dangerously-half-right", "claim": "Housel's patience is a luxury good"},
        "wager": {"book_claim_on_trial": "just be patient", "decision": "bet the emergency fund on a tip", "outcome": "book-loses"},
        "plant": "the aquarium trip", "payoff": "his kid ignores the watch",
        "closing_scene": "Theo at the aquarium", "opening_move": "envy", "voice_moves": ["total recall"],
        "acts": [
            {"title": "A", "focus": "f", "role": "cold open", "ideas": [{"idea": "compounding", "mode": "obstacle"}], "carries": "none"},
            {"title": "B", "focus": "g", "role": "final", "ideas": [], "carries": "payoff"},
        ],
    }}
    b = script._validate_story(data["story"])
    assert b["protagonist"]["name"] == "Theo"
    assert b["argument"]["stance"] == "dangerously-half-right"
    assert b["acts"][1]["carries"] == "payoff"


def test_validate_story_defaults_optionals():
    b = script._validate_story({
        "protagonist": {"name": "X", "description": "d"},
        "argument": {"claim": "c"},
        "acts": [{"title": "1"}, {"title": "2"}],
    })
    assert b["protagonist"]["wound"] == ""
    assert b["voice_moves"] == []
    assert b["acts"][0]["carries"] == "none" and b["acts"][0]["ideas"] == []


def test_validate_story_rejects_missing_argument_and_thin_acts():
    import pytest
    with pytest.raises(RuntimeError):
        script._validate_story({"protagonist": {"name": "X", "description": "d"}, "acts": [{"title": "1"}, {"title": "2"}]})
    with pytest.raises(RuntimeError):
        script._validate_story({"protagonist": {"name": "X", "description": "d"}, "argument": {"claim": "c"}, "acts": [{"title": "1"}]})


def test_shapes_from_docs_collects_and_dedupes():
    docs = [
        {"story": {"argument": {"stance": "mostly-right"}, "opening_move": "envy",
                   "wager": {"book_claim_on_trial": "just be patient"}}},
        {"story": {"argument": {"stance": "mostly-right"}, "opening_move": "crisis",
                   "wager": {"book_claim_on_trial": "cut the lattes"}}},
        {"scenes": []},  # old book, no story — tolerated
    ]
    s = script._shapes_from_docs(docs)
    assert s["stances"] == ["mostly-right"]                 # deduped
    assert set(s["openings"]) == {"crisis", "envy"}
    assert "just be patient" in s["wagers"]


def test_architect_prompt_demands_bible():
    p = script._build_architect_prompt(
        OUTLINE, "angle", 5, 7, 30,
        {"stances": ["mostly-right"], "openings": ["envy"], "wagers": ["just be patient"]},
    )
    assert "Cognibot" in p
    for key in ('"argument"', '"wager"', '"plant"', '"payoff"', '"closing_scene"', '"acts"', '"wound"'):
        assert key in p, key
    assert "test" in p.lower() and "illustrat" in p.lower()      # test, don't illustrate
    assert "mostly-right" in p and "envy" in p                    # variety: prior shapes fed in
    assert "lose" in p.lower()                                    # the book can lose the wager
