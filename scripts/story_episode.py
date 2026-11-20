#!/usr/bin/env python3
"""Nova illustrated survival-story episode builder.

Creates a 3-minute narrated illustrated story with a recurring original mascot.
If POLLINATIONS_API_KEY is configured, it generates storybook-style scenes;
otherwise it uses reusable Wikimedia Commons images with the same mascot overlay
and cinematic camera motion. No paid API is required for the fallback path.
"""
from __future__ import annotations
import asyncio, json, os, re, subprocess, textwrap
from pathlib import Path
from urllib.parse import quote
import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "story_episode"
SCENES = 18
W, H, FPS = 1920, 1080, 30
VOICE = os.getenv("TTS_VOICE", "en-US-GuyNeural")
UA = "NovaIllustratedStories/1.0 (educational storytelling)"
TOPIC = {
 "title": "60 Days Alone in the Desert — Can He Survive?",
 "hook": "Imagine waking up in the middle of a vast desert, with no phone, no map, and almost no water.",
 "scenes": [
  ("desert sunrise", "A lone young adventurer in a blue headscarf and green jacket wakes beside a tiny backpack in an endless golden desert."),
  ("empty water bottle", "Close view of the adventurer checking an almost empty water bottle, worried expression, scorching sun."),
  ("sand dunes", "The adventurer looks across enormous rolling dunes, heat haze shimmering above the sand."),
  ("footprints", "Fresh footprints trail behind the adventurer and disappear beneath blowing sand."),
  ("desert rocks", "The adventurer finds a cluster of dark rocks and searches for shade."),
  ("scorpion tracks", "Small animal tracks cross the sand near a sheltered rock crevice."),
  ("sunset desert camp", "The adventurer builds a tiny windbreak from stones as the sky turns orange."),
  ("cold desert night", "The adventurer sits beneath a star-filled desert sky, wrapped in a jacket beside a small safe campfire."),
  ("distant oasis", "At dawn, the adventurer spots a distant patch of green that might be an oasis."),
  ("dry riverbed", "The adventurer follows a dry riverbed between weathered canyon walls."),
  ("desert storm", "A wall of dust approaches across the desert, the adventurer covers their face and seeks shelter."),
  ("rock shelter", "Inside a shallow rock shelter, the adventurer waits while sand blows past the entrance."),
  ("rare desert plant", "The adventurer discovers hardy desert plants growing in a shaded crack between rocks."),
  ("clouds over dunes", "Dark clouds gather above the dunes and the first raindrops hit the sand."),
  ("rain in desert", "A brief desert shower darkens the ground and leaves small pools between stones."),
  ("distant road", "The adventurer climbs a ridge and notices a faint vehicle track far away."),
  ("rescue vehicle", "A distant rescue vehicle approaches along the track as the adventurer waves both arms."),
  ("sunset hopeful ending", "The exhausted adventurer stands safely beside rescuers, looking back at the immense desert under a warm sunset.")
 ]
}
NARRATION = """
Imagine waking up in the middle of a vast desert, with no phone, no map, and almost no water.
That is the beginning of a survival challenge that tests every decision. The first rule is simple: do not panic. Running under the midday sun wastes precious water, so our young explorer stops, checks the supplies, and studies the landscape.
The bottle is nearly empty. There is no road in sight. The dunes stretch in every direction, and the heat makes distant rocks look like lakes. Walking without a plan could turn a difficult situation into a disaster.
The explorer searches for shade near a group of rocks. A small shelter can reduce direct sunlight and slow dehydration. The backpack contains a compass, a little food, and a lightweight emergency blanket. There is no magic trick here. Staying calm and protecting energy matter more than heroic gestures.
As the sun falls, the desert changes. The temperature drops quickly. The explorer makes a small windbreak and prepares for a cold night. Above, the stars are brilliant, but the silence is unsettling. Every sound seems closer than it really is.
At sunrise, a green patch appears on the horizon. It might be an oasis, or it might be another mirage. The explorer does not rush toward it blindly. Instead, they follow the shape of an old dry riverbed, watching the terrain and conserving strength.
Then the weather changes. A wall of dust rises in the distance. The explorer covers their face and finds shelter behind a rock formation. The storm arrives with a roar, filling the air with sand. For a while, visibility drops to almost nothing. The safest choice is to stay protected and wait.
When the wind finally weakens, the explorer continues carefully. A few hardy plants grow in a shaded crack. They are a reminder that life survives here, but they are not a reason to eat unknown plants or take risks.
Later, clouds gather. Rain begins to fall, briefly transforming the dry ground. The explorer collects a little rainwater in a clean container, then climbs a ridge to look for signs of people. Far away, a faint vehicle track cuts across the sand.
The explorer waves a bright piece of cloth. Minutes later, a rescue vehicle appears. The challenge is over, but the lesson remains: preparation, patience, and sensible decisions can make the difference in an emergency.
The desert is beautiful, powerful, and unforgiving. Would you have stayed calm for sixty days? Follow Nova for more survival stories.
"""

