"""Single LLM entry point for the whole pipeline.

All stages call `call_llm(model, prompt, ...)`. It wraps OpenRouter via the
OpenAI-compatible client so English (Claude) and Khmer (Gemini) route through
one place — the model slug per stage is set in config.yaml.
"""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .config import load_config, require_env

# OpenRouter recommends these headers for attribution; harmless if unused.
_APP_HEADERS = {
    "HTTP-Referer": "https://github.com/jxnhoongz/project_cogni",
    "X-Title": "Project Cogni",
}


def _client(cfg: dict[str, Any]) -> OpenAI:
    """Build an OpenAI client pointed at OpenRouter. Fails loudly if no key."""
    api_key = require_env("OPENROUTER_API_KEY")
    return OpenAI(
        base_url=cfg["llm"]["base_url"],
        api_key=api_key,
        timeout=cfg["llm"].get("timeout_sec", 120),
        default_headers=_APP_HEADERS,
    )


def call_llm(
    model: str,
    prompt: str,
    *,
    system: str | None = None,
    json_out: bool = True,
    max_tokens: int | None = None,
    cfg: dict[str, Any] | None = None,
) -> str | dict[str, Any]:
    """Send one prompt to `model` (an OpenRouter slug) and return the reply.

    json_out=True  -> request a JSON object and return a parsed dict.
    json_out=False -> return the raw text string.

    Raises RuntimeError on missing key, empty response, or (when json_out)
    unparseable JSON — never returns a half-broken result silently.
    """
    cfg = cfg or load_config()
    client = _client(cfg)

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens or cfg["llm"].get("max_tokens", 8000),
    }
    if json_out:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as e:  # network / auth / provider errors — surface clearly
        raise RuntimeError(f"LLM call to '{model}' failed: {e}") from e

    if not resp.choices:
        raise RuntimeError(f"LLM call to '{model}' returned no choices")
    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError(f"LLM call to '{model}' returned empty content")

    if not json_out:
        return content

    return _parse_json(content, model)


def _parse_json(content: str, model: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating ```json fences some models emit."""
    text = content.strip()
    if text.startswith("```"):
        # strip a leading ```json / ``` fence and the trailing ```
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"LLM '{model}' did not return valid JSON: {e}\n--- got ---\n{content[:500]}"
        ) from e
    if not isinstance(data, dict):
        raise RuntimeError(f"LLM '{model}' returned JSON but not an object: {type(data)}")
    return data
