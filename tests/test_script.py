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


def test_validate_story_ok():
    data = {"story": {
        "hook_puzzles": ["why do you check your phone first", "why is your Sunday flat"],
        "promise": "you'll see which sentence in this book is the dangerous one",
        "author_story": "Frankl wrote it in nine days",
        "recurring_figure": {"name": "Viktor Frankl", "description": "50s, pale, grey side-parted hair"},
        "argument": {"stance": "dangerously-half-right", "claim": "the famous line curdles"},
        "where_the_book_is_wrong": "he never saw the replication work",
        "closing_image": "a book face-down on a windowsill", "voice_moves": ["total recall"],
        "acts": [
            {"title": "A", "focus": "f", "role": "cold open",
             "ideas": [{"idea": "the will to meaning", "anchor": "16 million copies"}], "carries": "hook"},
            {"title": "B", "focus": "g", "role": "final", "ideas": [], "carries": "verdict"},
        ],
    }}
    b = script._validate_story(data["story"])
    assert b["recurring_figure"]["name"] == "Viktor Frankl"
    assert b["argument"]["stance"] == "dangerously-half-right"
    assert b["acts"][0]["carries"] == "hook" and b["acts"][1]["carries"] == "verdict"
    assert b["acts"][0]["ideas"][0]["anchor"] == "16 million copies"


def test_validate_story_defaults_optionals():
    b = script._validate_story(_bible_min())
    assert b["voice_moves"] == []
    assert b["recurring_figure"] is None          # no figure is a legitimate shape
    assert b["acts"][1]["carries"] == "none" and b["acts"][1]["ideas"] == []


def test_validate_story_requires_hook_and_promise():
    """The cold open IS the product: a bible without them would silently ship a script
    with no reason to keep watching — the exact failure this format replaced."""
    import pytest
    b = _bible_min(); b.pop("hook_puzzles")
    with pytest.raises(RuntimeError):
        script._validate_story(b)
    b = _bible_min(); b.pop("promise")
    with pytest.raises(RuntimeError):
        script._validate_story(b)


def test_recurring_figure_needs_both_halves():
    """A name with no description gives the image model nothing to lock onto — that is
    how a protagonist changed race mid-video. Half a figure is no figure."""
    b = script._validate_story(_bible_min(recurring_figure={"name": "Frankl", "description": ""}))
    assert b["recurring_figure"] is None


def test_validate_story_rejects_missing_argument_and_thin_acts():
    import pytest
    with pytest.raises(RuntimeError):
        script._validate_story({"protagonist": {"name": "X", "description": "d"}, "acts": [{"title": "1"}, {"title": "2"}]})
    with pytest.raises(RuntimeError):
        script._validate_story({"protagonist": {"name": "X", "description": "d"}, "argument": {"claim": "c"}, "acts": [{"title": "1"}]})


def test_shapes_from_docs_collects_and_dedupes():
    docs = [
        {"story": {"argument": {"stance": "mostly-right", "claim": "it oversells patience"},
                   "hook_puzzles": ["why is your Sunday flat"]}},
        {"story": {"argument": {"stance": "mostly-right", "claim": "it ignores luck"},
                   "hook_puzzles": ["why do you refresh the app"]}},
        {"story": {"opening_move": "envy"}},   # legacy book: pre-format bible
        {"scenes": []},                         # older book, no story at all — tolerated
    ]
    s = script._shapes_from_docs(docs)
    assert s["stances"] == ["mostly-right"]                       # deduped
    assert "why is your Sunday flat" in s["hooks"]
    assert "envy" in s["hooks"]                                    # legacy shape still counts
    assert "it oversells patience" in s["claims"]


def test_architect_prompt_demands_bible():
    p = script._build_architect_prompt(
        OUTLINE, "angle", 5, 7, 30,
        {"stances": ["mostly-right"], "hooks": ["envy"], "claims": ["it oversells patience"]},
    )
    assert "Cognibot" in p
    for key in ('"hook_puzzles"', '"promise"', '"argument"', '"author_story"',
                '"where_the_book_is_wrong"', '"recurring_figure"', '"acts"', '"anchor"'):
        assert key in p, key
    assert "second person" in p.lower()
    assert "never invent" in p.lower()                  # no fictional characters
    assert "mostly-right" in p and "envy" in p          # variety: prior shapes fed in


def test_architect_prompt_demands_every_key_idea():
    """Book #5 shipped 7 of 12 ideas. The idea count goes in the prompt so 'all of them'
    is a number the model can be held to, not a vibe."""
    outline = dict(OUTLINE, key_ideas=[{"title": f"idea {i}", "summary": "s"} for i in range(12)])
    p = script._build_architect_prompt(outline, "angle", 5, 7, 30, {})
    assert "ALL 12 key ideas" in p