def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def draw_mascot(path: Path):
    im=Image.new("RGBA",(520,760),(0,0,0,0)); d=ImageDraw.Draw(im)
    # Backpack
    d.rounded_rectangle((95,300,425,650),radius=95,fill=(111,76,43),outline=(44,35,29),width=12)
    d.rounded_rectangle((145,355,375,615),radius=55,fill=(145,100,54),outline=(61,43,31),width=10)
    # Body / green jacket
    d.rounded_rectangle((95,325,425,735),radius=110,fill=(65,125,74),outline=(26,62,39),width=14)
    d.polygon([(240,350),(280,350),(300,735),(220,735)],fill=(45,94,57))
    # Head
    d.ellipse((80,45,440,425),fill=(246,207,166),outline=(45,39,35),width=14)
    # scarf hood, blue
    d.arc((55,15,465,450),180,355,fill=(36,82,145),width=68)
    d.polygon([(82,185),(145,55),(320,30),(435,160),(400,250),(330,160),(160,150)],fill=(42,91,159),outline=(25,52,92))
    d.rounded_rectangle((95,55,430,175),radius=65,fill=(48,99,169),outline=(25,52,92),width=10)
    # eyes and brows
    d.ellipse((175,225,210,270),fill=(28,29,33)); d.ellipse((305,225,340,270),fill=(28,29,33))
    d.arc((160,195,220,235),190,340,fill=(55,39,33),width=8)
    d.arc((295,195,355,235),200,350,fill=(55,39,33),width=8)
    d.arc((225,285,295,345),10,170,fill=(112,54,47),width=8)
    # jacket collar and zipper
    d.polygon([(95,350),(255,440),(425,350),(365,505),(255,465),(150,505)],fill=(77,145,86),outline=(27,69,43))
    d.line((260,450,260,710),fill=(220,197,142),width=8)
    d.ellipse((240,520,280,560),fill=(224,190,110),outline=(55,53,40),width=5)
    im.save(path)

def download_commons(query: str, dest: Path, used: set[str]):
    api="https://commons.wikimedia.org/w/api.php"
    for term in [query, " ".join(query.split()[:2]), "desert landscape"]:
        try:
            r=requests.get(api,params={"action":"query","format":"json","generator":"search","gsrsearch":f"filetype:bitmap {term}","gsrnamespace":6,"gsrlimit":12,"prop":"imageinfo","iiprop":"url|mime|size|extmetadata"},headers={"User-Agent":UA},timeout=25)
            r.raise_for_status()
            pages=(r.json().get("query") or {}).get("pages") or {}
            for page in pages.values():
                title=page.get("title","")
                if title in used: continue
                info=(page.get("imageinfo") or [{}])[0]
                if info.get("mime") not in ("image/jpeg","image/png","image/webp") or info.get("size",0)>20_000_000: continue
                meta=info.get("extmetadata") or {}
                license_name=re.sub("<[^>]+>","",str((meta.get("LicenseShortName") or {}).get("value","")))
                license_url=str((meta.get("LicenseUrl") or {}).get("value","")).lower()
                if not (license_name.lower() in ("cc0","public domain","pd") or "creativecommons.org/licenses/by/" in license_url or "creativecommons.org/licenses/by-sa/" in license_url): continue
                data=requests.get(info["url"],headers={"User-Agent":UA},timeout=45)
                data.raise_for_status()
                tmp=dest.with_suffix(".tmp"); tmp.write_bytes(data.content)
                with Image.open(tmp) as test: test.verify()
                tmp.replace(dest); used.add(title)
                return dest,{"title":title,"url":info["url"],"license":license_name,"artist":re.sub("<[^>]+>","",str((meta.get("Artist") or {}).get("value","")))}
        except Exception as e:
            print(f"[IMAGE] {term}: {type(e).__name__}: {e}",flush=True)
    return None,None

def generate_ai_scene(prompt: str, dest: Path):
    key=os.getenv("POLLINATIONS_API_KEY")
    if not key: return None
    text=("Hand-painted 2D animated adventure storybook illustration, warm cinematic lighting, expressive cute young male adventurer with the SAME blue headscarf, green jacket and brown backpack, consistent character design, detailed environment, 16:9 landscape, no text, no watermark. Scene: "+prompt)
    try:
        url="https://gen.pollinations.ai/image/"+quote(text,safe="")
        r=requests.get(url,params={"model":os.getenv("POLLINATIONS_IMAGE_MODEL","flux"),"width":1280,"height":720},headers={"Authorization":f"Bearer {key}","User-Agent":UA},timeout=180)
        r.raise_for_status()
        if not r.headers.get("content-type","").startswith("image/"): return None
        dest.write_bytes(r.content)
        with Image.open(dest) as im: im.verify()
        return dest
    except Exception as e:
        print(f"[AI IMAGE] unavailable: {type(e).__name__}: {e}",flush=True)
        return None

def make_karaoke(audio: Path):
    # Use phrase-timed captions generated from the narration chunks.
    # Edge TTS word boundaries are captured for accurate highlighting.
    return asyncio.run(make_voice())

