#!/usr/bin/env python3
"""Create a five-minute English documentary from AI images (Z-Image Turbo) or licensed stills."""
from __future__ import annotations
import asyncio, json, math, os, re, subprocess, time
from pathlib import Path
from urllib.parse import quote
from datetime import datetime, timezone

import requests
import edge_tts
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "longform"
API_KEY = os.getenv("POLLINATIONS_API_KEY", "").strip()
IMAGE_MODEL = os.getenv("POLLINATIONS_IMAGE_MODEL", "tongyi-mai/z-image-turbo").strip()
VOICE = os.getenv("TTS_VOICE", "en-US-GuyNeural")
UA = "NovaLongformDocumentary/1.0 (educational video)"

SCENES = [
("A World Beneath the Waves", "Beneath the ocean surface lies a world larger than all the continents combined. From bright coastal reefs to plains of darkness, the sea contains environments that are still difficult for humans to reach. Scientists have explored only a small part of this immense underwater world, and every expedition adds another piece to the picture.", "deep ocean blue water sunlight rays from surface underwater cinematic natural history documentary"),
("Where Sunlight Disappears", "Sunlight fades quickly as depth increases. In the twilight zone, only a faint blue glow remains. Farther down, sunlight disappears completely, temperatures drop, and the pressure becomes immense. Plants cannot grow in the ordinary way without light, so many deep-sea animals depend on falling organic material, predators, or chemical energy from the seafloor.", "deep ocean twilight zone underwater descending sunlight blue light rays cinematic"),
("The Pressure of the Deep", "The pressure in the deep ocean rises by roughly one atmosphere every ten metres. At the deepest trenches, it is more than a thousand times the pressure at the surface. Human divers cannot reach these places. Researchers instead use specially engineered submersibles with thick pressure-resistant hulls, robotic arms, lights, and cameras built to survive the crushing force.", "deep sea trench underwater research submersible dramatic scale cinematic documentary"),
("Life Makes Its Own Light", "In the darkness, some animals create their own light through a process called bioluminescence. A flash can attract prey, confuse a predator, or help an animal recognize another of its kind. The light is produced by chemical reactions inside the body, and its colour, timing, and pattern can be as important as a signal in a city at night.", "bioluminescent jellyfish glowing blue deep sea black water macro cinematic"),
("The Strange Shapes of Deep-Sea Life", "Many deep-sea animals look unfamiliar because evolution has shaped them for a world unlike ours. Some have enormous mouths, sensitive organs, transparent bodies, or eyes adapted to faint flashes. When food is scarce, a meal may be unpredictable, so some species can swallow surprisingly large prey or conserve energy for long periods between opportunities.", "anglerfish deep sea animal bioluminescent macro underwater photorealistic"),
("Coral Cities in the Dark", "Not all deep-sea habitats are barren. Cold-water corals can build complex structures far below the reach of sunlight. These reefs provide shelter, feeding grounds, and nursery habitat for fish, crustaceans, and many other organisms. Unlike tropical corals, many deep-water species do not rely on symbiotic algae, and some grow very slowly over centuries.", "deep sea cold water coral reef underwater marine ecosystem detailed cinematic"),
("Hydrothermal Vents", "On the ocean floor, hydrothermal vents release mineral-rich hot water through cracks in the crust. Entire communities gather around them. Instead of depending directly on sunlight, microbes use chemical energy to build the foundation of a food web. Tube worms, clams, and other animals live in conditions once thought too extreme to support complex life.", "hydrothermal vent black smoker deep ocean underwater scientific expedition"),
("The Ocean's Great Migrators", "The deep ocean is connected to the surface by migration. Whales and other animals travel enormous distances, carrying nutrients between feeding and breeding areas. Some small creatures rise toward the surface at night to feed and descend again by day. This daily movement is one of the largest migrations of animal life on Earth, repeated across the open sea.", "humpback whale underwater ocean migration cinematic natural history"),
("A Hidden World of Sound", "Sound travels efficiently through seawater, allowing animals and natural events to be heard over long distances. Researchers use hydrophones to listen to whales, dolphins, earthquakes, storms, and the movement of ice. These recordings reveal activity that cameras alone could never capture, and they help scientists understand how noise from ships affects marine animals.", "underwater hydrophone ocean research equipment scientist blue sea cinematic"),
("Robots Explore the Unreachable", "Remotely operated vehicles carry cameras, lights, and scientific instruments into places too dangerous for people. Their cables connect them to ships at the surface, allowing pilots to guide them while watching discoveries in real time. Autonomous underwater vehicles can also follow programmed routes, mapping large areas without a continuous cable to a research vessel.", "remotely operated vehicle ROV deep ocean exploration lights underwater cinematic"),
("Mapping the Seafloor", "Much of the seafloor has not been mapped in high detail. Research ships use sonar to measure depth and build maps of underwater mountains, valleys, and trenches. Better maps help researchers understand ocean circulation, geology, habitats, and natural hazards. They also reveal where future expeditions should go to investigate unusual formations or unexplored ecosystems.", "multibeam sonar ocean floor mapping research ship ocean science"),
("The Ocean and the Climate", "The ocean stores and moves enormous amounts of heat. Currents redistribute energy around the planet, while marine organisms take part in the global carbon cycle. The sea absorbs much of the excess heat trapped by greenhouse gases, influencing weather and climate far beyond the coast. Understanding the ocean is therefore essential to understanding Earth's changing climate.", "ocean currents aerial sea ice climate science blue planet cinematic"),
("Fragile Deep-Sea Ecosystems", "Deep-sea ecosystems can be slow to recover from disturbance. Some corals and sponges grow only a little each year, and damage to their habitat may last for decades or longer. Scientific exploration helps identify these places, measure their biodiversity, and understand how fishing, mining, pollution, and warming waters may affect life in the deep.", "deep sea sponge coral fragile ecosystem underwater macro documentary"),
("What We Still Do Not Know", "Every expedition reveals new details, from unfamiliar species to geological features no one had documented before. The unknown is not a reason for fear. It is an invitation to explore carefully, test ideas, and improve our understanding of the planet. New cameras, better maps, and quieter robots are making more discoveries possible each year.", "scientific deep ocean expedition submersible lights darkness cinematic"),
("A Planet Still Waiting to Be Explored", "The deep ocean reminds us how much of Earth remains beyond everyday experience. Its darkness contains complex life, powerful geology, and clues about the history and future of our planet. The next discovery may change what we think we know about life on Earth. And somewhere below the waves, an entire world is still waiting to be seen.", "blue planet Earth ocean from space cinematic photorealistic documentary")
]

