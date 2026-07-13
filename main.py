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

from cogni.animate import animate_plan
from cogni.assemble import assemble
from cogni.audio import check_audio
from cogni.config import (
    active_project,
    list_projects,
    load_config,
    load_style_token,
    set_active_project,
)
from cogni.convert import convert
from cogni.images import images
from cogni.ingest import ingest
from cogni.llm import call_stage
from cogni.narrate import narrate
from cogni.fact_review import fact_review
from cogni.review import review
from cogni.script import script
from cogni.script_review import revise_narration, script_review
from cogni.visuals import visuals


def cmd_narrate(args: argparse.Namespace) -> int:
    narrate(force=args.force)
    return 0


def cmd_projects(_args: argparse.Namespace) -> int:
    projects = list_projects()
    if not projects:
        print("No books yet — run `convert <book-file>` to create one.")
        return 0
    active = active_project()
    for slug in projects:
        print(f"  {'* ' if slug == active else '  '}{slug}")
    print("\n(* = active)")
    return 0


def cmd_script_review(args: argparse.Namespace) -> int:
    summary = script_review(force=args.force)
    return 0 if not summary["flagged"] else 1


def cmd_revise(args: argparse.Namespace) -> int:
    ids = [int(x) for x in args.scenes.split(",")] if args.scenes else None
    revise_narration(ids)
    return 0


def cmd_fact_check(args: argparse.Namespace) -> int:
    summary = fact_review(force=args.force)
    return 0 if not summary["flagged"] else 1


def cmd_visuals(args: argparse.Namespace) -> int:
    visuals(force=args.force)
    return 0


def cmd_review(_args: argparse.Namespace) -> int:
    summary = review()
    return 0 if summary["passed"] else 1


def cmd_images(args: argparse.Namespace) -> int:
    images(force=args.force, skip_review=args.skip_review)
    return 0


def cmd_assemble(args: argparse.Namespace) -> int:
    assemble(force=args.force)
    return 0


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


def cmd_animate(_args: argparse.Namespace) -> int:
    plan = animate_plan()
    if not plan:
        print("No scenes flagged animate=true. Tick 'Animate' in the UI (Edit script) first.")
        return 0
    print(f"{len(plan)} scene(s) flagged for Higgsfield hero clips (start->end):")
    for p in plan:
        if p["has_clip"]:
            state = "[done] has clip"
        elif p["start_image"] and p["end_image"]:
            state = "[ready] start + end keyframes"
        elif p["start_image"]:
            state = "[wait] end keyframe missing - run `images`"
        else:
            state = "[wait] no keyframes - run `images`"
        print(f"  scene {p['id']:>2}: {state}")
        if p["start_image"]:
            print(f"           start: {p['start_image']}")
        if p["end_image"]:
            print(f"           end:   {p['end_image']}")
        print(f"           clip:  {p['clip']}")
    print("\nWith the Higgsfield MCP connected, run the `cogni-animate` skill to "
          "generate these clips and re-assemble.")
    return 0


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
    parser.add_argument(
        "--project", default=None,
        help="Act on this book (slug); default is the active one. See `projects`.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_projects = sub.add_parser("projects", help="List books and show the active one")
    p_projects.set_defaults(func=cmd_projects)

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
        "script", help="Generate the verdict narration scenes.json from outline.json"
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

    p_sreview = sub.add_parser(
        "script-review",
        help="Critique the narration and flag weak scenes (text-only, no credits)",
    )
    p_sreview.add_argument(
        "--force", action="store_true",
        help="Re-review every scene (default: only ones changed since last review)",
    )
    p_sreview.set_defaults(func=cmd_script_review)

    p_revise = sub.add_parser(
        "revise", help="Rewrite flagged scenes' narration to fix the review notes"
    )
    p_revise.add_argument(
        "--scenes", default=None,
        help="Comma-separated scene ids to revise (default: all flagged by script-review/fact-check)",
    )
    p_revise.set_defaults(func=cmd_revise)

    p_fact = sub.add_parser(
        "fact-check",
        help="Check narration claims against book.md and flag grounding issues (no credits)",
    )
    p_fact.add_argument(
        "--force", action="store_true",
        help="Re-check every scene (default: only ones changed since last check)",
    )
    p_fact.set_defaults(func=cmd_fact_check)

    p_visuals = sub.add_parser(
        "visuals",
        help="Write per-scene keyframe + motion prompts (start/end/video) — no credits",
    )
    p_visuals.add_argument(
        "--force", action="store_true", help="Rewrite prompts even if they exist"
    )
    p_visuals.set_defaults(func=cmd_visuals)

    p_review = sub.add_parser(
        "review",
        help="Validate the visual prompts and gate generation (text-only, no credits)",
    )
    p_review.set_defaults(func=cmd_review)

    p_narrate = sub.add_parser(
        "narrate", help="TTS the narration to audio/scene_XXX.mp3 (edge-tts)"
    )
    p_narrate.add_argument(
        "--force", action="store_true", help="Re-narrate existing audio"
    )
    p_narrate.set_defaults(func=cmd_narrate)

    p_audio = sub.add_parser(
        "check-audio", help="Verify every scene has a narration audio file"
    )
    p_audio.set_defaults(func=cmd_check_audio)

    p_animate = sub.add_parser(
        "animate", help="Show which scenes are flagged for Higgsfield hero clips"
    )
    p_animate.set_defaults(func=cmd_animate)

    p_images = sub.add_parser(
        "images", help="Generate a still per scene into images/scene_XXX.png"
    )
    p_images.add_argument(
        "--force", action="store_true", help="Regenerate existing images"
    )
    p_images.add_argument(
        "--skip-review", action="store_true",
        help="Bypass the review gate and generate anyway (spends credits)",
    )
    p_images.set_defaults(func=cmd_images)

    p_assemble = sub.add_parser(
        "assemble", help="Render output/final.mp4 from scenes + images (+ audio)"
    )
    p_assemble.add_argument(
        "--force", action="store_true", help="Re-render an existing final.mp4"
    )
    p_assemble.set_defaults(func=cmd_assemble)

    p_style = sub.add_parser("show-style", help="Print the current STYLE token")
    p_style.set_defaults(func=cmd_show_style)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "project", None):
        set_active_project(args.project)
    try:
        return args.func(args)
    except (RuntimeError, FileNotFoundError, ValueError, KeyError) as e:
        # Expected, actionable failures (missing key/file/config) — no stack trace.
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
