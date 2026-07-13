"""Project Cogni — web UI (thin wrapper over the pipeline stages).

Each book is a project. Pick a book (or upload one), then: generate script ->
edit the narration + tick Animate -> generate narration (TTS) -> generate images
-> generate video. The Preview tab shows everything together.

No real logic lives here — every button calls a stage function in cogni/.
Run:  python app.py   (opens http://127.0.0.1:7860)
"""

from __future__ import annotations

import gradio as gr

from cogni import store
from cogni.assemble import assemble
from cogni.config import active_project, list_projects, load_config, set_active_project
from cogni.convert import convert
from cogni.images import images
from cogni.ingest import ingest
from cogni.narrate import narrate
from cogni.review import review
from cogni.script import script
from cogni.script_review import revise_narration, script_review
from cogni.visuals import visuals

VOICES = [
    "en-GB-RyanNeural", "en-US-AndrewNeural", "en-US-GuyNeural",
    "en-GB-SoniaNeural", "en-US-AriaNeural",
]


def _audio_status_md() -> str:
    rows = store.audio_status()
    if not rows:
        return "_No scenes yet._"
    have = sum(1 for _, ok in rows if ok)
    marks = "  ".join(f"{i}{'🔊' if ok else '⬜'}" for i, ok in rows)
    return f"**Narrated: {have}/{len(rows)}**\n\n{marks}"


def _refresh():
    """Component values for the active book: grid, scene picker, audio status,
    gallery, preview storyboard, final video, visuals grid, review status."""
    ids = store.scene_ids()
    return (
        store.scenes_table(),
        gr.update(choices=ids, value=(ids[0] if ids else None)),
        _audio_status_md(),
        store.scene_images(),
        store.preview_html(),
        store.final_video_path(),
        store.visuals_table(),
        store.review_status_md(),
        store.narration_review_md(),
    )


def _hold_refresh():
    """No-op updates for the refresh_outputs slots — used by intermediate progress
    yields so streaming a status message doesn't recompute/clear the rest. Length
    must match refresh_outputs (and _refresh's tuple): 9."""
    return tuple(gr.update() for _ in range(9))


def switch_project(slug):
    if slug:
        set_active_project(slug)
    return _refresh()


def do_generate_script(file):
    if not file:
        yield (gr.update(), "⚠️ Upload a book file first.", *_hold_refresh())
        return
    try:  # surface stage errors in the UI, don't crash the app
        yield (gr.update(), "⏳ **1/3** Converting the book (document → text)…", *_hold_refresh())
        convert(file, force=True)
        yield (gr.update(), "⏳ **2/3** Ingesting the key ideas…", *_hold_refresh())
        ingest(force=True)
        yield (gr.update(), "⏳ **3/3** Writing the verdict script — the long step…", *_hold_refresh())
        script(force=True)
    except Exception as e:
        yield (gr.update(), f"❌ {e}", *_refresh())
        return
    slug = active_project()
    yield (
        gr.update(choices=list_projects(), value=slug),
        f"✅ Script ready for '{slug}' — {len(store.scene_ids())} scenes. Edit it, then narrate.",
        *_refresh(),
    )


def do_save_edits(df):
    try:
        rows = df.values.tolist() if hasattr(df, "values") else list(df)
        n = store.save_scene_edits(rows)
    except Exception as e:
        return f"❌ {e}", store.preview_html()
    return f"✅ Saved edits for {n} scenes. Re-run narration to update the audio.", store.preview_html()


def do_script_review():
    try:
        summary = script_review()
    except Exception as e:
        return f"❌ {e}", store.narration_review_md(), store.preview_html()
    if summary["flagged"]:
        msg = (f"⚠️ {summary['n_ok']}/{summary['n_scenes']} strong — flagged "
               f"{summary['flagged']}. Revise them (or edit), then re-review.")
    else:
        msg = f"✅ All {summary['n_scenes']} scenes read strong."
    return msg, store.narration_review_md(), store.preview_html()


def do_revise_narration():
    try:
        changed = revise_narration()
    except Exception as e:
        return store.scenes_table(), f"❌ {e}", store.narration_review_md(), store.preview_html()
    if not changed:
        msg = "Nothing flagged — run **Review narration** first."
    else:
        msg = f"✅ Rewrote scenes {changed}. Re-run review, then re-narrate those scenes."
    return store.scenes_table(), msg, store.narration_review_md(), store.preview_html()


def do_animate_all(flag):
    try:
        n = store.set_animate_all(flag)
    except Exception as e:
        return store.scenes_table(), f"❌ {e}", store.preview_html()
    verb = "Flagged all" if flag else "Cleared animate on"
    return (
        store.scenes_table(),
        f"✅ {verb} {n} scenes. Run **Images** to make the end keyframes, then animate.",
        store.preview_html(),
    )


