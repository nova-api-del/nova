#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, os, random, subprocess
from datetime import datetime, timezone
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"; OUT.mkdir(exist_ok=True)
W,H=1080,1920
VOICE=os.getenv("TTS_VOICE","en-US-GuyNeural")
TOPICS=[
("Ocean Mysteries","ocean,deep sea,marine animal"),
("Impossible Animal Abilities","animal,wildlife,octopus,bird"),
("Space Facts That Sound Fake","space,planet,astronomy"),
("Ancient Engineering","ancient architecture,archaeology"),
("Extreme Places on Earth","Antarctica,desert,volcano"),
("Weather That Looks Unreal","storm,lightning,cloud"),
("Hidden World of Insects","insect,macro,wildlife"),
("How Your Brain Predicts Reality","brain,neuroscience"),
("Volcanoes Explained","volcano,eruption,geology"),
("The Deepest Places Humans Explore","deep ocean,submarine"),
("Strangest Natural Phenomena","aurora,geology,nature"),
("Technology That Changed Everything","technology,robotics,computer"),
]
FACTS={
"Ocean Mysteries":["The deep ocean covers most of our planet, yet huge areas remain poorly explored.","Some deep sea animals produce their own light using bioluminescence.","Pressure in the deepest trenches can exceed a thousand times the pressure at the surface.","Scientists still discover species and behaviors that were previously unknown.","That makes the ocean one of Earth's greatest remaining frontiers."],
"Impossible Animal Abilities":["Octopuses have three hearts and blue blood.","Some birds can use Earth's magnetic field as part of their navigation system.","Geckos can climb smooth surfaces using millions of microscopic structures on their feet.","Tardigrades can survive extreme conditions that kill most organisms.","Nature has spent millions of years building biological technology."],
"Space Facts That Sound Fake":["Venus rotates so slowly that its day is longer than its year.","A neutron star packs enormous mass into a sphere only about the size of a city.","Light from the Sun takes about eight minutes to reach Earth.","Some planets outside our solar system orbit two stars.","The universe is stranger than science fiction in many ways."],
"Ancient Engineering":["Ancient builders moved enormous stones without modern cranes.","Roman concrete structures have survived for thousands of years.","Some ancient cities used sophisticated water and drainage systems.","Engineers in different civilizations solved similar problems in very different ways.","The past was far more technically creative than it is often portrayed."],
"Extreme Places on Earth":["Antarctica is the largest desert on Earth because deserts are defined by precipitation.","The Atacama Desert is among the driest places on the planet.","Some Antarctic lakes remain liquid beneath kilometers of ice.","Deep ocean trenches reach farther below sea level than Mount Everest rises above it.","Earth has environments that feel almost like other worlds."],
"Weather That Looks Unreal":["Lightning can heat nearby air to temperatures hotter than the surface of the Sun.","Mammatus clouds can form dramatic pouch-like structures beneath storm clouds.","Sprites are huge electrical flashes that occur high above thunderstorms.","Hurricanes can release enormous amounts of energy over several days.","The atmosphere is a giant physics laboratory above our heads."],
"Hidden World of Insects":["Many insects communicate using chemical signals that humans cannot smell.","Dragonflies have been flying for hundreds of millions of years in some form.","Ant colonies can behave like a distributed superorganism.","Some insects use camouflage so effective that predators can pass right by them.","The tiny world around us is full of complex survival strategies."],
"How Your Brain Predicts Reality":["Your brain does not simply record the world like a camera.","It constantly combines incoming signals with predictions about what should happen next.","That is one reason context can change what you notice.","Sleep, attention and learning all reshape how the brain processes information.","Your perception is an active construction, not a perfect recording."],
"Volcanoes Explained":["Volcanoes form when magma finds pathways through Earth's crust.","Some eruptions are explosive while others produce slow-moving lava flows.","Volcanic ash can travel thousands of kilometers through the atmosphere.","Volcanoes also create new land and enrich some soils.","The same geological process can be both destructive and creative."],
"The Deepest Places Humans Explore":["The deepest parts of the ocean are darker and colder than almost anywhere on Earth.","Specialized submersibles can descend to pressures that would crush ordinary equipment.","Scientists use remotely operated vehicles to explore places humans cannot safely reach.","New observations from the deep can change what researchers understand about life.","The ocean floor is still one of the least familiar landscapes on our planet."],
"Strangest Natural Phenomena":["Auroras happen when energetic particles interact with gases in Earth's upper atmosphere.","Some rocks can move across desert surfaces when rare combinations of ice and wind occur.","Lightning can appear in volcanic plumes during major eruptions.","Under the right conditions, water can freeze and boil at the same time.","Nature can produce effects that look impossible until the physics is understood."],
"Technology That Changed Everything":["The first web page was published in 1991.","Modern processors contain billions of transistors.","GPS receivers determine position by comparing signals from multiple satellites.","Machine learning systems can identify patterns across enormous datasets.","Technology changes fastest when old assumptions are challenged."]
}
def run(cmd): subprocess.run(cmd,check=True)
def font(n,b=False):
    p="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if b else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p,n)
