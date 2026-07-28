import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    "check_crutches", pathlib.Path(__file__).resolve().parent.parent / "scripts" / "check_crutches.py")
cc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cc)

def _sc(i, n): return {"id": i, "narration": n}

def test_flags_honest_overuse():
    scenes = [_sc(i, "honest take here") for i in range(1, 6)]   # 5 "honest"
    out = cc.find_crutches(scenes, honest_max=3)
    assert sum(c for _, c in out["honest"]) >= 5
    assert out["honest"]                                          # non-empty -> flagged

def test_ignores_honest_under_threshold():
    out = cc.find_crutches([_sc(1, "an honest look"), _sc(2, "nothing here")], honest_max=3)
    assert out["honest"] == []

def test_flags_skeleton_phrases():
    scenes = [_sc(1, "here's my honest take on this"), _sc(2, "five years later, he was fine"),
              _sc(3, "so who is this book for")]
    out = cc.find_crutches(scenes, honest_max=99)                # isolate skeleton detection
    hit = {sid for sid, _ in out["skeleton"]}
    assert hit == {1, 2, 3}