BIBLE = {
    "hook_puzzles": ["why is your Sunday flat", "why does the raise not land"],
    "promise": "you'll see which sentence is the dangerous one",
    "author_story": "he wrote it in nine days",
    "recurring_figure": {"name": "Viktor Frankl", "description": "50s, pale, grey side-parted hair"},
    "argument": {"stance": "dangerously-half-right", "claim": "patience is a luxury good"},
    "where_the_book_is_wrong": "the priming studies failed to replicate",
    "closing_image": "a book face-down on a windowsill", "voice_moves": ["total recall"],
    "acts": [{"title": "The Trap", "focus": "the idea bites", "role": "deliver ideas",
              "ideas": [{"idea": "margin of safety", "anchor": "a 90% drawdown"}], "carries": "ideas"}],
}

def test_act_prompt_is_second_person_and_forbids_invention():
    p = script._build_act_prompt(OUTLINE, BIBLE, BIBLE["acts"][0], 3, 6, ["Cold Open"], 10, 14)
    assert "SECOND PERSON" in p
    assert "INVENT NO ONE" in p                          # the whole point of the format change
    assert "margin of safety" in p and "90% drawdown" in p   # idea + its concrete anchor
    assert "Viktor Frankl" in p                           # the REAL recurring figure is threaded
    assert "honest" not in p.lower()                      # we don't tell it to be "honest" (the crutch)

def test_act_prompt_hook_carries_puzzles_and_promise():
    hook = dict(BIBLE["acts"][0]); hook["carries"] = "hook"
    p = script._build_act_prompt(OUTLINE, BIBLE, hook, 1, 6, [], 10, 14)
    assert "why is your Sunday flat" in p                 # the cascade
    assert "he wrote it in nine days" in p                # the real author story
    assert "which sentence is the dangerous one" in p     # the promise = reason to stay

def test_act_prompt_where_wrong_uses_the_bot_flex():
    ww = dict(BIBLE["acts"][0]); ww["carries"] = "where-wrong"
    p = script._build_act_prompt(OUTLINE, BIBLE, ww, 5, 6, ["a"], 10, 14)
    assert "failed to replicate" in p
    assert "total recall" in p.lower()

def test_act_prompt_final_delivers_verdict():
    final = dict(BIBLE["acts"][0]); final["carries"] = "verdict"; final["role"] = "final"
    p = script._build_act_prompt(OUTLINE, BIBLE, final, 6, 6, ["a", "b"], 10, 14)
    assert "patience is a luxury good" in p              # the withheld argument lands here
    assert "windowsill" in p.lower()                      # the closing image


def test_generate_long_wires_architect_then_acts(monkeypatch):
    calls = {"n": 0}
    def fake_call_stage(cfg, stage, prompt, **kw):
        calls["n"] += 1
        if "ARCHITECTING" in prompt:                       # the architect pass
            return {"hook_puzzles": ["why is your Sunday flat"],
                    "promise": "you'll see the dangerous sentence",
                    "argument": {"stance": "mostly-wrong", "claim": "the book oversells patience"},
                    "recurring_figure": {"name": "Frankl", "description": "grey side-parted hair"},
                    "acts": [{"title": "Cold Open", "carries": "hook"},
                             {"title": "The Trap", "carries": "verdict"}]}
        return {"scenes": [{"narration": "n", "on_screen_text": "", "image_prompt": "i"}]}
    monkeypatch.setattr(script, "call_stage", fake_call_stage)
    monkeypatch.setattr(script, "_prior_story_shapes", lambda cfg: {"stances": [], "hooks": [], "claims": []})
    cfg = {"script": {"long": {"min_chapters": 2, "max_chapters": 2,
                               "min_scenes_per_chapter": 1, "max_scenes_per_chapter": 1, "target_minutes": 20}}}
    scenes, extra = script._generate_long(cfg, OUTLINE, "angle")
    assert calls["n"] == 3                                  # 1 architect + 2 acts
    assert extra["story"]["argument"]["claim"] == "the book oversells patience"
    assert extra["chapters"] == ["Cold Open", "The Trap"]
    # the doc-level `character` slot now carries the REAL recurring figure, so the
    # existing image reference-locking keeps working without knowing anything changed
    assert extra["character"] == {"name": "Frankl", "description": "grey side-parted hair"}
    assert scenes[0]["chapter"] == "Cold Open" and scenes[1]["chapter"] == "The Trap"
    assert scenes[0]["id"] == 1 and scenes[1]["id"] == 2


def test_generate_long_tolerates_no_recurring_figure(monkeypatch):
    """Plenty of books have no person worth recurring. `images` must then simply skip
    character-locking rather than crash."""
    def fake_call_stage(cfg, stage, prompt, **kw):
        if "ARCHITECTING" in prompt:
            return {"hook_puzzles": ["why"], "promise": "p",
                    "argument": {"claim": "c"},
                    "acts": [{"title": "A", "carries": "hook"}, {"title": "B", "carries": "verdict"}]}
        return {"scenes": [{"narration": "n", "on_screen_text": "", "image_prompt": "i"}]}
    monkeypatch.setattr(script, "call_stage", fake_call_stage)
    monkeypatch.setattr(script, "_prior_story_shapes", lambda cfg: {"stances": [], "hooks": [], "claims": []})
    cfg = {"script": {"long": {"min_chapters": 2, "max_chapters": 2,
                               "min_scenes_per_chapter": 1, "max_scenes_per_chapter": 1, "target_minutes": 20}}}
    _, extra = script._generate_long(cfg, OUTLINE, "angle")
    assert extra["character"] is None


