#!/usr/bin/env python3
"""Render a five-minute, single-recurring-character illustrated story preview."""
from __future__ import annotations
import json, math, os, re, subprocess, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("output/story_episode_5min")
ASSETS = OUT / "assets"
OUT.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)
W, H, FPS = 1920, 1080, 30
TOTAL = 300.0
VOICE_DURATION = 251.0766
AUDIO_URL = "https://resource2.heygen.ai/text_to_speech/040dbe04d21f45deab4901f77b3512e6/a3a4aa242aaf431ea8ec2c4b3bb332fa/id=e688312479b2440a9830b08848fbc614.wav"
IMAGE_URLS = [
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/61cfd9e6-5efe-4b0e-9e95-0af225a17597/b9bdfce4-1a32-4976-983e-229fd1dba4e4/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiY2E0YjMzYTg0MGVjODBlMiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM1MzI1Nn0.E-Oga42Ij7-J8NI4IaSrpDErMHUA2DHUwqNRHj5wd7k",
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/4b2ac492-d702-4a5f-bd57-72a563b6c25d/3b979e47-3d91-48a0-88bb-c129d2709dc9/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMzgyM2RiYmVlNDdmODkzYyIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzMzMxMH0.tUIKsd8drzfc_8zseqa6Ufkc_wlNMioDZ5wmxQYPsPI",
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/e07fb62d-aa5b-4e06-88bb-4ca52dcf0235/f12f4996-cf1a-49e6-8039-e0db0aa31fd5/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNjhlNjJkZGNmNDNhOTQyZiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzOTQ4NH0.2T7E6rO17rzJ5DUqN38uCo8Ccn6iqnSBf7Gxdu4cJSc",
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/b3ace10a-2bc2-4b43-a760-2451eeeda531/d5b06f86-3847-473a-beb2-75a6ffa9d020/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMDI3MmE4ZmM4NDllZjA3NSIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzNDM5Nn0.K7EHUATLUcBe7MzzSYcPBE9Jmt39HdZ8w4g0rcV5kzM",
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/0ec0c4ed-d9b5-400e-8bc3-692fa011d4b1/47c0fbde-b9af-4257-ae73-55af9f989f92/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNWJiZTFlYTBkMzcwZGY5YSIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM2MjMzNn0.Jq8duCuRIf-DnP0NbHG5FbgoFv7VWGnxLK3RNnNgb_c",
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/991a256d-9a7a-4f5f-81d3-484559baafd5/13cd8dcb-dea5-4e91-b113-779d177dd2fa/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNjdiZjBmODg1YTM3ZWQyMiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM1MjIwMH0.CVi0-OyNSL2R5EytDw1fhojyCzl_L_UtD7awz5lZ2bQ",
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/b6e2271f-a8cb-4069-a2a5-d10ee1fb2571/b98e41fd-b730-433b-bea1-7c2f874d2acf/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiOGE4OTk2ZTk0ZGQxOGQwMSIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzMjA3M30.mLntEgX-QsMSlPNGDCIF6abqByvXrpomiUhjtOQtc4g",
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/e1f3b0ab-2e57-4c14-8b61-b58f8c76464d/ccec0269-5e0e-4e6a-baa2-3aa07c2cac56/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNmVlYTA5NzExMTRmN2EyYiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM0MDQwMX0.zvZll7WO6ivjdZa1DcstxkbDKGUXuiuB-NygR6lPfqc",
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/9840220c-561d-4195-821f-ad575724308a/b35269d4-485f-4039-aecf-44dec3dd903e/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMzU2ZjRkOTFiNzA4MmNmOCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMwNjAwMX0.sCUi2LjsmLRJr1TS8lzNRQuDxIPBYs1b7swtV1DKOWk",
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/b1b9dd5e-0062-4aab-a9a0-38566133beb0/940e1323-8842-4820-ba27-c91909d9fc79/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiZTI0NDg1ZTJhNmQwMTQzZCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM3NjczOH0.gN697rWUUTNfVyEMlYwPrUZvQqQogi6BAuYwfDHfrgU",
 "https://dnznrvs05pmza.cloudfront.net/gemini/gemini-nano-banana-2.1/images/1c0baf59-8d21-4b4c-8a12-9dbc06b35812/65986a8f-e17b-4419-a58b-84c0b774b0b1/Use__hero_as_the_exact_recurring_character_design_reference_.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiZjdlOGZmMDdhYWU3NWM3MiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzNzk5MX0.Gqzoh6a6y8VwEDbDlmRlkszTHo7LbzVTA3oEb5G_2xQ"
]
NARRATION = """Imagine waking up in the middle of a desert with no phone signal, no road, and almost no water. The sun is rising, the sand stretches in every direction, and the only sound is the wind. This is the beginning of one man's fight to survive.

He opens his eyes beneath a small patch of shade. His head hurts. His clothes are covered in dust. For a moment, he cannot remember how he got there. Then he sees the endless dunes, and the truth becomes terrifying. He is alone.

He checks his backpack. A few basic supplies, a small bottle, and a little food. Not enough for a long journey. He takes one careful sip of water. He knows that every drop matters. In the desert, thirst is not just uncomfortable. It can become dangerous much faster than most people imagine.

The first decision is the most important: do not waste energy walking without a plan. He climbs a nearby dune, slowly, stopping whenever the heat makes his head spin. From the top, he scans the horizon. Nothing but sand, rocks, and a pale line of sky.

Then, far away, he notices a faint patch of green. It might be an oasis. It might be an illusion caused by the heat. But it is the only clue he has.

He starts moving toward it, keeping the sun behind him when he can and using the shape of the land to guide his direction. The sand gives way beneath his boots. Each step takes effort. The backpack feels heavier with every minute.

By midday, the heat becomes brutal. The air above the dunes trembles. He finds a narrow strip of shade beside a rock and rests there. He checks the bottle again. Almost empty. Panic begins to rise, but panic will not create water. He takes a breath, slows down, and saves his strength.

As afternoon approaches, the sky changes. A dark wall of dust appears in the distance. A sandstorm is moving toward him. He searches for shelter and spots a shallow opening between rocks. He reaches it just before the wind arrives.

The storm hits like a living thing. Sand rushes past the entrance. The sky turns orange and the world disappears behind dust. He covers his face and pulls his jacket tight. For a long time, he stays still, listening to the wind roar outside.

When the storm finally weakens, the desert looks completely different. The dunes have shifted. His tracks are gone. The direction he had been following is no longer clear.

But the storm has also exposed something useful: a dry riverbed cutting through the rocks. He follows it carefully. Long ago, water must have flowed here. If he is lucky, the channel may lead to a spring or an oasis.

The canyon narrows. He notices small tracks in the sand. They are not his. He studies them and follows their direction, hoping that animals know where water can be found. The sun begins to lower, painting the rocks gold.

Then he hears something he has almost forgotten: the faint sound of moving water.

Between two stones, a thin trickle seeps into a shallow pool. He kneels, checks that the water is clear enough to collect, and drinks slowly. It is not a river. It is not safety forever. But it is a chance.

A little farther on, the canyon opens. A few palm trees stand beside a small oasis. He reaches the water and sits in silence. For the first time since waking, he allows himself to believe he might survive.

But the journey is not over. He still needs a safe route out, a way to signal for help, and enough strength to keep moving. As the sun sets, he climbs a rocky ridge and sees a faint line on the horizon. Perhaps it is a road. Perhaps it is a distant settlement.

He tightens his backpack and takes one more look at the desert behind him. One day has changed everything. He has learned that survival is not about being fearless. It is about making the next careful decision, even when the future is uncertain.

And tomorrow, he will have to make another one."""
def run(cmd):
    print("+", " ".join(map(str,cmd[:8])), flush=True)
    subprocess.run(cmd, check=True)
