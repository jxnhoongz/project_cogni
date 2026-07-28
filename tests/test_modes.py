from cogni import modes

DOC = {
    "project_title": "Rich Dad Poor Dad",
    "thesis": "Financial literacy beats income.",
    "scenes": [
        {"id": 1, "chapter": "Cold Open", "narration": "Meet Dana.", "on_screen_text": ""},
        {"id": 2, "chapter": "The Trap", "narration": "She works hard.",
         "on_screen_text": "Hard work"},
        {"id": 3, "chapter": "Verdict", "narration": "Here is the honest take.",
         "on_screen_text": ""},
    ],
}


def test_build_prompt_covers_modes_and_cap():
    p = modes._build_prompt(DOC, 12)
    assert "HIGH" in p
    assert "MEDIUM" in p
    assert "LOW" in p
    # the max_animated cap number is stated
    assert "12" in p
    # beat 1 must be HIGH is called out explicitly
    assert "Beat 1" in p
    assert "MUST be HIGH" in p


def test_validate_forces_beat1_coerces_unknown_and_fills_prompt():
    data = {
        "scenes": [
            {"id": 1, "mode": "LOW", "video_prompt": ""},          # model got beat 1 wrong
            {"id": 2, "mode": "SIDEWAYS", "video_prompt": "spin"},  # unknown mode
            {"id": 3, "mode": "HIGH", "video_prompt": ""},          # animated but empty prompt
        ]
    }
    out = modes._validate(data, {1, 2, 3})

    # beat 1 is forced to HIGH regardless of what the model returned...
    assert out[1]["mode"] == "HIGH"
    # ...and, now animated with an empty prompt, gets the fallback motion.
    assert out[1]["video_prompt"]

    # an unknown mode is coerced to LOW, and LOW clears the video_prompt.
    assert out[2]["mode"] == "LOW"
    assert out[2]["video_prompt"] == ""

    # an empty video_prompt on a HIGH beat is filled with the fallback.
    assert out[3]["mode"] == "HIGH"
    assert out[3]["video_prompt"] == "Very slow push-in."