def wrap(d,s,f,m):
    out=[]; cur=""
    for w in s.split():
        t=(cur+" "+w).strip()
        if d.textbbox((0,0),t,font=f)[2]<=m: cur=t
        else:
            if cur: out.append(cur)
            cur=w
    if cur: out.append(cur)
    return out
def fallback(title,sentence,path,idx,total):
    im=Image.new("RGB",(W,H)); d=ImageDraw.Draw(im)
    for y in range(H): d.line((0,y,W,y),fill=(8+int(18*y/H),20+int(25*y/H),55+int(55*y/H)))
    d.rectangle((0,0,W,24),fill=(80,200,255))
    d.text((70,110),"NOVA • DAILY DISCOVERY",font=font(30,1),fill=(130,220,255))
    y=270
    for line in wrap(d,title,font(64,1),900)[:3]:
        d.text((70,y),line,font=font(64,1),fill="white"); y+=85
    d.rounded_rectangle((55,690,1025,1510),45,fill=(16,35,78),outline=(80,140,210),width=4)
    lines=wrap(d,sentence,font(54,1),820); yy=1080-(len(lines)*76)//2
    for line in lines:
        bb=d.textbbox((0,0),line,font=font(54,1)); d.text(((W-(bb[2]-bb[0]))/2,yy),line,font=font(54,1),fill="white"); yy+=76
    d.text((70,1650),f"{idx+1}/{total}",font=font(32,1),fill=(130,220,255))
    im.save(path)
def commons_video(query,work):
    api="https://commons.wikimedia.org/w/api.php"
    params={"action":"query","format":"json","generator":"search","gsrsearch":query+" filetype:video","gsrnamespace":6,"gsrlimit":15,"prop":"imageinfo","iiprop":"url|mime|size"}
    try:
        data=requests.get(api,params=params,headers={"User-Agent":"NovaShortsFactory/1.0"},timeout=20).json()
        for p in (data.get("query") or {}).get("pages",{}).values():
            info=(p.get("imageinfo") or [{}])[0]; mime=info.get("mime",""); url=info.get("url")
            if url and mime.startswith("video/") and info.get("size",0)<80000000:
                ext=".mp4" if "mp4" in mime else ".webm"; dest=work/("clip"+ext)
                r=requests.get(url,headers={"User-Agent":"NovaShortsFactory/1.0"},timeout=90); r.raise_for_status(); dest.write_bytes(r.content)
                return dest
    except Exception: pass
    return None