async def make_voice():
    audio=OUT/"narration.mp3"; boundaries=[]
    comm=edge_tts.Communicate(NARRATION,VOICE,rate="-4%",boundary="WordBoundary")
    with audio.open("wb") as f:
        async for c in comm.stream():
            if c["type"]=="audio": f.write(c["data"])
            elif c["type"]=="WordBoundary":
                boundaries.append((c["offset"]/10_000_000,(c["offset"]+c["duration"])/10_000_000,c["text"]))
    if not boundaries: raise RuntimeError("TTS returned no word timings")
    ass=["[Script Info]","ScriptType: v4.00+","PlayResX: 1920","PlayResY: 1080","[V4+ Styles]",
      "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
      "Style: Story,DejaVu Sans,48,&H00FFFFFF,&H0000D7FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,4,2,2,100,100,70,1","[Events]",
      "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    def ts(t):
      n=round(t*100); return f"{n//360000}:{(n//6000)%60:02d}:{(n//100)%60:02d}.{n%100:02d}"
    for i in range(0,len(boundaries),7):
      group=boundaries[i:i+7]; words=[]
      for a,b,w in group:
        words.append(r"{\kf"+str(max(1,round((b-a)*100)))+"}"+w.replace("{",r"\{").replace("}",r"\}"))
      ass.append(f"Dialogue: 0,{ts(group[0][0])},{ts(group[-1][1]+.15)},Story,,0,0,0,,{{\\an2\\pos(960,970)}}{' '.join(words)}")
    (OUT/"captions.ass").write_text("\n".join(ass),encoding="utf-8")
    return audio

def render():
    OUT.mkdir(parents=True,exist_ok=True); scene_dir=OUT/"scenes"; scene_dir.mkdir(exist_ok=True)
    mascot=OUT/"nova_mascot.png"; draw_mascot(mascot)
    audio=asyncio.run(make_voice()); duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(audio)],text=True).strip())
    if duration<150 or duration>260: raise RuntimeError(f"Story narration must be 2.5–4.3 minutes; got {duration:.1f}s")
    per=duration/SCENES; used=set(); rendered=[]; credits=[]; ai_count=0
    for idx,(query,desc) in enumerate(TOPIC["scenes"],1):
      img=scene_dir/f"scene_{idx:02d}.jpg"
      ai=generate_ai_scene(desc,img)
      if ai:
        source={"kind":"ai_generated_storybook_image","prompt":desc,"provider":"Pollinations"}; ai_count+=1
      else:
        found,credit=download_commons(query,img,used)
        if not found: raise RuntimeError(f"No reusable illustration/background found for scene {idx}: {query}")
        source={"kind":"wikimedia_commons_background",**credit}
      # Fit image, apply warm storybook grade, add the same mascot overlay.
      with Image.open(img).convert("RGB") as bg:
        bg=ImageOps.fit(bg,(W,H),method=Image.Resampling.LANCZOS)
        tint=Image.new("RGB",(W,H),(238,174,100))
        bg=Image.blend(bg,tint,0.10)
        bg=bg.filter(ImageFilter.GaussianBlur(0.15))
        bg=bg.convert("RGBA")
        char=Image.open(mascot).convert("RGBA")
        char.thumbnail((int(W*.31),int(H*.70)))
        bg.alpha_composite(char,(W-char.width-55,H-char.height+5))
        bg.convert("RGB").save(img,quality=91)
      sec=per
      # Slow alternating camera drift, with a gentle fade between still scenes.
      zoom="1.0+0.00035*on" if idx%2 else "min(1.12,1.12-0.00035*on)"
      vf=f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={round(sec*FPS)}:s={W}x{H}:fps={FPS},fade=t=in:st=0:d=0.35,fade=t=out:st={max(0,sec-.35):.2f}:d=0.35,format=yuv420p"
      seg=scene_dir/f"seg_{idx:02d}.mp4"
      run(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-i",str(img),"-t",f"{sec:.3f}","-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",str(seg)])
      rendered.append(seg); credits.append({"scene":idx,"query":query,**source})
      print(f"[STORY] Scene {idx}/{SCENES} ready ({source['kind']})",flush=True)
    concat=scene_dir/"concat.txt"; concat.write_text("".join(f"file '{p.resolve()}'\n" for p in rendered))
    silent=OUT/"silent.mp4"; run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)])
    final=OUT/"nova_story_episode.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(silent),"-i",str(audio),"-vf",f"subtitles={str(OUT/'captions.ass')}", "-map","0:v:0","-map","1:a:0","-t",f"{duration:.3f}","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(final)])
    meta={"title":TOPIC["title"],"duration_seconds":round(duration,2),"resolution":f"{W}x{H}","scenes":SCENES,"ai_generated_scenes":ai_count,"narration":"Edge TTS","character":"Original Nova adventurer mascot, blue headscarf, green jacket, brown backpack","sources":credits,"video":final.name}
    (OUT/"metadata.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    print(f"[STORY] SUCCESS {final} duration={duration:.1f}s AI-scenes={ai_count}",flush=True)

if __name__=="__main__":
    from PIL import ImageOps
    render()
