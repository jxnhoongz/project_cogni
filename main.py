"""Project Cogni CLI.

Each pipeline stage is a subcommand. Stages are added as they are built
(see PROGRESS.md build order). Today: `test-llm` to smoke-test the OpenRouter
wiring.

Usage:
    python main.py test-llm            # trivial prompt, default (ingest) model
    python main.py test-llm --stage script_en
    python main.py test-llm --text     # raw text instead of JSON
"""

from __future__ import annotations

import argparse
import sys

from cogni.audio import check_audio
from cogni.config import load_config, load_style_token
from cogni.convert import convert
from cogni.ingest import ingest
from cogni.llm import call_stage
from cogni.script import script


def cmd_convert(args: argparse.Namespace) -> int:
    convert(args.source, force=args.force)
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    ingest(force=args.force)
    return 0


def cmd_script(args: argparse.Namespace) -> int:
    script(force=args.force, angle=args.angle)
    return 0


def cmd_check_audio(_args: argparse.Namespace) -> int:
    return 0 if check_audio() else 1


def cmd_test_llm(args: argparse.Namespace) -> int:
    cfg = load_config()
    models = cfg["llm"]["models"]
    if args.stage not in models:
        print(f"Unknown stage '{args.stage}'. Known: {', '.join(models)}", file=sys.stderr)
        return 2
    spec = models[args.stage]
    print(f"[test-llm] stage={args.stage} spec={spec}")

    if args.text:
        reply = call_stage(cfg, args.stage, "Reply with exactly the word: pong", json_out=False)
    else:
        reply = call_stage(
            cfg,
            args.stage,
            'Reply with a JSON object of the form {"status": "ok"} and nothing else.',
            json_out=True,
        )
    print(f"[reply] {reply!r}")
    return 0


def cmd_show_style(_args: argparse.Namespace) -> int:
    print(load_style_token())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cogni", description="Project Cogni pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p_test = sub.add_parser("test-llm", help="Smoke-test the OpenRouter LLM wiring")
    p_test.add_argument(
        "--stage",
        default="ingest",
        help="Which config.yaml llm.models stage to use (default: ingest)",
    )
    p_test.add_argument(
        "--text",
        action="store_true",
        help="Request raw text instead of JSON",
    )
    p_test.set_defaults(func=cmd_test_llm)

    p_convert = sub.add_parser(
        "convert", help="Convert a book file (PDF/epub/docx) to input/book.md"
    )
    p_convert.add_argument("source", help="Path to the book file")
    p_convert.add_argument(
        "--force", action="store_true", help="Overwrite an existing book.md"
    )
    p_convert.set_defaults(func=cmd_convert)

    p_ingest = sub.add_parser(
        "ingest", help="Extract title/thesis/key ideas from book.md to outline.json"
    )
    p_ingest.add_argument(
        "--force", action="store_true", help="Overwrite an existing outline.json"
    )
    p_ingest.set_defaults(func=cmd_ingest)

    p_script = sub.add_parser(
        "script",
        help="Generate EN+KM narration scenes.json + recording_script.txt from outline.json",
    )
    p_script.add_argument(
        "--force", action="store_true", help="Regenerate an existing scenes.json"
    )
    p_script.add_argument(
        "--angle",
        default=None,
        help="Override the narration point of view (default: config.yaml script.angle)",
    )
    p_script.set_defaults(func=cmd_script)

    p_audio = sub.add_parser(
        "check-audio", help="Verify every scene has a recorded audio file"
    )
    p_audio.set_defaults(func=cmd_check_audio)

    p_style = sub.add_parser("show-style", help="Print the current STYLE token")
    p_style.set_defaults(func=cmd_show_style)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (RuntimeError, FileNotFoundError, ValueError, KeyError) as e:
        # Expected, actionable failures (missing key/file/config) — no stack trace.
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
