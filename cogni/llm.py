"""Single LLM entry point for the whole pipeline.

Two providers, chosen per stage in config.yaml:
  - "claude"     -> the local `claude` CLI (Claude Code), billed against the
                    user's Claude subscription — NOT per-token. Use for Claude models.
  - "openrouter" -> OpenAI-compatible OpenRouter API (per-token). Use for models
                    the subscription can't reach, e.g. Gemini for Khmer.

Stages call `call_stage(cfg, "<stage>", prompt, ...)`; it resolves the stage's
{provider, model} from config and dispatches.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any

from openai import OpenAI

from .config import load_config, require_env

# OpenRouter recommends these headers for attribution; harmless if unused.
_APP_HEADERS = {
    "HTTP-Referer": "https://github.com/jxnhoongz/project_cogni",
    "X-Title": "Project Cogni",
}
# Generous ceiling for a single `claude -p` call (Opus long-form can take a while).
_CLAUDE_TIMEOUT_SEC = 300


def _claude_env() -> dict[str, str] | None:
    """Environment for the `claude` subprocess.

    On Windows, Claude Code needs to know where git-bash is. When invoked from a
    clean subprocess env that lacks it, `claude` errors out. If
    CLAUDE_CODE_GIT_BASH_PATH isn't already set, point it at a discovered bash.exe
    so the headless call works out of the box. Returns None on macOS/Linux (inherit
    the parent environment unchanged).
    """
    if os.name != "nt":
        return None
    env = os.environ.copy()
    if env.get("CLAUDE_CODE_GIT_BASH_PATH"):
        return env
    for cand in (
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ):
        if cand and os.path.exists(cand):
            env["CLAUDE_CODE_GIT_BASH_PATH"] = cand
            break
    return env


def call_stage(
    cfg: dict[str, Any],
    stage: str,
    prompt: str,
    *,
    system: str | None = None,
    json_out: bool = True,
    max_tokens: int | None = None,
) -> str | dict[str, Any]:
    """Resolve a stage's provider+model from config and call it."""
    models = cfg["llm"]["models"]
    if stage not in models:
        raise KeyError(f"config.yaml llm.models has no stage '{stage}'")
    provider, model = _resolve(models[stage])
    return call_llm(
        provider, model, prompt, system=system, json_out=json_out,
        max_tokens=max_tokens, cfg=cfg,
    )


def _resolve(spec: Any) -> tuple[str, str]:
    """A model spec is {provider, model}. (A bare string defaults to openrouter.)"""
    if isinstance(spec, str):
        return "openrouter", spec
    if isinstance(spec, dict) and spec.get("provider") and spec.get("model"):
        return str(spec["provider"]), str(spec["model"])
    raise ValueError(f"invalid model spec (need {{provider, model}}): {spec!r}")


def call_llm(
    provider: str,
    model: str,
    prompt: str,
    *,
    system: str | None = None,
    json_out: bool = True,
    max_tokens: int | None = None,
    cfg: dict[str, Any] | None = None,
) -> str | dict[str, Any]:
    """Send one prompt to (provider, model) and return the reply.

    json_out=True  -> parse and return a dict. json_out=False -> raw text.
    Raises RuntimeError on provider errors, empty output, or (json) bad JSON.
    """
    cfg = cfg or load_config()
    if provider not in ("claude", "openrouter"):
        raise RuntimeError(
            f"unknown LLM provider '{provider}' (use 'claude' or 'openrouter')"
        )

    def _once() -> str:
        if provider == "claude":
            return _call_claude(model, prompt, system)
        return _call_openrouter(cfg, model, prompt, system, json_out, max_tokens)

    # LLMs occasionally emit malformed JSON (a stray trailing comma) or empty output.
    # For JSON stages, resample a couple of times before giving up — each attempt is a
    # fresh completion, so a one-off glitch on a single long call no longer aborts a
    # whole multi-call run (e.g. one bad act killing a 6-act script).
    attempts = 3 if json_out else 1
    last_err: Exception = RuntimeError("no LLM attempt was made")
    for n in range(1, attempts + 1):
        content = (_once() or "").strip()
        if not content:
            last_err = RuntimeError(f"LLM call to {provider}:{model} returned empty content")
        elif not json_out:
            return content
        else:
            try:
                return _parse_json(content, model)
            except RuntimeError as e:
                last_err = e  # bad JSON — resample and try again
        # Say so: each claude attempt can take up to _CLAUDE_TIMEOUT_SEC, so a silent
        # retry looks like a hang (and hides *why* a run is slow).
        if n < attempts:
            print(f"[llm] {provider}:{model} gave unusable output ({last_err}); "
                  f"resampling ({n + 1}/{attempts}) ...")
    raise last_err


