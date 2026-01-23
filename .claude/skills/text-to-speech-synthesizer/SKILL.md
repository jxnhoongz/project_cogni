---
name: text-to-speech-synthesizer
description: Converts scripts to natural-sounding voiceover using ElevenLabs or Edge-TTS. Applies voice settings (0.95x speed, -2 pitch, calm emotion), normalizes to -16 LUFS. Use after script passes quality check, when saying "generate audio for [script]", or in production pipeline.
---

# Text To Speech Synthesizer

Converts scripts to natural voiceover audio files.

## Voice Settings (Locked)

| Setting | Value |
|---------|-------|
| Voice | Male, 30-40, neutral English |
| Speed | 0.95x (slightly slower) |
| Pitch | -2 semitones (warmer) |
| Emotion | Calm mentor |
| Normalization | -16 LUFS |

## Generate Audio

### Shorts (single file)

```bash
python scripts/call_tts_api.py --script script.json --output vo_S_20251012.mp3
```

### Midform (chapter chunks)

```bash
python scripts/call_tts_api.py --script midform.json --by-chapter --output-dir ./chapters/
python scripts/stitch_chapters.py --input-dir ./chapters/ --output vo_M_20251015.mp3
```

## Providers

1. **ElevenLabs** (primary) - Higher quality, has quota
2. **Edge-TTS** (backup) - Free, slightly robotic

## Output

```json
{
  "audio_file": "vo_S_20251012.mp3",
  "duration_sec": 95,
  "provider": "elevenlabs",
  "voice_profile": "male_calm_en",
  "normalized": true,
  "lufs": -16
}
```

## Pronunciation Fixes

Custom phonetic mappings for Chinese terms:
- 认知 → "ren-zhi" (cognitive)
- 本质 → "ben-zhi" (essence)
- 反脆弱 → "fan-cui-ruo" (antifragile)

## Post-Processing

After TTS:
```bash
python scripts/normalize_audio.py --input raw.mp3 --output normalized.mp3 --target-lufs -16
```