def run(cmd):
    subprocess.run(cmd, check=True)

def probe(path):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)], text=True).strip())

def ai_image(prompt: str, dest: Path, seed: int):
    if not API_KEY:
        return None
    url = "https://gen.pollinations.ai/image/" + quote(prompt, safe="")
    params = {"model": IMAGE_MODEL, "width": 1536, "height": 864, "seed": seed, "nologo": "true"}
    try:
        response = requests.get(url, params=params, headers={"Authorization": "Bearer " + API_KEY, "User-Agent": UA}, timeout=240)
        response.raise_for_status()
        if not response.headers.get("content-type","").startswith("image/") or len(response.content) < 50000:
            raise RuntimeError("image API returned an invalid or very small file")
        dest.write_bytes(response.content)
        with Image.open(dest) as im:
            im.verify()
        return {"source":"Pollinations AI","model":IMAGE_MODEL,"prompt":prompt}
    except Exception as exc:
        print(f"[IMAGE] AI generation failed for {dest.name}: {type(exc).__name__}: {str(exc)[:180]}", flush=True)
        dest.unlink(missing_ok=True)
        return None

def nasa_image(query: str, dest: Path, used: set[str]):
    try:
        data = requests.get("https://images-api.nasa.gov/search", params={"q":query,"media_type":"image","page_size":30}, headers={"User-Agent":UA}, timeout=30).json()
        for item in (data.get("collection") or {}).get("items") or []:
            meta = (item.get("data") or [{}])[0]
            nasa_id = meta.get("nasa_id")
            links = item.get("links") or []
            url = next((x.get("href") for x in links if x.get("rel")=="preview" and x.get("href")), None)
            if not url or nasa_id in used:
                continue
            try:
                r = requests.get(url, headers={"User-Agent":UA}, timeout=90)
                r.raise_for_status()
                if len(r.content) < 20000: continue
                dest.write_bytes(r.content)
                with Image.open(dest) as im: im.verify()
                used.add(nasa_id)
                return {"source":"NASA Image and Video Library","title":meta.get("title",""),"nasa_id":nasa_id,"url":url,"credit":"NASA"}
            except Exception:
                dest.unlink(missing_ok=True)
    except Exception as exc:
        print(f"[IMAGE] NASA search failed: {str(exc)[:120]}", flush=True)
    return None

