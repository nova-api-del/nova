#!/usr/bin/env python3
"""Create one English vertical Short using Edge TTS, Pillow and FFmpeg.
No paid AI API or stock-footage key is required.
"""
from datetime import datetime, timezone
from pathlib import Path
import asyncio, json, math, subprocess, textwrap

from PIL import Image, ImageDraw, ImageFont
import edge_tts

OUT = Path("output")
OUT.mkdir(exist_ok=True)
W, H = 1080, 1920
VOICE = "en-US-GuyNeural"

TOPICS = [
    ("The Ocean Has a Hidden World", [
        "The ocean is the largest living space on Earth.",
        "More than eighty percent of it has never been mapped in detail.",
        "Some deep-sea animals make their own light.",
        "Scientists discover new marine species every year.",
        "The deep ocean is still one of our planet's greatest mysteries."
    ]),
    ("Space Is Stranger Than You Think", [
        "A day on Venus lasts longer than its year.",
        "That happens because Venus rotates extremely slowly.",
        "Neutron stars are so dense that a tiny amount weighs billions of tons.",
        "And space is not completely silent in every scientific sense.",
        "The universe keeps surprising us."
    ]),
    ("Amazing Facts About Your Brain", [
        "Your brain contains roughly eighty-six billion neurons.",
        "It constantly changes as you learn and practice.",
        "Sleep helps your brain organize memories.",
        "Your brain also uses a remarkable amount of your body's energy.",
        "The most powerful learning tool is consistent practice."
    ]),
    ("Animals With Incredible Abilities", [
        "Octopuses have three hearts and blue blood.",
        "Some birds can navigate using Earth's magnetic field.",
        "A tardigrade can survive conditions that would kill most life.",
        "Dolphins use unique whistles that work like individual names.",
        "Nature is full of extraordinary engineering."
    ]),
    ("Everyday Science That Feels Like Magic", [
        "A lightning bolt can heat the air hotter than the Sun's surface.",
        "Water can boil and freeze at the same time under special conditions.",
        "Glass is an amorphous solid, not a slow-flowing liquid.",
        "Your phone uses radio waves to communicate across long distances.",
        "Science explains the magic hiding in everyday life."
    ]),
    ("The World's Most Surprising Places", [
        "Antarctica is technically the world's largest desert.",
        "The Atacama Desert is one of the driest places on Earth.",
        "Some forests create their own local rainfall patterns.",
        "There are lakes beneath the ice in Antarctica.",
        "Our planet is far more diverse than it first appears."
    ]),
    ("How Technology Changed the World", [
        "The first web page went online in 1991.",
        "Modern smartphones contain billions of tiny transistors.",
        "GPS works by measuring signals from satellites.",
        "Artificial intelligence learns patterns from data.",
        "Technology advances when people keep asking better questions."
    ])
]

def run(cmd):
    subprocess.run(cmd, check=True)

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(draw, text, fnt, max_width):
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textbbox((0,0), trial, font=fnt)[2] <= max_width:
            line = trial
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    return lines

def make_card(title, sentence, idx, total, path):
    im = Image.new("RGB", (W,H))
    px = im.load()
    for y in range(H):
        t = y / H
        c = (int(8+15*t), int(18+20*t), int(48+38*t))
        for x in range(W):
            glow = max(0, 1 - math.sqrt(((x-W*.78)/(W*.9))**2 + ((y-H*.18)/(H*.5))**2))
            px[x,y] = (min(255,int(c[0]+glow*25)), min(255,int(c[1]+glow*35)), min(255,int(c[2]+glow*65)))
    d = ImageDraw.Draw(im)
    # Decorative bars and section indicator
    d.rounded_rectangle((72,100,1008,112), radius=6, fill=(68,190,255))
    d.text((78,165), "NOVA  •  DAILY DISCOVERY", font=font( thirty:=30, True), fill=(125,210,255))
    title_font = font(62, True)
    title_lines = wrap(d, title, title_font, 900)
    y = 290
    for line in title_lines[:3]:
        d.text((78,y), line, font=title_font, fill=(255,255,255), stroke_width=1, stroke_fill=(0,0,0))
        y += 82
    d.rounded_rectangle((72,690,1008,1510), radius=42, fill=(15,31,69), outline=(75,125,190), width=3)
    body_font = font(55, True)
    lines = wrap(d, sentence, body_font, 820)
    block_h = len(lines)*78
    yy = 1100-block_h//2
    for line in lines:
        box = d.textbbox((0,0), line, font=body_font)
        d.text(((W-(box[2]-box[0]))//2, yy), line, font=body_font, fill=(255,255,255))
        yy += 78
    d.text((78,1610), f"FACT {idx+1} / {total}", font=font(34,True), fill=(125,210,255))
    d.rounded_rectangle((78,1690,1002,1710), radius=10, fill=(45,62,100))
    d.rounded_rectangle((78,1690,78+int(924*(idx+1)/total),1710), radius=10, fill=(68,190,255))
    d.text((78,1780), "FOLLOW FOR MORE QUICK DISCOVERIES", font=font(30,True), fill=(205,220,245))
    im.save(path, quality=92)

async def main():
    day = datetime.now(timezone.utc).timetuple().tm_yday
    title, facts = TOPICS[(day-1) % len(TOPICS)]
    # Expand the narration so each daily video is close to one minute.
    expansions = [
        "Scientists use evidence like this to understand how the natural world works, and every new discovery can change what we thought we knew.",
        "The details matter because small clues often reveal much bigger patterns, helping researchers connect observations into a clearer picture.",
        "It is a reminder that the world is more complex than it first appears, and there is still so much left to explore.",
        "Researchers keep studying questions like this because better explanations can lead to new discoveries and useful real-world knowledge.",
        "So take a second to think about it: something happening far beyond our everyday view can still teach us something important."
    ]
    text = "Welcome to Nova Daily Discovery. " + " ".join(
        f"{fact} {expansions[i]}" for i, fact in enumerate(facts)
    ) + " Follow Nova for more fascinating discoveries tomorrow."
    audio = OUT / "voice.mp3"
    communicate = edge_tts.Communicate(text, VOICE, rate="-8%", volume="+0%")
    await communicate.save(str(audio))
    probe = subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(audio)], text=True)
    duration = float(probe.strip())
    # Split total narration evenly over five readable scene cards.
    each = duration / len(facts)
    lines = []
    for i, fact in enumerate(facts):
        img = OUT / f"scene_{i:02d}.jpg"
        make_card(title, fact, i, len(facts), img)
        lines += [f"file '{img.resolve()}'", f"duration {each:.3f}"]
    # concat demuxer needs the final image repeated.
    lines.append(f"file '{(OUT / f'scene_{len(facts)-1:02d}.jpg').resolve()}'")
    concat = OUT / "scenes.txt"
    concat.write_text("\n".join(lines), encoding="utf-8")
    # Render a vertical 1080x1920 mp4 with narration.
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-i",str(audio),
         "-vf","fps=30,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","23",
         "-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(OUT/"nova_short.mp4")])
    metadata = {"title": title, "description": "Five fascinating facts in about one minute. Follow Nova for more daily discoveries. #shorts #facts #science",
                "date_utc": datetime.now(timezone.utc).isoformat(), "duration_seconds": round(duration,2),
                "voice": VOICE, "language": "en"}
    (OUT/"metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata))

if __name__ == "__main__":
    asyncio.run(main())
