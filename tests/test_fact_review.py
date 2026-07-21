import json

from cogni import fact_review as fr


def _book(tmp_path, text):
    p = tmp_path / "book.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_excerpt_samples_the_whole_book_not_just_the_head(tmp_path, monkeypatch):
    """The old code took text[:max_chars] — on a 306k book that is the first ~52%, so a
    true claim about the ending reads as "not-in-book" while a fabrication about it is
    never checked. Every part of the book must appear in the excerpt."""
    head, middle, tail = "AAAA" * 5000, "MMMM" * 5000, "ZZZZ" * 5000
    p = _book(tmp_path, head + middle + tail)
    monkeypatch.setattr(fr, "resolve_path", lambda cfg, key: p)

    excerpt = fr.load_book_excerpt({}, max_chars=6000)

    assert len(excerpt) < len(head + middle + tail)   # it really is capped
    assert "AAAA" in excerpt                           # beginning
    assert "MMMM" in excerpt                           # middle
    assert "ZZZZ" in excerpt                           # END — the regression this guards


def test_short_book_is_passed_through_whole(tmp_path, monkeypatch):
    p = _book(tmp_path, "a short book")
    monkeypatch.setattr(fr, "resolve_path", lambda cfg, key: p)
    assert fr.load_book_excerpt({}, max_chars=10_000) == "a short book"


def _scenes_doc(n):
    return {"scenes": [{"id": i, "narration": f"beat {i}"} for i in range(1, n + 1)]}


def test_fact_review_batches_instead_of_one_giant_call(tmp_path, monkeypatch):
    """94 scenes plus 160k of book in a single call is the shape that blew the CLI
    timeout on visuals. Batch, and persist after each batch."""
    scenes_path = tmp_path / "scenes.json"
    scenes_path.write_text(json.dumps(_scenes_doc(45)), encoding="utf-8")
    monkeypatch.setattr(fr, "resolve_path", lambda cfg, key: scenes_path)
    monkeypatch.setattr(fr, "load_book_excerpt", lambda cfg: "BOOK")
    monkeypatch.setattr(fr, "load_config", lambda: {})

    calls = []

    def fake_call_stage(cfg, stage, prompt, **kw):
        ids = [int(line.split()[1].rstrip(":"))
               for line in prompt.splitlines() if line.startswith("Scene ")]
        calls.append(ids)
        return {"scenes": [{"id": i, "ok": True, "issues": []} for i in ids]}

    monkeypatch.setattr(fr, "call_stage", fake_call_stage)
    out = fr.fact_review(cfg={})

    assert len(calls) == 3                       # 45 scenes / 20 per call
    assert [len(c) for c in calls] == [20, 20, 5]
    assert sorted(i for c in calls for i in c) == list(range(1, 46))   # nothing dropped
    assert out["n_ok"] == 45
    # persisted, not just held in memory
    saved = json.loads(scenes_path.read_text(encoding="utf-8"))
    assert all(s["fact_review"]["ok"] for s in saved["scenes"])


def test_flagged_scenes_are_reported(tmp_path, monkeypatch):
    scenes_path = tmp_path / "scenes.json"
    scenes_path.write_text(json.dumps(_scenes_doc(3)), encoding="utf-8")
    monkeypatch.setattr(fr, "resolve_path", lambda cfg, key: scenes_path)
    monkeypatch.setattr(fr, "load_book_excerpt", lambda cfg: "BOOK")
    monkeypatch.setattr(fr, "load_config", lambda: {})
    monkeypatch.setattr(fr, "call_stage", lambda cfg, stage, prompt, **kw: {"scenes": [
        {"id": 1, "ok": True, "issues": []},
        {"id": 2, "ok": False, "issues": ["not-in-book: the coat lining is invented"]},
        {"id": 3, "ok": True, "issues": []},
    ]})
    out = fr.fact_review(cfg={})
    assert out["flagged"] == [2] and out["n_ok"] == 2
