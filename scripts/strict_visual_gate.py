#!/usr/bin/env python3
"""Strict visual quality gate for Nova Shorts.
Checks portrait format, black frames, and genuinely frozen footage.
Scene-cut detection is deliberately not used: a continuous moving shot is valid.
"""
from __future__ import annotations
import glob, json, re, subprocess, sys
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False)

def probe_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nw=1:nk=1",str(path)
    ], text=True).strip())

def inspect_scene(path: Path):
    duration = probe_duration(path)
    black = run([
        "ffmpeg","-hide_banner","-i",str(path),
        "-vf","blackdetect=d=0.35:pix_th=0.10",
        "-an","-f","null","-"
    ])
    if black.returncode != 0:
        raise RuntimeError(f"{path.name}: ffmpeg blackdetect failed")
    black_time = 0.0
    for line in black.stderr.splitlines():
        match = re.search(r"black_duration:\s*([0-9.]+)", line)
        if match:
            black_time += float(match.group(1))

    # Detect long frozen sections, not scene cuts. This allows one continuous
    # tracking shot while rejecting a still image masquerading as footage.
    frozen = run([
        "ffmpeg","-hide_banner","-i",str(path),
        "-vf","freezedetect=n=-55dB:d=2",
        "-an","-f","null","-"
    ])
    if frozen.returncode != 0:
        raise RuntimeError(f"{path.name}: ffmpeg freezedetect failed: {frozen.stderr[-800:]}")
    freeze_time = 0.0
    starts, ends = [], []
    for line in frozen.stderr.splitlines():
        match = re.search(r"freeze_duration:\s*([0-9.]+)", line)
        if match:
            freeze_time += float(match.group(1))
        match = re.search(r"freeze_start:\s*([0-9.]+)", line)
        if match:
            starts.append(float(match.group(1)))
        match = re.search(r"freeze_end:\s*([0-9.]+)", line)
        if match:
            ends.append(float(match.group(1)))
    # A freeze that continues through EOF has freeze_start but no freeze_end.
    if len(starts) > len(ends):
        freeze_time += max(0.0, duration - starts[-1])
    return duration, black_time, freeze_time

def main():
    metadata_files = sorted(glob.glob("output/short_*.json"))
    if not metadata_files:
        raise SystemExit("FAIL: no output/short_*.json metadata found")
    failures=[]
    for raw in metadata_files:
        meta_path=Path(raw)
        meta=json.loads(meta_path.read_text(encoding="utf-8"))
        stem=meta_path.stem
        video=meta_path.with_suffix(".mp4")
        if not video.exists():
            video=meta_path.parent / (stem + ".mp4")
        if not video.exists():
            failures.append(f"{stem}: matching MP4 missing")
            continue
        info=json.loads(subprocess.check_output([
            "ffprobe","-v","error","-show_entries",
            "stream=codec_type,width,height","-of","json",str(video)
        ],text=True))
        v=next((x for x in info.get("streams",[]) if x.get("codec_type")=="video"),{})
        has_audio=any(x.get("codec_type")=="audio" for x in info.get("streams",[]))
        if (v.get("width"),v.get("height")) != (1080,1920):
            failures.append(f"{video.name}: expected 1080x1920 portrait video")
        if not has_audio:
            failures.append(f"{video.name}: narration/audio stream missing")
        try:
            slot_number = int(stem.rsplit("_", 1)[1])
            scene_dirs = sorted(meta_path.parent.glob(f"cinematic_*_{slot_number}"))
            scenes = sorted(scene_dirs[-1].glob("scene_*.mp4")) if scene_dirs else []
        except (ValueError, IndexError):
            scenes = []
        if len(scenes)!=5:
            failures.append(f"{stem}: expected 5 rendered scenes for this video, found {len(scenes)}")
            continue
        voice_duration = float(meta.get("duration_seconds", 0))
        if not 45 <= voice_duration <= 64:
            failures.append(f"{stem}: expected 45-64 seconds, got {voice_duration:.1f}s")
        for scene in scenes:
            try:
                duration,black,freeze=inspect_scene(scene)
                if black > max(0.8,duration*0.10):
                    failures.append(f"{scene.name}: excessive black frames ({black:.2f}s/{duration:.2f}s)")
                if duration > 0 and freeze > duration*0.90:
                    failures.append(f"{scene.name}: appears frozen ({freeze:.2f}s/{duration:.2f}s)")
            except Exception as exc:
                failures.append(f"{scene.name}: inspection error: {exc}")
        sources=meta.get("sources",[])
        if len(sources)!=5:
            failures.append(f"{stem}: expected five attributed sources")
        sourced=[x for x in sources if x.get("kind") not in ("ai_generated_image_animated",)]
        video_sources=[x for x in sources if x.get("kind") not in ("ai_generated_image_animated","licensed_image_animated")]
        if len(sourced)<3:
            failures.append(f"{stem}: fewer than three distinct licensed non-AI visual assets")
        if len(video_sources)<3:
            failures.append(f"{stem}: fewer than three actual moving-video sources found")
        if sum(x.get("kind")=="ai_generated_image_animated" for x in sources)>2:
            failures.append(f"{stem}: more than two AI-generated still scenes")

    if failures:
        print("QUALITY GATE FAILED:\n" + "\n".join(failures))
        sys.exit(1)
    for raw in metadata_files:
        p=Path(raw)
        meta=json.loads(p.read_text(encoding="utf-8"))
        meta["visual_quality_gate"]="passed"
        meta["scene_checks"]="black-frame + frozen-footage analysis"
        p.write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print(f"QUALITY GATE PASSED: {len(metadata_files)} video(s); portrait, audio, five scenes, black-frame and freeze checks passed.")

if __name__ == "__main__":
    main()
