from cogni import narrate


def test_audio_without_stamp_is_stale(tmp_path):
    mp3 = tmp_path / "scene_001.mp3"
    mp3.write_bytes(b"fake")
    # pre-existing audio from before this guard existed -> must re-narrate, not trust it
    assert narrate._audio_matches(mp3, "hello") is False


def test_audio_matches_only_the_text_it_was_made_from(tmp_path):
    mp3 = tmp_path / "scene_001.mp3"
    mp3.write_bytes(b"fake")
    narrate._stamp_audio_text(mp3, "This is Theo.")
    assert narrate._audio_matches(mp3, "This is Theo.") is True
    # the real bug: script rewritten, same filename -> must NOT be treated as cached
    assert narrate._audio_matches(mp3, "That little blinking line?") is False
