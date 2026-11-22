#!/usr/bin/env python3
"""Render output/story/story.json + scene images into a 1080p video with English narration and captions.

Images: FRAMES_DIR/scene_01.png ... scene_NN.png (and optional thumbnail.png).
Only your own generated images are used; a missing image stops the build.
"""
from __future__ import annotations
import asyncio, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "story"
FRAMES = Path(os.getenv("FRAMES_DIR", str(OUT / "frames")))
VOICE = os.getenv("TTS_VOICE", "en-US-AndrewNeural")
TTS_RATE = os.getenv("TTS_RATE", "-3%")
W, H, FPS, TAIL = 1920, 1080, 30, 0.35


def run(cmd):
    subprocess.run(cmd, check=True)


def probe_duration(path: Path) -> float:
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        text=True).strip())


async def synth(text: str, mp3: Path) -> list[dict]:
    """English neural TTS with word timings (Edge TTS, no API key)."""
    import edge_tts
    comm = edge_tts.Communicate(text, VOICE, rate=TTS_RATE, boundary="WordBoundary")
    words = []
    with mp3.open("wb") as handle:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                handle.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({"start": chunk["offset"] / 1e7,
                              "end": (chunk["offset"] + chunk["duration"]) / 1e7, "text": chunk["text"]})
    if not words:
        raise RuntimeError("TTS returned no word timings")
    return words


def write_ass(words: list[dict], path: Path):
    def t(v):
        cs = max(0, round(v * 100))
        return f"{cs // 360000}:{(cs // 6000) % 60:02d}:{(cs // 100) % 60:02d}.{cs % 100:02d}"
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 5 or len(" ".join(x["text"] for x in cur)) >= 32 or re.search(r"[.!?]$", w["text"]):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Cap,DejaVu Sans,62,&H00FFFFFF,&H0000D7FF,&H00101010,&H99000000,-1,0,0,0,100,100,0,0,1,5,2,2,60,60,70,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for g in groups:
        text = " ".join(x["text"] for x in g).replace("{", "(").replace("}", ")")
        lines.append(f"Dialogue: 0,{t(g[0]['start'])},{t(g[-1]['end'] + 0.10)},Cap,,0,0,0,,{text}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def motion(index: int, frames: int) -> str:
    f = max(1, frames)
    ctr_x, ctr_y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    kind = index % 4
    if kind == 0:
        return f"z='1+0.10*on/{f}':x='{ctr_x}':y='{ctr_y}'"
    if kind == 1:
        return f"z='1.10-0.10*on/{f}':x='{ctr_x}':y='{ctr_y}'"
    if kind == 2:
        return f"z='1.10':x='(iw-iw/zoom)*on/{f}':y='{ctr_y}'"
    return f"z='1.10':x='(iw-iw/zoom)*(1-on/{f})':y='{ctr_y}'"


def render_scene(index: int, image: Path, mp3: Path, ass: Path, dest: Path, seconds: float):
    frames = round(seconds * FPS)
    vf = (f"scale=2400:1350:force_original_aspect_ratio=increase,crop=2400:1350,"
          f"zoompan={motion(index, frames)}:d={frames}:s={W}x{H}:fps={FPS},"
          f"setsar=1,format=yuv420p,ass='{ass.as_posix()}'")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(image), "-i", str(mp3),
         "-vf", vf, "-af", f"apad=whole_dur={seconds:.3f}", "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-t", f"{seconds:.3f}", str(dest)])


def make_pingpong(src: Path, dst: Path):
    """Forward-then-backward copy of a short clip so looping it has no visible jump."""
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
         "-filter_complex", "[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0[v]",
         "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", str(dst)])


def render_video_scene(clip: Path, mp3: Path, ass: Path, dest: Path, seconds: float, work: Path, n: int):
    """Scene built from an AI-animated clip: ping-pong loop to the narration length, then captions."""
    loop_src = work / f"pingpong_{n:02d}.mp4"
    make_pingpong(clip, loop_src)
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"fps={FPS},setsar=1,format=yuv420p,ass='{ass.as_posix()}'")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", str(loop_src),
         "-i", str(mp3), "-vf", vf, "-af", f"apad=whole_dur={seconds:.3f}", "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-t", f"{seconds:.3f}", str(dest)])


def make_thumbnail(story: dict, frames: Path, dest: Path):
    from PIL import Image, ImageDraw, ImageFont
    src = frames / "thumbnail.png"
    if not src.exists():
        src = frames / "scene_01.png"
    im = Image.open(src).convert("RGB")
    ratio = max(1280 / im.width, 720 / im.height)
    im = im.resize((round(im.width * ratio), round(im.height * ratio)), Image.LANCZOS)
    left, top = (im.width - 1280) // 2, (im.height - 720) // 2
    im = im.crop((left, top, left + 1280, top + 720))
    draw = ImageDraw.Draw(im)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    text = str(story.get("thumb_text", "")).upper()[:28]
    size = 150
    font = ImageFont.truetype(font_path, size) if Path(font_path).exists() else ImageFont.load_default()
    while size > 60 and draw.textbbox((0, 0), text, font=font)[2] > 1160:
        size -= 8
        font = ImageFont.truetype(font_path, size)
    draw.text((50, 720 - size - 50), text, font=font, fill=(255, 221, 0), stroke_width=8, stroke_fill=(0, 0, 0))
    im.save(dest, "JPEG", quality=90)


def main() -> int:
    story = json.loads((OUT / "story.json").read_text(encoding="utf-8"))
    scenes = story["scenes"]
    work = OUT / "work"
    work.mkdir(parents=True, exist_ok=True)
    clips = []
    for i, scene in enumerate(scenes):
        n = i + 1
        image = next((p for p in (FRAMES / f"scene_{n:02d}.png", FRAMES / f"scene_{n:02d}.jpg") if p.exists()), None)
        if image is None:
            raise SystemExit(f"Missing image for scene {n} in {FRAMES}")
        animated = FRAMES / f"scene_{n:02d}.mp4"  # optional AI-animated clip (see notebook step 2b)
        mp3, ass, clip = work / f"voice_{n:02d}.mp3", work / f"cap_{n:02d}.ass", work / f"scene_{n:02d}.mp4"
        words = asyncio.run(synth(scene["narration"], mp3))
        write_ass(words, ass)
        seconds = probe_duration(mp3) + TAIL
        if animated.exists():
            render_video_scene(animated, mp3, ass, clip, seconds, work, n)
        else:
            render_scene(i, image, mp3, ass, clip, seconds)
        clips.append(clip)
        print(f"[RENDER] scene {n}/{len(scenes)}", flush=True)
    listing = work / "clips.txt"
    listing.write_text("".join(f"file '{c.resolve().as_posix()}'\n" for c in clips), encoding="utf-8")
    final = OUT / "video.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-c", "copy", "-movflags", "+faststart", str(final)])
    make_thumbnail(story, FRAMES, OUT / "thumbnail.jpg")
    streams = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(final)], text=True))["streams"]
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    if (video.get("width"), video.get("height")) != (W, H) or not any(s.get("codec_type") == "audio" for s in streams):
        raise SystemExit("Rendered video failed the format check")
    seconds = probe_duration(final)
    print(f"[RENDER] DONE {final} ({seconds / 60:.1f} min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
