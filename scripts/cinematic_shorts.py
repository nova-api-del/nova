#!/usr/bin/env python3
"""Build a real-footage-first Nova Short. No text-card fallback is allowed."""
from __future__ import annotations
import argparse, asyncio, json, os, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
import requests
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
W, H = 1080, 1920
VOICE = os.getenv("TTS_VOICE", "en-US-GuyNeural")
UA = "NovaCinematicShorts/2.0 (educational video; contact: repository owner)"
TOPICS = [
    {
        "title": "Could a Supervolcano Change the World?",
        "hook": "One eruption could change the world for years.",
        "facts": [
            "A supervolcano can eject more than one thousand cubic kilometers of material in an enormous eruption.",
            "Ash can spread across huge regions and disrupt transport, agriculture, and daily life.",
            "Sulfur gases high in the atmosphere can reflect sunlight and temporarily cool the planet.",
            "These eruptions are extremely rare, and scientists monitor volcanic systems for signs of change.",
            "The real story is not a prediction of doom, but how closely Earth scientists watch our restless planet."
        ],
        "queries": ["supervolcano volcanic caldera eruption", "volcanic ash plume eruption aerial", "volcanic ash falling landscape", "volcano monitoring scientists seismology", "lava flowing volcano landscape"]
    },
    {
        "title": "What Is Hiding in the Deepest Ocean?",
        "hook": "There are places in the ocean sunlight has never reached.",
        "facts": [
            "Most of the deep ocean exists in permanent darkness, under crushing pressure.",
            "Some animals create their own light through a process called bioluminescence.",
            "Deep sea trenches can plunge almost eleven kilometers below the ocean surface.",
            "Robotic submersibles let researchers explore places that would be impossible for divers to reach.",
            "Every expedition can reveal unfamiliar species and surprising ways life survives."
        ],
        "queries": ["deep sea ocean ROV underwater exploration", "bioluminescent deep sea animals", "ocean trench underwater deep sea", "research submarine remotely operated vehicle", "deep sea fish underwater"]
    },
    {
        "title": "Nature's Most Impossible Animal Abilities",
        "hook": "These abilities sound fictional, but they are real.",
        "facts": [
            "An octopus can squeeze through openings barely larger than its beak.",
            "Geckos climb smooth surfaces using millions of microscopic structures on their toes.",
            "Some migratory birds use Earth's magnetic field to help navigate across continents.",
            "Tardigrades can enter a dormant state that helps them survive extreme conditions.",
            "Evolution has produced survival strategies more surprising than science fiction."
        ],
        "queries": ["octopus underwater swimming closeup", "gecko climbing glass macro", "migratory birds flock flying", "tardigrade microscope water bear", "wildlife animal nature macro"]
    },
    {
        "title": "The Strangest Weather on Earth",
        "hook": "The sky can produce things that look completely unreal.",
        "facts": [
            "Sprites are brief electrical flashes that appear high above powerful thunderstorms.",
            "Mammatus clouds form rounded pouches beneath some storm clouds.",
            "Lightning heats the surrounding air to temperatures hotter than the Sun's visible surface.",
            "Dust storms can carry particles across entire oceans and continents.",
            "The atmosphere is an enormous physics laboratory, and we are still learning its behavior."
        ],
        "queries": ["red sprites lightning upper atmosphere", "mammatus clouds storm sky", "lightning thunderstorm dramatic", "dust storm desert aerial", "supercell thunderstorm clouds"]
    },
    {
        "title": "The Most Extreme Places on Earth",
        "hook": "Earth has landscapes that look like another planet.",
        "facts": [
            "Antarctica is the largest desert on Earth because it receives so little precipitation.",
            "The Atacama Desert contains some of the driest landscapes ever measured.",
            "Deep beneath Antarctic ice, scientists have found lakes sealed off from the surface.",
            "The deepest ocean trenches descend farther below sea level than Everest rises above it.",
            "These extreme environments help scientists understand the limits of life."
        ],
        "queries": ["Antarctica aerial ice desert", "Atacama desert landscape Chile", "Antarctic ice drilling research", "ocean deep sea trench submersible", "extreme landscape Earth mountains ice"]
    },
    {
        "title": "Space Facts That Sound Impossible",
        "hook": "The universe is stranger than most people imagine.",
        "facts": [
            "A day on Venus is longer than a Venusian year because the planet rotates so slowly.",
            "Neutron stars pack more mass than the Sun into a sphere roughly the size of a city.",
            "Light from the Sun takes about eight minutes to reach Earth.",
            "Some planets orbit two stars, creating sunsets unlike anything on Earth.",
            "The more we explore space, the more extraordinary the universe becomes."
        ],
        "queries": ["Venus planet space NASA", "neutron star space illustration observatory", "Sun solar flare NASA", "binary star exoplanet astronomy", "galaxy stars telescope deep space"]
    }
]

