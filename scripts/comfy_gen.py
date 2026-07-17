r"""Generate an image via a local ComfyUI server (txt2img: SDXL or Flux.1-dev).

Drives ComfyUI's HTTP API — no browser. Used first to prove the low-poly style, then
(once dialed) wired in as a free, local, consistent image provider for the pipeline.

Server: start it with
  D:\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\python_embeded\python.exe
      -s ComfyUI\main.py --port 8188

Usage:
  python scripts/comfy_gen.py --prompt "<text>" --out test.png [--seed 1] [--steps 7]
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

HOST = "127.0.0.1:8188"

# DreamShaper XL Turbo defaults (turbo = few steps, low cfg)
CKPT = "dreamshaperXL_turbo.safetensors"
NEG = ("photorealistic, realistic photo, photograph, text, words, letters, watermark, "
       "signature, blurry, noisy, jpeg artifacts, cluttered, busy background, ugly, deformed")

# Flux.1-dev (GGUF, fits our 12GB card) — the low-poly path. All files are ungated.
# Text encoders + VAE + LoRA are loaded by name from ComfyUI/models/{clip,vae,loras}.
FLUX_UNET = "flux1-dev-Q4_K_S.gguf"
FLUX_CLIP_L = "clip_l.safetensors"
FLUX_T5 = "t5xxl_fp8_e4m3fn.safetensors"
FLUX_VAE = "ae.safetensors"
FLUX_LORA = "low-poly-joy.safetensors"
FLUX_TRIGGER = "lo-ply_"  # low-poly-joy activation token (prepended to the prompt)


def build(pos: str, neg: str, seed: int, w: int, h: int, ckpt: str,
          steps: int, cfg: float, sampler: str, sched: str,
          lora: str = "", lora_str: float = 1.0) -> dict:
    """SDXL txt2img. SDXL runs full-precision fp16 on 12GB, so a style LoRA (node 2)
    patches model+clip cleanly — no quantization grain, unlike the Flux GGUF path."""
    m_clip = ["4", 1]  # checkpoint's CLIP, or the LoRA-patched CLIP if a lora is used
    m_model = ["4", 0]
    if lora:
        m_model, m_clip = ["2", 0], ["2", 1]
    wf = {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": m_clip}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": m_clip}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": sampler,
            "scheduler": sched, "denoise": 1.0,
            "model": m_model, "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "cogni", "images": ["8", 0]}},
    }
    if lora:
        wf["2"] = {"class_type": "LoraLoader", "inputs": {
            "model": ["4", 0], "clip": ["4", 1], "lora_name": lora,
            "strength_model": lora_str, "strength_clip": lora_str}}
    return wf


def build_flux(pos: str, seed: int, w: int, h: int, *, unet: str, clip_l: str, t5: str,
               vae: str, lora: str, lora_str: float, steps: int, guidance: float,
               sampler: str, sched: str, use_lora: bool = True) -> dict:
    """Flux.1-dev GGUF txt2img graph. Flux is guidance-distilled: cfg=1.0, so the
    negative prompt is unused. With use_lora, a model-only LoRA patches the transformer;
    without it, the model comes straight from the GGUF loader (style via prompt alone)."""
    model_src = ["13", 0] if use_lora else ["10", 0]
    wf = {
        "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": unet}},
        "11": {"class_type": "DualCLIPLoader",
               "inputs": {"clip_name1": clip_l, "clip_name2": t5, "type": "flux"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": vae}},
        "14": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["11", 0]}},
        "15": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["14", 0], "guidance": guidance}},
        "16": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["11", 0]}},
        "17": {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "18": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": steps, "cfg": 1.0, "sampler_name": sampler,
            "scheduler": sched, "denoise": 1.0,
            "model": model_src, "positive": ["15", 0], "negative": ["16", 0], "latent_image": ["17", 0]}},
        "19": {"class_type": "VAEDecode", "inputs": {"samples": ["18", 0], "vae": ["12", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "cogni_flux", "images": ["19", 0]}},
    }
    if use_lora:
        wf["13"] = {"class_type": "LoraLoaderModelOnly",
                    "inputs": {"model": ["10", 0], "lora_name": lora, "strength_model": lora_str}}
    return wf


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"http://{HOST}{path}", timeout=60) as r:
        return json.load(r)


def _run(wf: dict, out: Path, timeout_s: int) -> Path:
    """Submit a workflow, poll /history, download the SaveImage (node '9') output."""
    body = json.dumps({"prompt": wf}).encode()
    req = urllib.request.Request(f"http://{HOST}/prompt", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.load(r)
    if "prompt_id" not in resp:
        raise RuntimeError(f"ComfyUI rejected the workflow: {resp}")
    pid = resp["prompt_id"]

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        hist = _get(f"/history/{pid}")
        if pid in hist and hist[pid].get("outputs"):
            imgs = hist[pid]["outputs"].get("9", {}).get("images")
            if imgs:
                img = imgs[0]
                q = urllib.parse.urlencode({"filename": img["filename"],
                                            "subfolder": img.get("subfolder", ""),
                                            "type": img.get("type", "output")})
                with urllib.request.urlopen(f"http://{HOST}/view?{q}", timeout=180) as r:
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(r.read())
                return out
        time.sleep(1.5)
    raise TimeoutError(f"generation timed out after {timeout_s}s (prompt {pid})")


def generate(pos: str, out: Path, *, neg: str = NEG, seed: int = 1, w: int = 1344,
             h: int = 768, ckpt: str = CKPT, steps: int = 7, cfg: float = 2.0,
             sampler: str = "dpmpp_sde", sched: str = "karras", lora: str = "",
             lora_str: float = 1.0, timeout_s: int = 240) -> Path:
    return _run(build(pos, neg, seed, w, h, ckpt, steps, cfg, sampler, sched, lora, lora_str),
                out, timeout_s)


def generate_flux(pos: str, out: Path, *, seed: int = 1, w: int = 1344, h: int = 768,
                  unet: str = FLUX_UNET, clip_l: str = FLUX_CLIP_L, t5: str = FLUX_T5,
                  vae: str = FLUX_VAE, lora: str = FLUX_LORA, lora_str: float = 1.0,
                  steps: int = 20, guidance: float = 3.5, sampler: str = "euler",
                  sched: str = "simple", trigger: str = FLUX_TRIGGER, use_lora: bool = True,
                  timeout_s: int = 360) -> Path:
    """Flux.1-dev GGUF. With use_lora, applies the low-poly LoRA (prepends its trigger);
    without, style comes from the prompt alone. ~1-2 min/img warm on a 3060."""
    if use_lora and trigger and trigger.lower() not in pos.lower():
        pos = f"{trigger} {pos}"
    wf = build_flux(pos, seed, w, h, unet=unet, clip_l=clip_l, t5=t5, vae=vae, lora=lora,
                    lora_str=lora_str, steps=steps, guidance=guidance, sampler=sampler,
                    sched=sched, use_lora=use_lora)
    return _run(wf, out, timeout_s)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--flux", action="store_true", help="Flux.1-dev + low-poly LoRA (else SDXL)")
    ap.add_argument("--neg", default=NEG)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--steps", type=int, default=0, help="0 = provider default (SDXL 7 / Flux 20)")
    ap.add_argument("--cfg", type=float, default=2.0)
    ap.add_argument("--w", type=int, default=1344)
    ap.add_argument("--h", type=int, default=768)
    ap.add_argument("--ckpt", default=CKPT)
    ap.add_argument("--lora", default=FLUX_LORA)
    ap.add_argument("--lora-strength", type=float, default=1.0)
    ap.add_argument("--no-lora", action="store_true", help="Flux base only, style via prompt")
    ap.add_argument("--sdxl-lora", default="", help="SDXL style LoRA filename (SDXL path only)")
    ap.add_argument("--guidance", type=float, default=3.5)
    a = ap.parse_args()
    t = time.time()
    if a.flux:
        out = generate_flux(a.prompt, Path(a.out), seed=a.seed, w=a.w, h=a.h, lora=a.lora,
                            lora_str=a.lora_strength, guidance=a.guidance, steps=a.steps or 20,
                            use_lora=not a.no_lora)
    else:
        out = generate(a.prompt, Path(a.out), neg=a.neg, seed=a.seed, w=a.w, h=a.h,
                       ckpt=a.ckpt, steps=a.steps or 7, cfg=a.cfg,
                       lora=a.sdxl_lora, lora_str=a.lora_strength)
    print(f"wrote {out} in {time.time()-t:.1f}s")


if __name__ == "__main__":
    main()
