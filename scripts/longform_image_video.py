#!/usr/bin/env python3
"""Render a five-minute English image-led Nova documentary.

Uses AI-generated stills when POLLINATIONS_API_KEY is configured; otherwise
uses NASA/Wikimedia images with attribution metadata. Every still gets a
slow Ken Burns camera move, narration, and word-timed captions.
"""
from __future__ import annotations
import asyncio, json, math, os, re, subprocess
from pathlib import Path
from datetime import datetime, timezone

import edge_tts
from PIL import Image, ImageDraw, ImageFont

from cinematic_shorts import find_image, generate_ai_image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "longform"
SCENES = [
    ("A World Beneath the Waves", "deep ocean blue water sunlight rays from surface underwater", "Beneath the ocean surface lies a world larger than all the continents combined. From bright coastal reefs to plains of darkness, the sea contains environments that are still difficult for humans to reach."),
    ("Where Sunlight Disappears", "deep ocean twilight zone underwater descending sunlight", "Sunlight fades quickly as depth increases. Below the sunlit zone, the water becomes cold and dim. Farther down, sunlight disappears completely, and animals must survive without the energy that supports most familiar ecosystems."),
    ("The Pressure of the Deep", "deep sea trench underwater submersible dramatic scale", "The pressure in the deep ocean rises roughly one atmosphere every ten metres. At the deepest trenches, it is more than a thousand times the pressure at the surface. Human divers cannot reach these places, so researchers rely on specially engineered submersibles and robots."),
    ("Life Makes Its Own Light", "bioluminescent jellyfish deep sea glowing blue black water", "In the darkness, some animals create their own light through bioluminescence. A flash can attract prey, confuse a predator, or help an animal recognize another of its kind. The deep sea is not empty darkness. It can be filled with living signals."),
    ("The Strange Shapes of Deep-Sea Life", "anglerfish deep sea animal bioluminescent macro underwater", "Many deep-sea animals look unfamiliar because evolution has shaped them for a world unlike ours. Some have enormous mouths, sensitive organs, transparent bodies, or eyes adapted to faint flashes. Their forms are solutions to the challenges of finding food and avoiding danger."),
    ("Coral Cities in the Dark", "deep sea cold water coral reef underwater marine ecosystem", "Not all deep-sea habitats are barren. Cold-water corals can build complex structures far below the reach of sunlight. These reefs provide shelter and feeding grounds for fish, crustaceans, and many other organisms."),
    ("Hydrothermal Vents", "hydrothermal vent black smoker deep ocean underwater", "On the ocean floor, hydrothermal vents release mineral-rich hot water. Entire communities gather around them. Instead of depending directly on sunlight, microbes use chemical energy to build the foundation of a food web. It is one of the clearest examples of life thriving in an unexpected way."),
    ("The Ocean's Great Migrators", "whale migration underwater humpback whale ocean", "The deep ocean is also connected to the surface by migration. Whales and other animals travel through enormous distances, carrying nutrients between feeding and breeding areas. Their journeys connect ecosystems that may be thousands of kilometres apart."),
    ("A Hidden World of Sound", "underwater hydrophone ocean research scientist equipment", "Sound travels efficiently through seawater, allowing animals to communicate over long distances. Researchers use hydrophones to listen to whales, dolphins, earthquakes, and the movement of ice. These recordings reveal activity that cameras alone could never capture."),
    ("Robots Explore the Unreachable", "remotely operated vehicle ROV deep ocean exploration lights", "Remotely operated vehicles carry cameras, lights, and scientific instruments into places too dangerous for people. Their cables connect them to ships at the surface, allowing scientists to guide them while watching discoveries in real time."),
    ("Mapping the Seafloor", "multibeam sonar ocean floor mapping research ship", "Much of the seafloor has not been mapped in high detail. Ships use sonar to measure depth and build maps of underwater mountains, valleys, and trenches. Better maps help researchers understand ocean circulation, geology, habitats, and natural hazards."),
    ("The Ocean and the Climate", "ocean currents aerial sea ice climate science", "The ocean stores and moves enormous amounts of heat. Currents redistribute energy around the planet, while marine organisms take part in the global carbon cycle. Understanding the sea is therefore essential to understanding Earth's climate."),
    ("Fragile Deep-Sea Ecosystems", "deep sea sponge coral fragile ecosystem underwater", "Deep-sea ecosystems can be slow to recover from disturbance. Some corals and sponges grow very slowly, and damage to their habitat may last for decades or longer. Scientific exploration helps identify these places and understand how they can be protected."),
    ("What We Still Do Not Know", "scientific deep ocean expedition submersible lights darkness", "Every expedition reveals new details, from unfamiliar species to geological features no one had documented before. The unknown is not a reason for fear. It is an invitation to explore carefully, test ideas, and improve our understanding of the planet."),
    ("A Planet Still Waiting to Be Explored", "blue planet Earth ocean from space cinematic", "The deep ocean reminds us how much of Earth remains beyond everyday experience. Its darkness contains complex life, powerful geology, and clues about the history and future of our planet. The next discovery may change what we think we know about life on Earth.")
]

