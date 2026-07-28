import pytest

from cogni import assemble
from cogni import config as cfgmod


def _lib(tmp_path, names):
    for n in names:
        (tmp_path / n).write_bytes(b"x")
    return tmp_path


def _patch(monkeypatch, tmp_path, slug):
    monkeypatch.setattr(assemble, "resolve_shared", lambda cfg, key: tmp_path)
    monkeypatch.setattr(cfgmod, "active_project", lambda: slug)


def test_explicit_config_music_wins(monkeypatch, tmp_path):
    _lib(tmp_path, ["a.mp3", "b.mp3"])
    _patch(monkeypatch, tmp_path, "some-book")
    got = assemble._find_music({"video": {"music": "b.mp3"}})
    assert got.name == "b.mp3"


def test_unknown_config_music_fails_loudly(monkeypatch, tmp_path):
    _lib(tmp_path, ["a.mp3"])
    _patch(monkeypatch, tmp_path, "some-book")
    with pytest.raises(RuntimeError, match="no such track"):
        assemble._find_music({"video": {"music": "nope.mp3"}})


def test_auto_pick_never_selects_vo_files(monkeypatch, tmp_path):
    # assets/audio/ also holds narration VO (outro_vo.mp3) — a VO file must never be
    # hashed onto as a background bed, whatever the slug lands on.
    _lib(tmp_path, ["a.mp3", "outro_vo.mp3"])
    for slug in ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"]:
        _patch(monkeypatch, tmp_path, slug)
        assert assemble._find_music({"video": {}}).name == "a.mp3"


def test_vo_only_library_yields_none(monkeypatch, tmp_path):
    _lib(tmp_path, ["outro_vo.mp3"])
    _patch(monkeypatch, tmp_path, "some-book")
    assert assemble._find_music({"video": {}}) is None


def test_auto_pick_is_stable_per_book_and_differs_across_books(monkeypatch, tmp_path):
    _lib(tmp_path, ["a.mp3", "b.mp3", "c.mp3", "d.mp3"])
    _patch(monkeypatch, tmp_path, "book-one")
    first = assemble._find_music({"video": {}})
    again = assemble._find_music({"video": {}})
    assert first == again                     # stable: re-assembles keep the same bed
    _patch(monkeypatch, tmp_path, "a-totally-different-book")
    other = assemble._find_music({"video": {}})
    assert other != first                     # different books get different beds
