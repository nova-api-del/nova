#!/usr/bin/env python3
"""Optional local Wan2.1 T2V fallback for Nova.

This module is deliberately optional: GitHub-hosted CPU runners should not try to
download/run a multi-GB video model. When a CUDA runner has WAN2.1_T2V_MODEL_DIR,
it generates a short clip; otherwise Nova continues with real-footage providers.
"""
from __future__ import annotations
import os, shutil, subprocess
from pathlib import Path

def available() -> bool:
    return bool(os.getenv("WAN2_1_MODEL_DIR")) and shutil.which("python") is not None

def generate(prompt: str, out: Path, seconds: int = 5):
    model = os.getenv("WAN2_1_MODEL_DIR")
    if not model:
        return None
    if not shutil.which("python"):
        return None
    wan_root = os.getenv("WAN2_1_REPO", "Wan2.1")
    if not Path(wan_root).exists():
        return None
    raw = out.with_suffix(".raw.mp4")
    cmd = [
        "python", str(Path(wan_root) / "generate.py"),
        "--task", "t2v-1.3B",
        "--size", os.getenv("WAN2_1_SIZE", "832*480"),
        "--ckpt_dir", model,
        "--offload_model", "True",
        "--t5_cpu",
        "--sample_shift", "8",
        "--sample_guide_scale", "6",
        "--prompt", prompt,
        "--save_file", str(raw),
    ]
    try:
        subprocess.run(cmd, check=True, timeout=int(os.getenv("WAN2_1_TIMEOUT", "900")))
        if not raw.exists():
            return None
        subprocess.run([
            "ffmpeg","-y","-i",str(raw),"-t",str(seconds),
            "-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
            "-an","-c:v","libx264","-crf","21","-pix_fmt","yuv420p",str(out)
        ], check=True, timeout=180)
        return out if out.exists() else None
    except Exception:
        raw.unlink(missing_ok=True)
        out.unlink(missing_ok=True)
        return None
