#!/usr/bin/env python3
"""Strict visual quality gate for Nova Shorts.
Rejects letterboxed/black-heavy scenes and near-static scenes before publication.
"""
from __future__ import annotations
import json, glob, subprocess, sys
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False)

def metric(path: Path):
    # blackdetect: reject clips with substantial black frames/areas.
    r = run(["ffmpeg","-hide_banner","-i",str(path),"-vf","blackdetect=d=0.4:pix_th=0.10","-an","-f","null","-"])
    lines = [x for x in r.stderr.splitlines() if "blackdetect" in x]
    black_time = 0.0
    for line in lines:
        try:
            d = float(line.split("black_duration:")[1].split()[0])
            black_time += d
        except Exception:
            pass
    duration = float(subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)
    ], text=True).strip())
    # Count meaningful scene changes. A moving clip normally has at least a little visual change.
    s = run(["ffmpeg","-hide_banner","-i",str(path),"-vf","select='gt(scene,0.025)',showinfo","-an","-f","null","-"])
    changes = sum("Parsed_showinfo" in line and "pts_time:" in line for line in s.stderr.splitlines())
    return duration, black_time, changes

def main():
    meta_path = Path(glob.glob("output/short_*.json")[0])
    meta = json.loads(meta_path.read_text())
    scenes = sorted(Path(meta_path.parent).glob("cinematic_*/*scene_*.mp4"))
    if len(scenes) != 5:
        raise SystemExit(f"FAIL: expected 5 rendered scenes, found {len(scenes)}")
    bad=[]
    for p in scenes:
        duration, black, changes = metric(p)
        if black > max(0.8, duration * 0.10):
            bad.append(f"{p.name}: black/letterbox {black:.2f}s/{duration:.2f}s")
        if changes < 2:
            bad.append(f"{p.name}: insufficient visual motion/change ({changes} scene changes)")
    if bad:
        print("\n".join(["QUALITY GATE FAILED:"] + bad))
        sys.exit(1)
    meta["visual_quality_gate"] = "passed"
    meta["scene_checks"] = "blackdetect + scene-change analysis"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("QUALITY GATE PASSED: 5 scenes, no substantial black/letterbox, motion detected in every scene.")

if __name__ == "__main__":
    main()
