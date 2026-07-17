"""Words the TTS narrator (edge-tts, en-US-BrianMultilingualNeural) mispronounces.

Keep narration clear of these — the fix is to rephrase, since the spoken audio and the
burned subtitles come from the same text (a phonetic respelling would fix the audio but
corrupt the on-screen word). Grow this list as new mispronunciations are heard.

Used by cogni/script.py (prompt: avoid these) and scripts/check_pronunciation.py (scan +
flag before narrate).
"""
from __future__ import annotations

# word (lowercase) -> why it's wrong + how to rephrase
TTS_AVOID: dict[str, str] = {
    "messier": ("Brian reads it as the French astronomer 'Messier' (mess-ee-AY), not the "
                "comparative 'MESS-ee-er'. Rephrase: 'more of a mess', 'sloppier', 'more tangled'."),
}


def avoid_clause() -> str:
    """One line for the script prompt listing the words to steer around."""
    if not TTS_AVOID:
        return ""
    words = ", ".join(sorted(TTS_AVOID))
    return (f"The narrator voice mispronounces these words — do NOT use them, rephrase around "
            f"them: {words}.")
