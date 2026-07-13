"""Project Cogni — web UI (thin wrapper over the pipeline stages).

Flow: upload a book -> generate script -> edit the Khmer + tick Animate ->
record one clip per scene -> Generate video -> preview & download.

No real logic lives here — every button calls a stage function in cogni/.
Run:  python app.py   (opens http://127.0.0.1:7860)
"""

from __future__ import annotations

import gradio as gr

from cogni import store
from cogni.assemble import assemble
from cogni.convert import convert
from cogni.images import images
from cogni.ingest import ingest
from cogni.script import script


def _audio_status_md() -> str:
    rows = store.audio_status()
    if not rows:
        return "_No scenes yet._"
    have = sum(1 for _, ok in rows if ok)
    marks = "  ".join(f"{i}{'✅' if ok else '⬜'}" for i, ok in rows)
    return f"**Recordings: {have}/{len(rows)}**\n\n{marks}"


def do_generate_script(file):
    if not file:
        return ("⚠️ Upload a book file first.", gr.update(), "", gr.update(), _audio_status_md())
    try:
        convert(file, force=True)
        ingest(force=True)
        script(force=True)
    except Exception as e:  # surface stage errors in the UI, don't crash the app
        return (f"❌ {e}", gr.update(), "", gr.update(), _audio_status_md())
    ids = store.scene_ids()
    return (
        f"✅ Script ready — {len(ids)} scenes. Edit the Khmer below, then record.",
        store.scenes_table(),
        store.recording_script_text(),
        gr.update(choices=ids, value=(ids[0] if ids else None)),
        _audio_status_md(),
    )


def do_save_edits(df):
    try:
        rows = df.values.tolist() if hasattr(df, "values") else list(df)
        n = store.save_scene_edits(rows)
    except Exception as e:
        return f"❌ {e}"
    return f"✅ Saved edits for {n} scenes."


def do_save_audio(scene_id, audio_path):
    if scene_id in (None, "") or not audio_path:
        return "⚠️ Pick a scene and record/upload audio first.", _audio_status_md()
    try:
        store.save_audio(int(scene_id), audio_path)
    except Exception as e:
        return f"❌ {e}", _audio_status_md()
    return f"✅ Saved recording for scene {int(scene_id)}.", _audio_status_md()


def do_generate_images():
    try:
        images()
    except Exception as e:
        return store.scene_images(), f"❌ {e}"
    imgs = store.scene_images()
    return imgs, f"✅ {len(imgs)} images ready."


def do_generate_video():
    try:
        images()
        final = assemble(force=True)
    except Exception as e:
        return None, f"❌ {e}"
    return str(final), f"✅ Rendered {final.name}. Preview below; download from the player."


with gr.Blocks(title="Project Cogni") as demo:
    gr.Markdown(
        "# Project Cogni\n"
        "Book → English+Khmer script → **your** recorded voice → 16:9 video. "
        "The pipeline automates assembly only; the book, the voice, and the Khmer are yours."
    )

    with gr.Tab("1. Book → Script"):
        book = gr.File(label="Book (PDF / epub / docx)", file_types=[".pdf", ".epub", ".docx", ".doc", ".txt", ".md"])
        gen_btn = gr.Button("Generate script (a few minutes)", variant="primary")
        gen_status = gr.Markdown()

    with gr.Tab("2. Edit Khmer"):
        gr.Markdown("Edit the **Khmer (edit me)** column and tick **Animate** for hero scenes. English is reference only.")
        grid = gr.Dataframe(
            headers=store.TABLE_HEADERS,
            datatype=["number", "str", "str", "bool"],
            value=store.scenes_table(),
            interactive=True,
            wrap=True,
            column_widths=["6%", "40%", "42%", "12%"],
        )
        save_btn = gr.Button("Save edits", variant="primary")
        save_status = gr.Markdown()
        gr.Markdown("### Recording script (copy the Khmer to read)")
        rec_script = gr.Code(value=store.recording_script_text(), label="recording_script.txt")

    with gr.Tab("3. Record audio"):
        gr.Markdown("Record (or upload) one clip per scene. Saved as `audio/scene_XXX.wav`.")
        with gr.Row():
            scene_pick = gr.Dropdown(label="Scene", choices=store.scene_ids(), value=(store.scene_ids()[0] if store.scene_ids() else None))
        rec = gr.Audio(label="Record or upload", sources=["microphone", "upload"], type="filepath")
        rec_btn = gr.Button("Save recording", variant="primary")
        rec_status = gr.Markdown()
        audio_md = gr.Markdown(_audio_status_md())

    with gr.Tab("4. Images"):
        gr.Markdown("Generate a still per scene (cached — only new/changed scenes cost). "
                    "OpenRouter `gemini-2.5-flash-image`, ~$0.04/image.")
        img_btn = gr.Button("Generate images", variant="primary")
        img_status = gr.Markdown()
        gallery = gr.Gallery(value=store.scene_images(), label="Scene stills",
                             columns=3, height=560, object_fit="contain")

    with gr.Tab("5. Generate video"):
        gr.Markdown("Renders `output/final.mp4` from the stills (+ Ken Burns, captions, music) "
                    "and your recordings. Scenes without a recording use a short silent placeholder.")
        vid_btn = gr.Button("Generate video", variant="primary")
        vid_status = gr.Markdown()
        video = gr.Video(label="final.mp4")

    gen_btn.click(do_generate_script, inputs=book,
                  outputs=[gen_status, grid, rec_script, scene_pick, audio_md])
    save_btn.click(do_save_edits, inputs=grid, outputs=save_status)
    rec_btn.click(do_save_audio, inputs=[scene_pick, rec], outputs=[rec_status, audio_md])
    img_btn.click(do_generate_images, inputs=None, outputs=[gallery, img_status])
    vid_btn.click(do_generate_video, inputs=None, outputs=[video, vid_status])


if __name__ == "__main__":
    demo.launch()