async def tts(text,path): await edge_tts.Communicate(text,VOICE,rate="-5%").save(str(path))
def make_captions(text,duration,path):
    words=text.split(); chunks=[]; current=[]
    for word in words:
        current.append(word)
        if len(current)>=7 or len(' '.join(current))>=42:
            chunks.append(' '.join(current)); current=[]
    if current: chunks.append(' '.join(current))
    weights=[max(1,len(x)) for x in chunks]; total=sum(weights); cursor=0.0; rows=[]
    for chunk,weight in zip(chunks,weights):
        span=duration*weight/total; rows.append((cursor,min(duration,cursor+span),chunk)); cursor+=span
    def stamp(sec):
        ms=int(round(sec*1000)); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); sec,ms=divmod(ms,1000)
        return f'{h:02d}:{m:02d}:{sec:02d},{ms:03d}'
    path.write_text('\\n\\n'.join(f'{i}\\n{stamp(a)} --> {stamp(b)}\\n{t}' for i,(a,b,t) in enumerate(rows,1)),encoding='utf-8')
    return path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--slot",type=int,default=0); args=ap.parse_args()
    day=datetime.now(timezone.utc).strftime("%Y%m%d")
    topic_index=(datetime.now(timezone.utc).date().toordinal()*6+args.slot)%len(TOPICS)
    title,search=TOPICS[topic_index]; facts=FACTS[title]
    work=OUT/f"job_{day}_{args.slot}"; work.mkdir(parents=True,exist_ok=True)
    narration="Here is something most people never realize. "+" ".join(facts)+" Follow Nova for more discoveries."
    audio=work/"voice.mp3"; asyncio.run(tts(narration,audio))
    dur=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(audio)]))
    captions=make_captions(narration,dur,work/"captions.srt")
    subtitle_filter=f"subtitles=filename={captions.as_posix()}:force_style='FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=220'"
    clip=commons_video(search,work)
    if clip:
        video=work/"video.mp4"
        run(["ffmpeg","-y","-stream_loop","-1","-i",str(clip),"-i",str(audio),"-t",str(max(1,dur)),"-map","0:v:0","-map","1:a:0","-vf",f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p,{subtitle_filter}","-c:v","libx264","-preset","veryfast","-crf","24","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(video)])
    else:
        imgs=[]; each=max(4.5,dur/len(facts))
        for i,f in enumerate(facts):
            p=work/f"scene{i}.jpg"; fallback(title,f,p,i,len(facts)); imgs.append(p)
        concat=work/"concat.txt"; lines=[]
        for p in imgs: lines += [f"file '{p}'",f"duration {each:.3f}"]
        lines.append(f"file '{imgs[-1]}'"); concat.write_text("\n".join(lines))
        video=work/"video.mp4"
        frames_per_scene=max(1,round(each*30))
        run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-i",str(audio),"-map","0:v:0","-map","1:a:0","-vf",f"zoompan=z='min(zoom+0.0008,1.12)':d={frames_per_scene}:s=1080x1920:fps=30,format=yuv420p,{subtitle_filter}","-t",str(dur),"-c:v","libx264","-preset","veryfast","-crf","24","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(video)])
    meta={"title":title+" #"+str(args.slot+1),"description":"A fast science and nature discovery. Follow Nova for more. #shorts #facts #science #education","date_utc":datetime.now(timezone.utc).isoformat(),"topic":title,"slot":args.slot,"duration_seconds":round(dur,1),"captions":"burned-in"}
    actual=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(video)]))
    if actual < min(10.0,dur*0.8):
        raise RuntimeError(f"Rendered video is too short: {actual:.2f}s (voiceover {dur:.2f}s)")
    streams=subprocess.check_output(["ffprobe","-v","error","-show_entries","stream=codec_type,width,height","-of","json",str(video)],text=True)
    info=json.loads(streams); types={x.get("codec_type") for x in info.get("streams",[])}
    if "video" not in types or "audio" not in types:
        raise RuntimeError("Rendered video is missing its video or audio stream")
    final=OUT/f"short_{args.slot+1:02d}.mp4"; final.write_bytes(video.read_bytes()); (OUT/f"short_{args.slot+1:02d}.json").write_text(json.dumps(meta,indent=2))
if __name__=="__main__": main()
