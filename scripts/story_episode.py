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
 "title": "I Was Lost in a Blizzard for 3 Nights… Then I Saw Something Outside",
 "hook": "The storm buried the road, killed my phone, and left me alone in the mountains. On the third night, something walked around my cabin and whispered my name.",
 "scenes": [
  ("blizzard mountain", "A lone young man in a deep blue knit hood and scarf, olive green winter parka and brown backpack struggles through a violent whiteout blizzard in remote mountains."),
  ("lost in snow", "The same young man stands alone in a vast frozen forest, snow whipping sideways, barely visible pine trees and a fading trail."),
  ("dead phone", "Close view of the same young man holding a dead mobile phone with a cracked screen, snow covering his gloves, frightened eyes."),
  ("night blizzard forest", "The same young man follows faint footprints between dark snow covered pine trees at blue twilight, cinematic storybook illustration."),
  ("remote cabin snow", "A small abandoned wooden cabin appears through dense falling snow, one dark window, the same young man approaching exhausted."),
  ("cabin interior fireplace", "Inside a rustic isolated cabin, the same young man lights a small fireplace, wet gloves and backpack on the wooden floor."),
  ("frosted cabin window", "The same young man looks through a frosted window and sees a tall indistinct human shaped shadow among the trees."),
  ("old radio cabin", "Close view of an old emergency radio crackling on a wooden table as the same young man listens in fear."),
  ("footprints around cabin", "Fresh human footprints form a perfect circle around the isolated cabin in deep snow, viewed from the doorway."),
  ("shadow outside window", "A tall dark silhouette stands just beyond the cabin window in blowing snow, the same young man frozen in fear inside."),
  ("old photograph cabin", "The same young man discovers a faded old photograph showing a man with his exact face standing beside the same cabin decades earlier."),
  ("burned cabin memory", "A weathered newspaper clipping and old ranger map reveal the cabin burned down years ago, the same young man stares in disbelief."),
  ("knocking cabin door", "The cabin door trembles under three slow knocks while the same young man backs away, firelight flickering."),
  ("ranger rescue snow", "At dawn two mountain rescuers find the same young man outside the cabin in deep snow, distant pine forest and pale winter light."),
  ("snow rescue vehicle", "The same young man sits inside a rescue vehicle looking back at the cabin disappearing in the storm."),
  ("mysterious package", "At home weeks later, the same young man opens a plain package containing a small memory card and a note on a table."),
  ("memory card cabin footage", "A laptop screen shows grainy night vision footage of the same snow cabin, a shadow standing behind the camera, the young man watching."),
  ("final snowy window", "The same young man stands in a dark apartment looking at fresh frost and a human handprint on the outside of the window, chilling cinematic ending.")
 ]
}
NARRATION = """
The first thing I learned about being lost in a blizzard is that the snow does not have to bury you to kill you. It only has to make you stop moving. It can erase a road, hide a cliff, silence a phone, and turn a familiar mountain into a place where every direction looks exactly the same.

My name is Daniel. I was driving through the northern mountains when the weather alert came across the radio. Heavy snow. Dangerous visibility. Roads closing. I had planned to reach a small town before dark, so I told myself I had enough time. That was my first mistake.

The snow began as tiny white flecks against the windshield. Ten minutes later, the world outside had disappeared. My headlights illuminated a wall of white. The road markings vanished beneath the snow, and the tires began sliding whenever I touched the brakes. I slowed down, but a fallen branch blocked the road ahead. I tried to turn around. The rear wheels slipped into a ditch, and the engine died.

I called for help. No signal. I tried again. Nothing. The temperature was dropping, and the wind shook the car hard enough to make the mirrors rattle. I had a winter coat, a backpack, a bottle of water, a flashlight, and a little food. The nearest marked shelter was several miles behind me, but I could no longer tell where the road was.

I waited until the worst gusts passed, then wrapped my scarf around my face and stepped outside. The cold hit like a physical blow. Within seconds, snow covered my shoulders and the hood of my coat. I tied a bright strip of fabric to the car mirror, took my backpack, and followed what I thought was the road.

After twenty minutes, I realized I had been walking in a circle. My own footprints had disappeared beneath fresh snow. The trees looked identical. I stopped, forced myself to breathe slowly, and listened. Somewhere ahead, beneath the wind, I heard a faint metallic sound. It might have been a signpost swinging. It might have been a gate. I moved toward it carefully.

Then I saw a shape between the trees. A roof. A small wooden cabin, almost completely buried in snow.

The door was not locked. Inside, the air smelled of old wood, dust, and something faintly smoky. There was a fireplace, a table, two chairs, and an emergency radio with a cracked plastic case. No food. No working lights. But the walls blocked the wind, and that was enough for the moment.

I found a few dry pieces of wood beneath the table and managed to get a small fire going. My hands were shaking so badly that I dropped the matches twice. When the flames finally caught, I sat close to them and watched the shadows move across the walls. I told myself I would wait for daylight, then find a way back to the road.

That was night one.

At around two in the morning, the radio crackled. A voice came through beneath a storm of static. It sounded like a man speaking from far away. I turned the volume up.

'If anyone is inside the cabin, stay away from the windows.'

I leaned closer. The message repeated. Then the voice said something that made my stomach tighten.

'Do not open the door if you hear someone calling your name.'

I waited for more. There was only static.

A few minutes later, three soft knocks came from the front door.

I froze. The knocks were slow and evenly spaced. Not the random tapping of branches. Not the wind. Someone was standing outside.

I moved toward the window, careful not to stand directly in front of it. Through a narrow gap in the frost, I saw a dark figure near the edge of the porch. It was tall, perfectly still, and facing the cabin.

I called out, asking if they needed help. The figure did not move.

Then it spoke.

'Daniel.'

I had not told anyone in the mountains my name. My phone was dead. There was no one else in the cabin. I backed away from the window and turned off the lantern. I stayed beside the fireplace until the first grey light appeared.

When I looked outside again, the figure was gone. But there were footprints in the snow. They began at the tree line, crossed the porch, and stopped directly in front of the door.

There were no footprints leading away.

I spent the second day searching the cabin. I found a small cupboard with a tin of matches, a cracked mug, and an old photograph. The photograph showed a man standing in front of the cabin. He wore a dark coat and held a wooden walking stick. His face was pale, his hair dark, and his eyes looked strangely familiar.

I turned the photograph over. On the back, someone had written a date from twelve years earlier and a single sentence: 'He came back after the storm.'

The man in the picture looked exactly like me.

Not similar. Not a distant resemblance. The same face. The same small scar near the eyebrow. The same uneven smile I saw every morning in the mirror.

I dropped the photograph. It landed face down on the floor.

I searched the rest of the cabin, hoping to find an explanation. Behind a loose board near the fireplace, I discovered a folded newspaper clipping. The headline described a cabin fire in these mountains twelve years earlier. The building had burned to its foundations. A man had disappeared during the storm, and the search had been abandoned after three days.

The article included a photograph of the cabin.

It was this cabin.

I looked around at the walls, the fireplace, the table. Everything was solid. The fire was still burning. I could feel the floor beneath my boots. Yet the newspaper said the building had been destroyed.

Outside, the wind began to rise again.

That evening, the radio turned on by itself. A low hiss filled the room. Then the same voice returned, weaker than before.

'If you can hear me, do not trust the person who comes to rescue you.'

I grabbed the radio and shouted, asking who was speaking. The answer came after a long burst of static.

'You already met him.'

The radio clicked off.

Night two was worse than the first. I pushed the table against the door and placed the chairs beneath the window handles. I kept the flashlight in one hand and the photograph in the other. At midnight, something began walking around the cabin.

Slow steps. Crunch. Pause. Crunch. Pause.

The footsteps circled the walls again and again. Sometimes they stopped outside the window. Sometimes they stood near the chimney. Once, I heard snow sliding from the roof as if someone had climbed onto it.

Then the voice came from the other side of the door.

'Daniel, it's cold out here. Let me in.'

It sounded like my own voice.

I pressed my hands against my ears. The voice repeated the same sentence, but each time it sounded closer, as if the speaker had moved from the porch to the other side of the wood.

Then came a whisper.

'You left me here.'

I did not sleep.

On the third morning, the storm weakened. I could see the slope beyond the trees. I decided to leave as soon as there was enough light to follow the mountain down. I packed the photograph, the radio, and the remaining food. Before opening the door, I looked through the window.

The footprints were back. This time they formed a complete circle around the cabin. In the centre of the circle, directly beneath the window, lay my backpack.

I was holding my backpack.

The one outside looked identical. Same brown fabric. Same torn strap. Same small patch stitched near the top. I opened mine. Inside was the flashlight, the water bottle, and my car keys.

I looked outside again.

The other backpack was gone.

I ran.

I followed the slope downhill, slipping through deep snow and pushing between branches. Twice I fell. Once I heard footsteps behind me, matching my pace. I did not turn around. I kept moving until the trees opened onto a narrow road.

A rescue truck appeared through the snow. Two mountain rangers climbed out and waved me over. One wrapped a blanket around my shoulders. The other asked where I had spent the night.

I told them about the cabin.

They exchanged a look.

There was no cabin in that area, one of them said. The only structure nearby had burned down twelve years ago. The remains were still marked on the old map.

I showed them the photograph.

The younger ranger went pale. He said the man in the picture was his grandfather, one of the volunteers who had searched for the missing driver. The older ranger took the photograph, turned it over, and quietly put it in his coat pocket.

I asked for it back.

He said there was nothing to return. The photograph was blank.

I looked at his hand. The picture was not in it. It was not in his pocket. It had simply vanished.

They drove me to town. At the clinic, doctors treated my hands for frostbite and asked me the same questions again and again. I told them about the radio, the footprints, the voice, and the cabin. They wrote everything down but never mentioned the photograph.

Three weeks later, I received a package at my apartment. No return address. Inside was a small memory card and a note written in block letters.

'You forgot to bring the radio.'

I put the card into my laptop. It contained one video file. The footage was black and white, dated twelve years earlier. It showed the cabin from outside during a blizzard. A man stood on the porch, facing the camera.

It was me.

I watched the figure raise one hand and knock three times. Then the camera moved, as if someone behind it had stepped closer. The man on the porch leaned toward the lens.

His mouth moved.

The audio was almost silent, but I heard the words clearly.

'Do not trust the rescue team.'

The video ended.

I checked the file details. It had been created that morning.

I unplugged the memory card and looked toward my apartment window. A thin layer of frost had formed on the glass, even though the heating was on. Slowly, a handprint appeared on the outside of the window.

Then three knocks sounded from the other side.

I live on the seventh floor.

I have not opened the window. I have not told the police. I keep the lights on, and every night I listen for footsteps in the hallway.

Sometimes, just before dawn, I hear a radio turning on in the next room.

And sometimes, through the static, I hear my own voice saying the same thing.

'If anyone is listening, stay away from the windows.'

If you ever find yourself lost in a blizzard and discover a cabin that seems too welcoming, remember this: shelter can save your life, but not every place that opens its door wants you to leave.

And if something outside calls you by name, do not answer.
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
    if duration<450 or duration>700: raise RuntimeError(f"Blizzard narration must be 7.5–11.7 minutes; got {duration:.1f}s")
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
        tint=Image.new("RGB",(W,H),(92,145,190))
        bg=Image.blend(bg,tint,0.07)
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