def fetch(url, dest):
    req=urllib.request.Request(url, headers={"User-Agent":"NovaStoryPreview/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        data=response.read()
    if len(data)<10000: raise RuntimeError(f"Downloaded asset too small: {dest.name}")
    dest.write_bytes(data)
def ass_time(t):
    cs=round(t*100); h=cs//360000; m=(cs//6000)%60; s=(cs//100)%60; c=cs%100
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"
def build_ass(path):
    words=re.findall(r"[A-Za-z0-9’'-]+|[.,!?;:]", NARRATION)
    word_items=[w for w in words if re.match(r"[A-Za-z0-9]",w)]
    total_weight=sum(0.62+0.095*len(w) for w in word_items)
    style=[
      "[Script Info]","ScriptType: v4.00+","PlayResX: 1920","PlayResY: 1080",
      "[V4+ Styles]",
      "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
      "Style: Nova,DejaVu Sans,54,&H00FFFFFF,&H0000D7FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,5,2,2,120,120,90,1",
      "[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]
    t=0.0; idx=0
    while idx<len(word_items):
        group=word_items[idx:idx+6]
        weights=[0.62+0.095*len(w) for w in group]
        dur=sum(weights)/total_weight*VOICE_DURATION
        cursor=t; chunks=[]
        for w,wt in zip(group,weights):
            k=max(1,round(wt/total_weight*VOICE_DURATION*100))
            safe=w.replace("{",r"\{").replace("}",r"\}")
            chunks.append("{\\kf"+str(k)+"}"+safe)
            cursor+=wt/total_weight*VOICE_DURATION
        text=" ".join(chunks)
        style.append(f"Dialogue: 0,{ass_time(t)},{ass_time(min(VOICE_DURATION,t+dur))},Nova,,0,0,0,,{text}")
        t+=dur; idx+=6
    path.write_text("\n".join(style),encoding="utf-8")
def main():
    images=[]
    for i,url in enumerate(IMAGE_URLS,1):
        p=ASSETS/f"scene_{i:02d}.png"
        if not p.exists():
            print(f"Downloading scene {i}/{len(IMAGE_URLS)}",flush=True); fetch(url,p)
        images.append(p)
    audio=ASSETS/"narration.wav"
    if not audio.exists():
        print("Downloading narration",flush=True); fetch(AUDIO_URL,audio)
    # Eleven unique illustrations plus a final reprise of the same single hero at the oasis.
    sequence=images+[images[-1]]
    clip_duration=TOTAL/len(sequence)
    clips=[]
    for i,img in enumerate(sequence):
        clip=ASSETS/f"clip_{i:02d}.mp4"
        clips.append(clip)
        filters=f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},zoompan=z='min(zoom+0.00016,1.075)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(clip_duration*FPS)}:s={W}x{H}:fps={FPS},fade=t=in:st=0:d=0.45,fade=t=out:st={clip_duration-0.5:.3f}:d=0.5,format=yuv420p"
        if i==len(sequence)-1:
            filters += ",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='THE JOURNEY CONTINUES':fontcolor=yellow:fontsize=62:borderw=5:bordercolor=black:x=(w-text_w)/2:y=h*0.76"
        run(["ffmpeg","-y","-loop","1","-i",str(img),"-vf",filters,"-frames:v",str(int(clip_duration*FPS)),"-r",str(FPS),"-an","-c:v","libx264","-preset","veryfast","-crf","22",str(clip)])
    concat=ASSETS/"clips.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in clips),encoding="utf-8")
    silent=ASSETS/"picture_track.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)])
    ass=OUT/"captions.ass"; build_ass(ass)
    mp4=OUT/"nova_desert_5min.mp4"
    # Quiet synthetic wind bed under the narration; voice ends at 4:11 and the final 49 seconds breathe visually.
    fc=f"[1:a]volume=1.0,apad=pad_dur={TOTAL-VOICE_DURATION:.3f}[voice];anoisesrc=color=pink:duration={TOTAL}:sample_rate=48000,lowpass=f=650,volume=0.018[wind];[voice][wind]amix=inputs=2:duration=longest:weights=1 0.35[a]"
    run(["ffmpeg","-y","-i",str(silent),"-i",str(audio),"-filter_complex",fc,"-map","0:v","-map","[a]","-vf",f"subtitles={ass}:fontsdir=/usr/share/fonts/truetype/dejavu","-t",str(TOTAL),"-r",str(FPS),"-c:v","libx264","-preset","veryfast","-crf","22","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(mp4)])
    dur=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(mp4)],text=True).strip())
    # Thumbnail from the final scene.
    im=Image.open(images[-1]).convert("RGB").resize((1280,720))
    draw=ImageDraw.Draw(im)
    try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",64)
    except Exception: f=ImageFont.load_default()
    draw.rounded_rectangle((40,520,1240,685),radius=24,fill=(0,0,0,175))
    draw.text((75,545),"60 DAYS ALONE IN THE DESERT",font=f,fill=(255,220,0),stroke_width=3,stroke_fill=(0,0,0))
    im.save(OUT/"thumbnail.jpg",quality=92)
    meta={"title":"60 Days Alone in the Desert — Five-Minute Preview","duration_seconds":round(dur,2),"scene_count":len(sequence),"unique_illustrations":len(images),"aspect_ratio":"16:9","resolution":"1920x1080","narration_seconds":VOICE_DURATION,"captions":"ASS karaoke-style word highlighting (estimated timing from narration text)","character_rule":"One recurring illustrated adventurer; no duplicated character in scenes"}
    (OUT/"metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print(json.dumps(meta,indent=2))
if __name__=="__main__": main()