def _call_claude(model: str, prompt: str, system: str | None) -> str:
    """Run the local `claude` CLI headlessly (subscription-billed) and return text.

    Runs as a PURE generator: tools disabled (so it can't read the repo and turn
    agentic), project settings skipped, and in a neutral cwd so no project
    CLAUDE.md leaks in — we want a plain model completion, not Claude Code.
    """
    # Resolve the executable ourselves: on Windows `claude` is a .CMD shim and
    # subprocess/CreateProcess won't apply PATHEXT to a bare name, so we must pass
    # the full resolved path. shutil.which handles both (plain binary on macOS/Linux).
    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError(
            "`claude` CLI not found on PATH — install Claude Code, or set the stage's "
            "provider to 'openrouter' in config.yaml."
        )
    cmd = [
        exe, "-p", "--model", model, "--output-format", "json",
        "--tools", "",                 # no filesystem/tool access
        "--setting-sources", "user",   # ignore project/local settings
    ]
    if system:
        cmd += ["--system-prompt", system]
    try:
        proc = subprocess.run(
            cmd, input=prompt, capture_output=True,
            timeout=_CLAUDE_TIMEOUT_SEC, cwd=tempfile.gettempdir(),
            env=_claude_env(),
            # Force UTF-8 both ways. Without this, subprocess uses the locale
            # codec (cp1252 on Windows), which mangles the CLI's UTF-8 output —
            # em-dashes and curly quotes come back as mojibake ("—" -> "â€").
            text=True, encoding="utf-8", errors="replace",
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            "`claude` CLI not found — install Claude Code or use provider 'openrouter'."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"claude CLI timed out after {_CLAUDE_TIMEOUT_SEC}s") from e

    if proc.returncode != 0:
        raise RuntimeError(
            f"claude CLI failed (exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        )
    try:
        env = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"claude CLI returned non-JSON: {proc.stdout[:300]}") from e
    if env.get("is_error") or env.get("subtype") != "success":
        raise RuntimeError(f"claude CLI error: {env.get('result') or env}")
    return str(env.get("result") or "")


def _call_openrouter(
    cfg: dict[str, Any],
    model: str,
    prompt: str,
    system: str | None,
    json_out: bool,
    max_tokens: int | None,
) -> str:
    """Call OpenRouter via the OpenAI-compatible client. Fails loudly if no key."""
    api_key = require_env("OPENROUTER_API_KEY")
    client = OpenAI(
        base_url=cfg["llm"]["base_url"],
        api_key=api_key,
        timeout=cfg["llm"].get("timeout_sec", 120),
        default_headers=_APP_HEADERS,
    )
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
    except Exception as e:
        raise RuntimeError(f"OpenRouter call to '{model}' failed: {e}") from e
    if not resp.choices:
        raise RuntimeError(f"OpenRouter call to '{model}' returned no choices")
    return resp.choices[0].message.content or ""


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")  # control chars except \t \n \r


def _repair_json(text: str) -> str:
    """Best-effort fixes for quirks LLMs emit: a trailing comma before } or ], and
    stray control characters. Cheap first line of defence before we resample."""
    return _CTRL_RE.sub("", _TRAILING_COMMA_RE.sub(r"\1", text))


def _parse_json(content: str, model: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating a ```json fence and/or surrounding prose."""
    text = content.strip()
    fenced = _FENCE_RE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    else:
        # No fence — carve out the outermost {...} in case there's preamble.
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            text = text[start : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            data = json.loads(_repair_json(text))  # trailing comma / stray control char
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"LLM '{model}' did not return valid JSON: {e}\n--- got ---\n{content[:500]}"
            ) from e
    if not isinstance(data, dict):
        raise RuntimeError(f"LLM '{model}' returned JSON but not an object: {type(data)}")
    return data
