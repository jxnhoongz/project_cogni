"""Stage 3: narrate — scenes.json narration -> audio/scene_XXX.mp3 via TTS.

`generate_tts()` is a pluggable provider. Provider "edge" uses edge-tts (free,
no key). Later providers (OpenAI, ElevenLabs) slot in the same way. Cached: a
scene keeps its audio unless --force. Records audio_path back into scenes.json,
so `assemble` finds the narration.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from .config import load_config, project_root, resolve_path


# --- Subtitle chunking -------------------------------------------------------
# edge-tts gives per-word timings; we group only a few words per cue so a short
# phrase is on screen at once instead of a whole sentence. Tune via config.yaml
# tts.subtitle_max_words / tts.subtitle_max_chars; these are the defaults.
_SUB_MAX_WORDS = 5
_SUB_MAX_CHARS = 42
_SENTENCE_END = ".!?…。！？"   # break a cue after sentence-final punctuation
_GAP_FILL_SEC = 0.5           # extend a cue across gaps <= this so captions don't flicker


def _fmt_ts(seconds: float) -> str:
    """Seconds -> SRT timestamp HH:MM:SS,mmm."""
    ms = max(0, int(round(seconds * 1000)))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _chunk_srt(
    words: list[tuple[float, float, str]],
    max_words: int = _SUB_MAX_WORDS,
    max_chars: int = _SUB_MAX_CHARS,
) -> str:
    """Group (start, end, word) timings into short SRT cues (a few words each)."""
    groups: list[list[tuple[float, float, str]]] = []
    cur: list[tuple[float, float, str]] = []
    cur_chars = 0
    for start, end, raw in words:
        w = raw.strip()
        if not w:
            continue
        # Start a new cue before adding a word that would overflow this one.
        if cur and (len(cur) >= max_words or cur_chars + 1 + len(w) > max_chars):
            groups.append(cur)
            cur, cur_chars = [], 0
        cur.append((start, end, w))
        cur_chars += (1 if cur_chars else 0) + len(w)
        # Break after sentence-final punctuation so cues land on natural pauses.
        if w[-1] in _SENTENCE_END:
            groups.append(cur)
            cur, cur_chars = [], 0
    if cur:
        groups.append(cur)

    spans = [[g[0][0], g[-1][1], " ".join(x[2] for x in g)] for g in groups]
    # Fill small gaps between adjacent cues so a caption doesn't blink off/on.
    for i in range(len(spans) - 1):
        gap = spans[i + 1][0] - spans[i][1]
        if 0 < gap <= _GAP_FILL_SEC:
            spans[i][1] = spans[i + 1][0]

    return "\n".join(
        f"{i}\n{_fmt_ts(start)} --> {_fmt_ts(end)}\n{text}\n"
        for i, (start, end, text) in enumerate(spans, 1)
    )


_WORD_RE = re.compile(r"\S+")


def _norm(token: str) -> str:
    """Lowercase alphanumerics only — for matching a spoken word to a source word."""
    return re.sub(r"[^0-9a-z]+", "", token.lower())


def _attach_punctuation(
    words: list[tuple[float, float, str]], source: str
) -> list[tuple[float, float, str]]:
    """Restore punctuation edge-tts strips from its word tokens.

    edge-tts emits bare words ("payoff", not "payoff."), so captions lose commas
    and periods and sentence-break detection can't fire. Walk the source text in
    order and swap each spoken word for its source token (which keeps punctuation).
    Best-effort: unmatched words are kept as-is, so it degrades gracefully.
    """
    src = _WORD_RE.findall(source)
    src_norm = [_norm(t) for t in src]
    out: list[tuple[float, float, str]] = []
    j = 0
    for start, end, w in words:
        wn = _norm(w)
        match = None
        for k in range(j, min(j + 6, len(src))):   # small window tolerates drift
            if wn and src_norm[k] == wn:
                match = k
                break
        if match is not None:
            out.append((start, end, src[match]))
            j = match + 1
        else:
            out.append((start, end, w))
    return out


def _edge_tts(
    text: str,
    voice: str,
    out_path: Path,
    max_words: int = _SUB_MAX_WORDS,
    max_chars: int = _SUB_MAX_CHARS,
) -> None:
    """Write the mp3 AND a word-synced .srt chunked into short phrases."""
    try:
        import edge_tts
    except ImportError as e:
        raise RuntimeError("edge-tts not installed — `pip install edge-tts`.") from e

    async def _run() -> None:
        # boundary="WordBoundary" (not the default SentenceBoundary) gives per-word
        # timings, so captions show a few words at a time rather than a whole line.
        comm = edge_tts.Communicate(text, voice, boundary="WordBoundary")
        words: list[tuple[float, float, str]] = []
        with open(out_path, "wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start = chunk["offset"] / 1e7               # 100-ns ticks -> seconds
                    end = (chunk["offset"] + chunk["duration"]) / 1e7
                    words.append((start, end, chunk["text"]))
        words = _attach_punctuation(words, text)
        out_path.with_suffix(".srt").write_text(
            _chunk_srt(words, max_words, max_chars), encoding="utf-8"
        )

    asyncio.run(_run())


def generate_tts(text: str, out_path: Path, cfg: dict[str, Any]) -> None:
    """Synthesize `text` to speech at out_path, per config tts.provider."""
    tts = cfg["tts"]
    provider = tts["provider"]
    if provider == "edge":
        _edge_tts(
            text,
            tts["voice"],
            out_path,
            max_words=int(tts.get("subtitle_max_words", _SUB_MAX_WORDS)),
            max_chars=int(tts.get("subtitle_max_chars", _SUB_MAX_CHARS)),
        )
    else:
        raise RuntimeError(f"unknown tts provider '{provider}' (use 'edge')")


def narrate(*, force: bool = False, cfg: dict[str, Any] | None = None) -> Path:
    """Generate narration audio for every scene in scenes.json (cached)."""
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(f"{scenes_path} not found — run `script` first.")
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    audio_dir = resolve_path(cfg, "audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    root = project_root(cfg)
    provider = cfg["tts"]["provider"]
    voice = cfg["tts"].get("voice", "")

    made = cached = 0
    changed = False
    for s in scenes:
        out = audio_dir / f"scene_{s['id']:03d}.mp3"
        rel = str(out.relative_to(root))
        text = s.get("narration") or s.get("narration_en") or ""
        if not text.strip():
            print(f"[narrate] scene {s['id']:>2}: skipped (no narration text)")
            continue
        if out.exists() and not force:
            cached += 1
        else:
            generate_tts(text, out, cfg)
            made += 1
            print(f"[narrate] scene {s['id']:>2}: narrated")
        if s.get("audio_path") != rel:
            s["audio_path"] = rel
            changed = True

    if changed:
        scenes_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"[narrate] provider={provider} voice={voice} — {made} narrated, {cached} cached "
          f"({len(scenes)} scenes) -> {audio_dir}")
    return audio_dir
