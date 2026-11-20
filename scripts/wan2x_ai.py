#!/usr/bin/env python3
"""Optional local AI-video backend for Nova.

Uses Wan2.1 T2V-1.3B when a CUDA GPU is available. This is deliberately
separate from the real-footage pipeline so GitHub-hosted CPU runners never
pretend they can cheaply generate AI video.
"""
from __future__ import annotations
import argparse, os, shutil, subprocess, sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--prompt",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--model",default=os.getenv("WAN_MODEL_DIR","models/Wan2.1-T2V-1.3B"))
    p.add_argument("--size",default="832*480")
    a=p.parse_args()
    if shutil.which("nvidia-smi") is None:
        raise SystemExit("NO_GPU: Wan2.1 AI generation requires CUDA/NVIDIA; use real-footage fallback on GitHub-hosted runners.")
    model=Path(a.model)
    if not model.exists():
        raise SystemExit(f"MODEL_NOT_FOUND: {model}")
    cmd=[
        sys.executable,"Wan2.1/generate.py","--task","t2v-1.3B",
        "--size",a.size,"--ckpt_dir",str(model),
        "--offload_model","True","--t5_cpu","--sample_shift","8",
        "--sample_guide_scale","6","--prompt",a.prompt,
    ]
    subprocess.run(cmd,check=True)
    candidates=sorted(Path(".").glob("*.mp4"),key=lambda x:x.stat().st_mtime,reverse=True)
    if not candidates:
        raise SystemExit("AI_GENERATION_FAILED: Wan2.1 produced no MP4")
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(candidates[0],a.out)

if __name__=="__main__":
    main()
