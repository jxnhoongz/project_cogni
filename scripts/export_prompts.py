"""Export the active book's image prompts for MANUAL generation in the Higgsfield web app.

Why: the web app's "Unlimited" toggle is free but has no API (verified — the API refuses
`use_unlim` and bills credits anyway). So when you'd rather spend an evening than credits,
generate the stills by hand and drop them back in. This writes the EXACT prompts the
pipeline would have sent (beat + recurring-character clause + STYLE token), numbered, so
you can paste straight into the web app in order.

Pairs with scripts/import_images.py, which renames your 1.png..N.png back onto the right
scenes using the manifest this writes. Keep the numbering — that's the whole contract.

Usage:  python scripts/export_prompts.py      -> projects/<slug>/manual/{prompts.txt,manifest.json}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from cogni.config import load_config, load_style_token, resolve_path  # noqa: E402
from cogni.images import _image_prompt  # noqa: E402


def main() -> None:
    cfg = load_config()
    slug = (REPO / ".active_project").read_text(encoding="utf-8").strip()
    doc = json.loads(resolve_path(cfg, "scenes").read_text(encoding="utf-8"))
    scenes, character, style = doc["scenes"], doc.get("character"), load_style_token()

    out_dir = REPO / "projects" / slug / "manual"
    out_dir.mkdir(parents=True, exist_ok=True)

    items: list[dict] = []
    for s in scenes:
        base = (s.get("start_image_prompt") or s.get("image_prompt") or "").strip()
        if not base:
            raise SystemExit(f"scene {s['id']} has no image prompt — run `visuals` first.")
        items.append({"target": f"scene_{s['id']:03d}.png",
                      "prompt": _image_prompt(base, character, style)})
    # end keyframes, only for animated beats (same rule as cogni/images.py)
    for s in scenes:
        if s.get("animate") and (s.get("end_image_prompt") or "").strip():
            items.append({"target": f"scene_{s['id']:03d}_end.png",
                          "prompt": f"{s['end_image_prompt'].strip()} {style}".strip()})

    for i, it in enumerate(items, 1):
        it["index"] = i

    (out_dir / "manifest.json").write_text(
        json.dumps({"slug": slug, "items": items}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")

    lines = [
        f"MANUAL IMAGE PROMPTS — {slug}  ({len(items)} images)",
        "",
        "HOW TO USE",
        "  1. higgsfield.ai/ai/image  ->  turn the 'Unlimited' toggle ON (green) = 0 credits.",
        "  2. Set aspect ratio 16:9 EVERY time. A 3:4 image gets badly cropped by assemble.",
        "  3. Generate each prompt below IN ORDER. Save as its NUMBER: 1.png, 2.png, ... "
        f"{len(items)}.png",
        "  4. Put them all in ONE folder, then tell Claude the folder path.",
        "",
        "  KEEP THE NUMBERING EXACT. If a generation flops, re-roll it and keep its number —",
        "  do not renumber, or every image after it lands on the wrong scene.",
        "",
        "=" * 78,
        "",
    ]
    for it in items:
        lines.append(f"----- {it['index']} -----  (becomes {it['target']})")
        lines.append(it["prompt"])
        lines.append("")
    (out_dir / "prompts.txt").write_text("\n".join(lines), encoding="utf-8")

    n_end = sum(1 for i in items if i["target"].endswith("_end.png"))
    print(f"[export] {slug}: {len(items)} prompts ({len(items)-n_end} stills + {n_end} end-frames)")
    print(f"[export] -> {out_dir / 'prompts.txt'}")
    print(f"[export] -> {out_dir / 'manifest.json'}  (import_images.py reads this)")


if __name__ == "__main__":
    main()