def commons_image(query: str, dest: Path, used: set[str]):
    api="https://commons.wikimedia.org/w/api.php"
    try:
        data=requests.get(api,params={"action":"query","format":"json","generator":"search","gsrsearch":query+" filetype:bitmap","gsrnamespace":6,"gsrlimit":20,"prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":1920},headers={"User-Agent":UA},timeout=30).json()
        pages=(data.get("query") or {}).get("pages") or {}
        for page in pages.values():
            info=(page.get("imageinfo") or [{}])[0]
            url=info.get("thumburl") or info.get("url")
            if not url or url in used: continue
            try:
                r=requests.get(url,headers={"User-Agent":UA},timeout=90); r.raise_for_status()
                if len(r.content)<20000: continue
                dest.write_bytes(r.content)
                with Image.open(dest) as im: im.verify()
                meta=info.get("extmetadata") or {}
                def val(k):
                    return re.sub("<[^>]+>","",str((meta.get(k) or {}).get("value",""))).strip()
                used.add(url)
                return {"source":"Wikimedia Commons","title":page.get("title",""),"url":url,"artist":val("Artist"),"license":val("LicenseShortName")}
            except Exception:
                dest.unlink(missing_ok=True)
    except Exception as exc:
        print(f"[IMAGE] Wikimedia search failed: {str(exc)[:120]}", flush=True)
    return None

def fit_image(path: Path):
    temp=path.with_suffix(".jpg")
    with Image.open(path) as im:
        im=im.convert("RGB")
        # Preserve full 16:9 composition; crop only if source is far from widescreen.
        target=16/9
        ratio=im.width/im.height
        if ratio>target:
            nw=int(im.height*target); left=(im.width-nw)//2; im=im.crop((left,0,left+nw,im.height))
        else:
            nh=int(im.width/target); top=(im.height-nh)//2; im=im.crop((0,top,im.width,top+nh))
        im=im.resize((1920,1080),Image.Resampling.LANCZOS)
        im.save(temp,"JPEG",quality=94,optimize=True)
    temp.replace(path)

async def make_voice(text: str, audio: Path, rate: str):
    comm=edge_tts.Communicate(text,VOICE,rate=rate)
    await comm.save(str(audio))

def ass_time(sec):
    cs=max(0,round(sec*100))
    return f"{cs//360000}:{(cs//6000)%60:02d}:{(cs//100)%60:02d}.{cs%100:02d}"