def run(cmd):
    subprocess.run(cmd, check=True)

def probe(path):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)], text=True).strip())

def make_captions(text, audio):
    async def collect():
        words = []
        comm = edge_tts.Communicate(text, "en-US-GuyNeural", rate="-12%", boundary="WordBoundary")
        with audio.open("wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio": f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    words.append((chunk["offset"]/10_000_000, (chunk["offset"]+chunk["duration"])/10_000_000, chunk["text"]))
        return words
    return asyncio.run(collect())

def ass_time(sec):
    cs=max(0,round(sec*100))
    return f"{cs//360000}:{(cs//6000)%60:02d}:{(cs//100)%60:02d}.{cs%100:02d}"

def write_ass(words, path):
    rows=["[Script Info]","ScriptType: v4.00+","PlayResX: 1920","PlayResY: 1080","ScaledBorderAndShadow: yes","","[V4+ Styles]",
    "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
    "Style: Nova,DejaVu Sans,58,&H00FFFFFF,&H0000D7FF,&H00101010,&H99000000,-1,0,0,0,100,100,0,0,1,4,2,2,80,80,110,1","","[Events]",
    "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
    groups=[]; cur=[]
    for w in words:
        cur.append(w)
        phrase=" ".join(x[2] for x in cur)
        if len(cur)>=5 or len(phrase)>=38 or re.search(r"[.!?]$",w[2]): groups.append(cur); cur=[]
    if cur: groups.append(cur)
    for group in groups:
        rendered=[]
        for a,b,word in group:
            safe=word.replace("{",r"\{").replace("}",r"\}")
            rendered.append(r"{\kf"+str(max(1,round((b-a)*100)))+r"}"+safe)
        rows.append(f"Dialogue: 0,{ass_time(group[0][0])},{ass_time(group[-1][1]+.15)},Nova,,0,0,0,,{' '.join(rendered)}")
    path.write_text("\n".join(rows)+"\n",encoding="utf-8")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    narration=" ".join(x[2] for x in SCENES)
    audio=OUT/"nova_longform_voice.mp3"
    words=make_captions(narration,audio)
    duration=probe(audio)
    if not 270 <= duration <= 330:
        raise RuntimeError(f"Narration is {duration:.1f}s, not close enough to five minutes. Adjust script or TTS rate.")
    ass=OUT/"captions.ass"; write_ass(words,ass)
    used=set(); records=[]; rendered=[]
    each=duration/len(SCENES)
    ai_enabled=bool(os.getenv("POLLINATIONS_API_KEY"))
    for i,(title,query,paragraph) in enumerate(SCENES,1):
        image=None; attribution=None
        if ai_enabled:
            image,attribution=generate_ai_image(f"wide 16:9 photorealistic cinematic natural history documentary image, no text, no watermark: {query}",OUT/f"image_{i:02d}.jpg")
        if not image:
            image,attribution=find_image(query,used,OUT/f"image_{i:02d}.jpg")
        if not image:
            raise RuntimeError(f"No usable image found for scene {i}: {query}. Configure POLLINATIONS_API_KEY for AI generation or retry later.")
        records.append({"scene":i,"title":title,"query":query,**(attribution or {})})
        seg=OUT/f"scene_{i:02d}.mp4"
        # A slow Ken Burns move makes every still feel like a moving documentary shot.
        vf=f"scale=2200:-2,crop=1920:1080,zoompan=z='min(zoom+0.00035,1.12)':d={math.ceil(each*30)}:s=1920x1080:fps=30,format=yuv420p"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-i",str(image),"-t",f"{each:.3f}","-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","20",str(seg)])
        rendered.append(seg)
        print(f"[LONGFORM] scene {i}/{len(SCENES)} ready: {title}",flush=True)
    concat=OUT/"scenes.txt"
    concat.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in rendered),encoding="utf-8")
    silent=OUT/"silent.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)])
    final=OUT/"nova_five_minute_documentary.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(silent),"-i",str(audio),"-vf",f"subtitles={ass.as_posix()}","-map","0:v:0","-map","1:a:0","-t",f"{duration:.3f}","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(final)])
    meta={"title":"What Is Hiding in the Deepest Ocean?","language":"English","duration_seconds":round(probe(final),2),"resolution":"1920x1080","scenes":records,"voice":"en-US-GuyNeural","captions":"English word-synchronized karaoke","created_at":datetime.now(timezone.utc).isoformat(),"ai_images_enabled":ai_enabled,"video_file":final.name}
    (OUT/"metadata.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(meta,ensure_ascii=False),flush=True)

if __name__=="__main__": main()