def do_generate_visuals():
    try:
        visuals(force=True)
    except Exception as e:
        return store.visuals_table(), f"❌ {e}", store.review_status_md(), store.preview_html()
    return (
        store.visuals_table(),
        f"✅ Visual prompts ready for {len(store.scene_ids())} scenes. "
        "Review them (free) before generating images.",
        store.review_status_md(),
        store.preview_html(),
    )


def do_save_visual_edits(df):
    try:
        rows = df.values.tolist() if hasattr(df, "values") else list(df)
        n = store.save_visual_edits(rows)
    except Exception as e:
        return f"❌ {e}", store.review_status_md(), store.preview_html()
    return (
        f"✅ Saved prompt edits for {n} scenes. Re-run review to re-check them.",
        store.review_status_md(),
        store.preview_html(),
    )


def do_run_review():
    try:
        summary = review()
    except Exception as e:
        return f"❌ {e}", store.review_status_md(), store.preview_html()
    if summary["passed"]:
        msg = f"✅ Reviewed {summary['n_scenes']} scenes — all passed. Safe to generate images."
    else:
        msg = (f"⚠️ Reviewed {summary['n_scenes']} scenes — issues in {summary['failing']}. "
               "Fix the prompts below, or generate anyway (skips the gate).")
    return msg, store.review_status_md(), store.preview_html()


def do_generate_narration(voice):
    try:
        cfg = load_config()
        if voice:
            cfg["tts"]["voice"] = voice
        narrate(force=True, cfg=cfg)
    except Exception as e:
        return f"❌ {e}", _audio_status_md(), store.preview_html()
    return f"✅ Narrated all scenes with {voice}.", _audio_status_md(), store.preview_html()


def do_save_audio(scene_id, audio_path):
    if scene_id in (None, "") or not audio_path:
        return "⚠️ Pick a scene and upload audio first.", _audio_status_md(), store.preview_html()
    try:
        store.save_audio(int(scene_id), audio_path)
    except Exception as e:
        return f"❌ {e}", _audio_status_md(), store.preview_html()
    return f"✅ Overrode scene {int(scene_id)} audio.", _audio_status_md(), store.preview_html()


def do_generate_images():
    try:
        images()
    except Exception as e:
        return store.scene_images(), f"❌ {e}", store.preview_html()
    imgs = store.scene_images()
    return imgs, f"✅ {len(imgs)} images ready.", store.preview_html()


def do_generate_video():
    try:
        yield None, "⏳ **1/2** Generating images (only new/changed scenes cost)…", gr.update(), gr.update()
        images()
        yield None, "⏳ **2/2** Rendering the video (Ken Burns, subtitles, music)…", gr.update(), gr.update()
        final = assemble(force=True)
    except Exception as e:
        yield None, f"❌ {e}", store.preview_html(), store.final_video_path()
        return
    yield (str(final), f"✅ Rendered {final.name}. Also shown in Preview.",
           store.preview_html(), str(final))


def do_refresh_preview():
    return store.preview_html(), store.final_video_path()


