from cogni import images


def test_image_prompt_threads_character():
    p = images._image_prompt(
        "a kitchen at night",
        {"name": "Dana", "description": "woman in blue scrubs, hair in a bun, seen from behind"},
        "RISO STYLE",
    )
    assert "a kitchen at night" in p
    assert "blue scrubs" in p
    assert "RISO STYLE" in p


def test_image_prompt_no_character():
    assert images._image_prompt("a desk", None, "STYLE") == "a desk STYLE"


def test_image_prompt_empty_character_desc():
    assert images._image_prompt("a desk", {"name": "X", "description": ""}, "STYLE") == "a desk STYLE"