def write_ass(words, path):
    rows=["[Script Info]","ScriptType: v4.00+","PlayResX: 1920","PlayResY: 1080","ScaledBorderAndShadow: yes","","[V4+ Styles]",
    "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
    "Style: Nova,DejaVu Sans,56,&H00FFFFFF,&H0000D7FF,&H00101010,&H99000000,-1,0,0,0,100,100,0,0,1,4,2,2,90,90,100,1","","[Events]",
    "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
    groups=[]; cur=[]
    for w in words:
        cur.append(w)
        phrase=" ".join(x[2] for x in cur)
        if len(cur)>=6 or len(phrase)>=44 or re.search(r"[.!?]$",w[2]):
            groups.append(cur); cur=[]
    if cur: groups.append(cur)
    for group in groups:
        rendered=[]
        for a,b,word in group:
            safe=word.replace("{",r"\{").replace("}",r"\}")
            rendered.append(r"{\kf"+str(max(1,round((b-a)*100)))+r"}"+safe)
        rows.append(f"Dialogue: 0,{ass_time(group[0][0])},{ass_time(group[-1][1]+.12)},Nova,,0,0,0,,{' '.join(rendered)}")
    path.write_text("\n".join(rows)+"\n",encoding="utf-8")

def get_word_boundaries(text, audio, rate):
    async def collect():
        words=[]
        comm=edge_tts.Communicate(text,VOICE,rate=rate)
        async for chunk in comm.stream():
            if chunk["type"]=="WordBoundary":
                words.append((chunk["offset"]/10_000_000,(chunk["offset"]+chunk["duration"])/10_000_000,chunk["text"]))
        return words
    return asyncio.run(collect())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    used=set(); images=[]; records=[]
    ai_count=0
    for i,(title,paragraph,visual) in enumerate(SCENES,1):
        dest=OUT/f"scene_{i:02d}.jpg"
        prompt=("Photorealistic premium natural history documentary still, cinematic IMAX photography, 16:9 widescreen, highly detailed, physically realistic lighting, rich but natural colors, no text, no labels, no watermark. Scene: "+visual+".")
        metadata=ai_image(prompt,dest,26000+i)
        if metadata: ai_count+=1
        if not metadata:
            metadata=nasa_image(visual,dest,used)
        if not metadata:
            metadata=commons_image(visual,dest,used)
        if not metadata:
            raise RuntimeError(f"No image source succeeded for scene {i}: {title}. Configure POLLINATIONS_API_KEY or retry the public image sources.")
        fit_image(dest)
        images.append(dest)
        records.append({"scene":i,"title":title,"prompt":prompt,**metadata})
        print(f"[IMAGE] {i}/{len(SCENES)} ready ({metadata['source']}): {title}",flush=True)

    narration=" ".join(x[1] for x in SCENES)
    audio=OUT/"narration.mp3"
    # Adjust speech rate until the spoken programme is close to five minutes.
    chosen_rate="-15%"
    for rate in ["-15%","-25%","-35%"]:
        asyncio.run(make_voice(narration,audio,rate))
        duration=probe(audio)
        chosen_rate=rate
        print(f"[VOICE] rate={rate} duration={duration:.1f}s",flush=True)
        if 275 <= duration <= 315: break
    if duration < 270:
        raise RuntimeError(f"Narration is only {duration:.1f}s; add narration before rendering.")
    if duration > 330:
        raise RuntimeError(f"Narration is {duration:.1f}s; shorten the script before rendering.")

    words=get_word_boundaries(narration,audio,chosen_rate)
    ass=OUT/"captions.ass"; write_ass(words,ass)
    scene_durations=[duration/len(SCENES)]*len(SCENES)
    segments=[]
    for i,(img,seconds) in enumerate(zip(images,scene_durations),1):
        seg=OUT/f"segment_{i:02d}.mp4"
        frames=math.ceil(seconds*30)
        # Smooth slow zoom plus slight horizontal drift, not a static slideshow.
        vf=f"scale=2200:-2,crop=1920:1080,zoompan=z='min(zoom+0.00032,1.10)':x='iw/2-(iw/zoom/2)+sin(on/90)*18':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30,format=yuv420p"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-i",str(img),"-t",f"{seconds:.3f}","-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","19",str(seg)])
        segments.append(seg)
        print(f"[VIDEO] scene {i}/{len(SCENES)} animated",flush=True)
    concat=OUT/"segments.txt"
    concat.write_text("".join("file '"+p.resolve().as_posix()+"'\n" for p in segments),encoding="utf-8")
    silent=OUT/"silent.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)])
    final=OUT/"nova_five_minute_documentary.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(silent),"-i",str(audio),"-vf",f"subtitles={ass.as_posix()}","-map","0:v:0","-map","1:a:0","-t",f"{duration:.3f}","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(final)])
    final_duration=probe(final)
    meta={"title":"What Is Hiding in the Deepest Ocean?","language":"English","duration_seconds":round(final_duration,2),"resolution":"1920x1080","fps":30,"scenes":records,"ai_generated_images":ai_count,"total_images":len(images),"voice":VOICE,"voice_rate":chosen_rate,"captions":"English word-synchronized karaoke","created_at":datetime.now(timezone.utc).isoformat(),"video_file":final.name}
    (OUT/"metadata.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    assert 270 <= final_duration <= 330, final_duration
    print("[SUCCESS] "+json.dumps(meta,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