with gr.Blocks(title="Project Cogni") as demo:
    gr.Markdown(
        "# Project Cogni\n"
        "Book → honest **verdict** script → TTS narration → 16:9 video. "
        "Not a summary — a point of view."
    )
    with gr.Row():
        book_dd = gr.Dropdown(
            label="Book", choices=list_projects(), value=active_project(),
            scale=4, info="Switch between books; upload a new one in the Book → Script tab.",
        )

    with gr.Tab("Preview"):
        gr.Markdown("Everything for the selected book — image, narration, caption, "
                    "audio/animate status — plus the final video once rendered.")
        prev_refresh = gr.Button("Refresh preview")
        prev_html = gr.HTML(store.preview_html())
        prev_video = gr.Video(value=store.final_video_path(), label="final.mp4")

    with gr.Tab("1. Book → Script"):
        book = gr.File(label="New book (PDF / epub / docx)", file_types=[".pdf", ".epub", ".docx", ".doc", ".txt", ".md"])
        gen_btn = gr.Button("Generate script (a few minutes)", variant="primary")
        gen_status = gr.Markdown()

    with gr.Tab("2. Edit script"):
        gr.Markdown("Edit the **Narration** (this is what the narrator reads) and tick "
                    "**Animate** for hero scenes. Re-narrate after editing.")
        grid = gr.Dataframe(
            headers=store.TABLE_HEADERS,
            datatype=["number", "str", "bool"],
            value=store.scenes_table(),
            interactive=True, wrap=True,
            column_widths=["6%", "82%", "12%"],
        )
        with gr.Row():
            save_btn = gr.Button("Save edits", variant="primary")
            anim_all_btn = gr.Button("Animate all scenes")
            anim_none_btn = gr.Button("Clear animate")
        save_status = gr.Markdown()
        gr.Markdown("### Narration review")
        gr.Markdown("Have the editor flag weak scenes (soft hook, filler, vague, "
                    "summary-not-verdict) — free — then rewrite just those.")
        with gr.Row():
            sreview_btn = gr.Button("Review narration (free)", variant="primary")
            revise_btn = gr.Button("Revise flagged scenes")
        nreview_md = gr.Markdown(store.narration_review_md())

    with gr.Tab("3. Visuals + Review"):
        gr.Markdown(
            "Generate two **keyframe** prompts (start / end) + a **motion** prompt per "
            "scene, then **review** them for free before spending any image/clip credits. "
            "Edit any prompt, save, and re-run review. Images stay blocked until review "
            "passes (or you generate anyway)."
        )
        with gr.Row():
            vis_btn = gr.Button("Generate visual prompts", variant="primary")
            review_btn = gr.Button("Run review (free, no credits)")
        vis_status = gr.Markdown()
        vis_grid = gr.Dataframe(
            headers=store.VISUALS_HEADERS,
            datatype=["number", "str", "str", "str"],
            value=store.visuals_table(),
            interactive=True, wrap=True,
            column_widths=["6%", "33%", "33%", "28%"],
        )
        vis_save_btn = gr.Button("Save prompt edits")
        gr.Markdown("### Review")
        review_md = gr.Markdown(store.review_status_md())

    with gr.Tab("4. Narration"):
        gr.Markdown("Generate the voiceover for every scene (edge-tts, free).")
        with gr.Row():
            voice_dd = gr.Dropdown(label="Voice", choices=VOICES, value=VOICES[0], scale=3)
        narr_btn = gr.Button("Generate narration", variant="primary")
        narr_status = gr.Markdown()
        audio_md = gr.Markdown(_audio_status_md())
        with gr.Accordion("Override one scene with your own audio (optional)", open=False):
            scene_pick = gr.Dropdown(label="Scene", choices=store.scene_ids(), value=(store.scene_ids()[0] if store.scene_ids() else None))
            rec = gr.Audio(label="Upload / record", sources=["upload", "microphone"], type="filepath")
            rec_btn = gr.Button("Save override")
            rec_status = gr.Markdown()

    with gr.Tab("5. Images"):
        gr.Markdown("Generate the **start** still per scene — plus an **end** keyframe for "
                    "any scene flagged *animate* (the two frames of its start→end clip). "
                    "Cached; blocked until **review** passes. OpenRouter "
                    "`gemini-2.5-flash-image`, ~$0.04/image.")
        img_btn = gr.Button("Generate images", variant="primary")
        img_status = gr.Markdown()
        gallery = gr.Gallery(value=store.scene_images(), label="Scene stills",
                             columns=3, height=560, object_fit="contain")

    with gr.Tab("6. Generate video"):
        gr.Markdown("Renders `output/final.mp4` from the stills (+ Ken Burns, captions, music) "
                    "and the narration. Scenes without audio use a short silent placeholder.")
        vid_btn = gr.Button("Generate video", variant="primary")
        vid_status = gr.Markdown()
        video = gr.Video(label="final.mp4")

    refresh_outputs = [grid, scene_pick, audio_md, gallery, prev_html, prev_video,
                       vis_grid, review_md, nreview_md]
    book_dd.change(switch_project, inputs=book_dd, outputs=refresh_outputs)
    gen_btn.click(do_generate_script, inputs=book, outputs=[book_dd, gen_status, *refresh_outputs])
    save_btn.click(do_save_edits, inputs=grid, outputs=[save_status, prev_html])
    anim_all_btn.click(lambda: do_animate_all(True), inputs=None, outputs=[grid, save_status, prev_html])
    anim_none_btn.click(lambda: do_animate_all(False), inputs=None, outputs=[grid, save_status, prev_html])
    sreview_btn.click(do_script_review, inputs=None, outputs=[save_status, nreview_md, prev_html])
    revise_btn.click(do_revise_narration, inputs=None, outputs=[grid, save_status, nreview_md, prev_html])
    vis_btn.click(do_generate_visuals, inputs=None, outputs=[vis_grid, vis_status, review_md, prev_html])
    vis_save_btn.click(do_save_visual_edits, inputs=vis_grid, outputs=[vis_status, review_md, prev_html])
    review_btn.click(do_run_review, inputs=None, outputs=[vis_status, review_md, prev_html])
    narr_btn.click(do_generate_narration, inputs=voice_dd, outputs=[narr_status, audio_md, prev_html])
    rec_btn.click(do_save_audio, inputs=[scene_pick, rec], outputs=[rec_status, audio_md, prev_html])
    img_btn.click(do_generate_images, inputs=None, outputs=[gallery, img_status, prev_html])
    vid_btn.click(do_generate_video, inputs=None, outputs=[video, vid_status, prev_html, prev_video])
    prev_refresh.click(do_refresh_preview, inputs=None, outputs=[prev_html, prev_video])


if __name__ == "__main__":
    demo.launch()