def run(cmd):
    subprocess.run(cmd, check=True)

def probe_duration(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)], text=True).strip())

def _download_verified(url: str, dest: Path):
    try:
        response = requests.get(url, headers={"User-Agent": UA}, timeout=150, stream=True)
        response.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        total = 0
        with tmp.open("wb") as out:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    total += len(chunk)
                    if total > 120_000_000:
                        raise ValueError("source clip exceeds 120 MB")
                    out.write(chunk)
        if total < 100_000:
            tmp.unlink(missing_ok=True)
            return None
        tmp.replace(dest)
        # Reject HTML/error pages and corrupt or non-video downloads before rendering.
        subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(dest)],
                       check=True, capture_output=True, text=True, timeout=30)
        return dest
    except Exception:
        dest.with_suffix(dest.suffix + ".part").unlink(missing_ok=True)
        dest.unlink(missing_ok=True)
        return None

def nasa_video(query: str, used: set[str], dest: Path):
    """Search NASA's public video library and resolve real MP4/MOV files via asset manifests."""
    search_api = "https://images-api.nasa.gov/search"
    headers = {"User-Agent": UA}
    # Shorter variants improve recall when the full descriptive phrase is not indexed.
    terms = [query, " ".join(query.split()[:3]), " ".join(query.split()[-2:])]
    seen = set()
    for term in terms:
        try:
            payload = requests.get(search_api, params={"q": term, "media_type": "video", "page_size": 30},
                                   headers=headers, timeout=30).json()
            items = (payload.get("collection") or {}).get("items") or []
        except Exception:
            continue
        for item in items:
            data = (item.get("data") or [{}])[0]
            nasa_id = data.get("nasa_id")
            if not nasa_id or nasa_id in used or nasa_id in seen:
                continue
            seen.add(nasa_id)
            try:
                manifest = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}",
                                        headers=headers, timeout=30).json()
                assets = (manifest.get("collection") or {}).get("items") or []
            except Exception:
                continue
            candidates = [a.get("href", "") for a in assets]
            candidates = [u for u in candidates if re.search(r"\.(mp4|mov)(?:$|\?)", u, re.I)]
            for url in candidates[:4]:
                ext = ".mov" if ".mov" in url.lower() else ".mp4"
                path = _download_verified(url, dest.with_suffix(ext))
                if path:
                    used.add(nasa_id)
                    return path, {"file": data.get("title", nasa_id), "url": url,
                                  "license": "NASA media usage guidance applies",
                                  "artist": data.get("center", "NASA"),
                                  "credit": data.get("description", "")[:500],
                                  "source_id": nasa_id}
    return None, None

def commons_video(query: str, used: set[str], dest: Path):
    """Wikimedia fallback using the supported list=search + filemime query."""
    api = "https://commons.wikimedia.org/w/api.php"
    headers = {"User-Agent": UA}
    for mime_query, ext in [("filemime:video/webm", ".webm"), ("filemime:video/mp4", ".mp4")]:
        try:
            params = {"action":"query", "format":"json", "list":"search", "srnamespace":6,
                      "srlimit":30, "srsearch":f"{query} {mime_query}",
                      "prop":"imageinfo", "iiprop":"url|mime|size|extmetadata"}
            data = requests.get(api, params=params, headers=headers, timeout=30).json()
            pages = (data.get("query") or {}).get("search") or []
            for result in pages:
                title = result.get("title", "")
                detail = requests.get(api, params={"action":"query","format":"json","titles":title,
                    "prop":"imageinfo","iiprop":"url|mime|size|extmetadata"}, headers=headers, timeout=30).json()
                page = next(iter((detail.get("query") or {}).get("pages", {}).values()), {})
                info = (page.get("imageinfo") or [{}])[0]
                url, mime = info.get("url"), info.get("mime", "")
                if not url or not mime.startswith("video/") or url in used or info.get("size", 0) > 120_000_000:
                    continue
                path = _download_verified(url, dest.with_suffix(ext))
                if not path:
                    continue
                meta = info.get("extmetadata") or {}
                def val(key):
                    return re.sub("<[^>]+>", "", (meta.get(key) or {}).get("value", "")).strip()
                used.add(url)
                return path, {"file":title, "url":url, "license":val("LicenseShortName"),
                              "artist":val("Artist"), "credit":val("Credit")}
        except Exception:
            continue
    return None, None

def find_video(query: str, used: set[str], dest: Path):
    clip, attribution = nasa_video(query, used, dest)
    if clip:
        return clip, attribution
    return commons_video(query, used, dest)

