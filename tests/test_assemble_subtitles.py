from cogni import assemble

def test_ass_color_cream_opaque():
    # #F1EDE4 -> BGR E4EDF1, alpha 00
    assert assemble._ass_color("F1EDE4", 0) == "&H00E4EDF1"

def test_ass_color_teal_semi():
    # #14332E -> BGR 2E3314, alpha 0x78
    assert assemble._ass_color("14332E", 0x78) == "&H782E3314"

def test_subtitle_style_uses_config_and_palette():
    cfg = {"video": {"subtitle": {"font": "Trebuchet MS", "font_size": 16,
                                   "text_color": "F1EDE4", "box_color": "14332E",
                                   "box_alpha": 120, "margin_v": 60}}}
    s = assemble._subtitle_style(cfg)
    assert "FontName=Trebuchet MS" in s
    assert "PrimaryColour=&H00E4EDF1" in s
    assert "BackColour=&H782E3314" in s
    assert "MarginV=60" in s

def test_subtitle_style_defaults_when_absent():
    s = assemble._subtitle_style({"video": {}})
    assert "FontName=" in s and "PrimaryColour=" in s