def _bible_min(**over):
    b = {"hook_puzzles": ["why is your Sunday flat"],
         "promise": "you'll see the dangerous sentence",
         "argument": {"claim": "c"},
         "acts": [{"title": "1"}, {"title": "2"}, {"title": "3"}]}
    b.update(over)
    return b


def test_validate_story_pins_verdict_when_architect_omits_it():
    # off-vocabulary carries all coerce to "none"; without this invariant NO act would
    # ever judge (every act prompt says only the verdict act does) -> script with no verdict
    b = script._validate_story(_bible_min(acts=[
        {"title": "1", "carries": "the opening"}, {"title": "2", "carries": "middle"},
        {"title": "3", "carries": "the payoff"}]))
    assert [a["carries"] for a in b["acts"]].count("verdict") == 1
    assert b["acts"][-1]["carries"] == "verdict"
    assert b["acts"][0]["carries"] == "hook"      # and something must open


def test_validate_story_keeps_explicit_verdict_act():
    b = script._validate_story(_bible_min(acts=[
        {"title": "1", "carries": "hook"}, {"title": "2", "carries": "verdict"}, {"title": "3"}]))
    assert b["acts"][1]["carries"] == "verdict"
    assert b["acts"][-1]["carries"] != "verdict"   # not double-assigned


def test_validate_story_assigns_where_wrong_only_with_material():
    b = script._validate_story(_bible_min(where_the_book_is_wrong="priming failed to replicate"))
    assert [a["carries"] for a in b["acts"]].count("where-wrong") == 1
    b2 = script._validate_story(_bible_min())          # no material -> no such act
    assert "where-wrong" not in [a["carries"] for a in b2["acts"]]


def test_validate_story_coerces_string_voice_moves():
    b = script._validate_story(_bible_min(voice_moves="total recall"))
    assert b["voice_moves"] == ["total recall"]   # not 12 single characters


def test_validate_story_coerces_bare_string_ideas():
    b = script._validate_story(_bible_min(acts=[
        {"title": "1", "ideas": ["compounding", "margin of safety"]}, {"title": "2"}]))
    assert b["acts"][0]["ideas"] == [{"idea": "compounding", "puzzle": "", "anchor": ""},
                                     {"idea": "margin of safety", "puzzle": "", "anchor": ""}]


def test_validate_story_carries_puzzle_and_bridge():
    """Puzzle-first is the watchability lever: each idea keeps its opening puzzle, and each
    act keeps its bridge_out into the next. Both must survive validation to reach the prompt."""
    b = script._validate_story(_bible_min(acts=[
        {"title": "1", "ideas": [{"idea": "will to meaning",
                                  "puzzle": "why did the man who preached meaning survive by luck?",
                                  "anchor": "16 million copies"}],
         "bridge_out": "but the line everyone quotes is the one that's most wrong"},
        {"title": "2"}]))
    idea = b["acts"][0]["ideas"][0]
    assert idea["puzzle"].startswith("why did the man")
    assert idea["anchor"] == "16 million copies"
    assert b["acts"][0]["bridge_out"].startswith("but the line")


def test_act_prompt_leads_with_puzzle_and_ends_on_bridge():
    b = script._validate_story(_bible_min(acts=[
        {"title": "The Trap", "carries": "ideas",
         "ideas": [{"idea": "hyper-reflection",
                    "puzzle": "try to fall asleep on command",
                    "anchor": "the eye that sees itself is failing"}],
         "bridge_out": "so where is meaning actually hiding?"},
        {"title": "2", "carries": "verdict"}]))
    p = script._build_act_prompt(OUTLINE, b, b["acts"][0], 3, 5, ["Cold Open"], 10, 14)
    assert "PUZZLE-FIRST" in p                                   # the rule is present
    assert "try to fall asleep on command" in p                  # the idea's puzzle is threaded
    assert "so where is meaning actually hiding?" in p           # the bridge is threaded
    # the verdict act must NOT be told to end on a bridge (it ends on the closing image)
    pv = script._build_act_prompt(OUTLINE, b, b["acts"][1], 5, 5, ["a"], 10, 14)
    assert "END this act on the bridge" not in pv


def test_act_prompt_verdict_omits_empty_optional_clauses():
    b = script._validate_story(_bible_min(acts=[{"title": "1"}, {"title": "2"}]))
    p = script._build_act_prompt(OUTLINE, b, b["acts"][-1], 2, 2, ["a"], 10, 14)
    assert "()" not in p and "—  —" not in p     # no empty parens / dangling dashes
    assert '"c"' in p                             # the verdict still lands