async def make_voice(text: str, path: Path):
    await edge_tts.Communicate(text, VOICE, rate="-3%", volume="+0%").save(str(path))

def make_srt(text: str, duration: float, path: Path):
    words = text.split()
    chunks, current = [], []
    for word in words:
        current.append(word)
        if len(current) >= 6 or len(" ".join(current)) > 38:
            chunks.append(" ".join(current)); current=[]
    if current: chunks.append(" ".join(current))
    weights = [len(x) for x in chunks]
    total = sum(weights) or 1
    cursor, rows = 0.0, []
    for chunk, weight in zip(chunks, weights):
        span = duration * weight / total
        rows.append((cursor, min(duration, cursor+span), chunk)); cursor += span
    def stamp(t):
        ms = int(t*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    path.write_text("\n\n".join(f"{i}\n{stamp(a)} --> {stamp(b)}\n{line}" for i,(a,b,line) in enumerate(rows,1)), encoding="utf-8")

def build(slot: int):
    topic = TOPICS[slot % len(TOPICS)]
    work = OUT / f"cinematic_{datetime.now(timezone.utc):%Y%m%d}_{slot+1}"
    work.mkdir(parents=True, exist_ok=True)
    narration = topic["hook"] + " " + " ".join(topic["facts"]) + " Follow Nova for more discoveries."
    voice = work / "voice.mp3"
    asyncio.run(make_voice(narration, voice))
    duration = probe_duration(voice)
    if not 24 <= duration <= 58:
        raise RuntimeError(f"Voiceover duration outside target: {duration:.1f}s")
    srt = work / "captions.srt"
    make_srt(narration, duration, srt)
    used, sources, scenes = set(), [], []
    scene_duration = duration / len(topic["queries"])
    for i, query in enumerate(topic["queries"]):
        clip, attribution = find_video(query, used, work / f"source_{i}")
        if clip is None:
            raise RuntimeError(f"QUALITY GATE: no distinct Wikimedia Commons video found for scene {i+1}: {query}. Refusing to render text cards or reuse a generic clip.")
        scene = work / f"scene_{i:02d}.mp4"
        # Every scene gets its own subject-matched moving source clip. Original source audio is removed.
        run(["ffmpeg","-y","-stream_loop","-1","-i",str(clip),"-t",f"{scene_duration:.3f}",
             "-vf",f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,eq=contrast=1.04:saturation=1.12:brightness=0.01,format=yuv420p",
             "-an","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",str(scene)])
        scenes.append(scene); sources.append(attribution)
    concat = work / "scenes.txt"
    concat.write_text("\n".join(f"file '{p.resolve()}'" for p in scenes), encoding="utf-8")
    final = work / "final.mp4"
    subtitle = f"subtitles=filename={srt.as_posix()}:force_style='FontName=DejaVu Sans,FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=250'"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-i",str(voice),"-t",f"{duration:.3f}",
         "-vf",subtitle,"-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","veryfast","-crf","21",
         "-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(final)])
    actual = probe_duration(final)
    if actual < 24 or final.stat().st_size < 2_000_000:
        raise RuntimeError(f"QUALITY GATE: output too short or too small ({actual:.1f}s, {final.stat().st_size} bytes)")
    streams = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","stream=codec_type,width,height","-of","json",str(final)],text=True))
    video = next((s for s in streams["streams"] if s.get("codec_type")=="video"),{})
    audio = any(s.get("codec_type")=="audio" for s in streams["streams"])
    if video.get("width") != 1080 or video.get("height") != 1920 or not audio:
        raise RuntimeError("QUALITY GATE: expected 1080x1920 video and narration audio")
    # Five distinct source URLs are mandatory; this is the critical no-slides/no-reuse check.
    if len({x["url"] for x in sources}) != 5:
        raise RuntimeError("QUALITY GATE: fewer than five distinct moving-footage sources")
    output = OUT / f"short_{slot+1:02d}.mp4"
    output.write_bytes(final.read_bytes())
    metadata = {
        "title":topic["title"],"description":"Real-world footage, science explained. Follow Nova for more. #shorts #science #nature #documentary",
        "duration_seconds":round(actual,2),"language":"en","voice":VOICE,
        "visual_type":"five_distinct_moving_video_clips","quality_gate":"passed",
        "sources":sources,"created_at":datetime.now(timezone.utc).isoformat()
    }
    (OUT / f"short_{slot+1:02d}.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    print(json.dumps({"output":str(output),"metadata":metadata},ensure_ascii=False))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--slot",type=int,default=0)
    args=parser.parse_args()
    build(args.slot)

if __name__=="__main__":
    main()
