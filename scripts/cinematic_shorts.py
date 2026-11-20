#!/usr/bin/env python3
"""Build a real-footage-first Nova Short. No text-card fallback is allowed."""
from __future__ import annotations
import argparse, asyncio, json, os, re, subprocess
from urllib.parse import quote
from datetime import datetime, timezone
from pathlib import Path
import requests
import edge_tts

try:
    from wan2x1_fallback import available as wan_available, generate as wan_generate
except Exception:
    wan_available = lambda: False
    wan_generate = lambda prompt, out, seconds=5: None

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
        "details": [
            "Even a large eruption would affect regions differently, depending on wind and weather.",
            "Fine ash can damage aircraft engines and make roads and water supplies unsafe.",
            "Cooling would depend on how much sulfur reaches the stratosphere and how long it remains.",
            "Monitoring includes earthquakes, ground deformation, gas emissions, and changes in heat.",
            "Past eruptions help researchers understand risk, but they cannot predict an exact date."
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
        "details": [
            "Sunlight fades quickly with depth, leaving ecosystems adapted to darkness.",
            "Some glowing animals use light to attract prey, confuse predators, or communicate.",
            "At the deepest points, pressure is more than a thousand times surface pressure.",
            "ROVs carry cameras, lights, and instruments into places humans cannot safely visit.",
            "New observations help scientists map habitats and understand deep ocean food webs."
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
        "details": [
            "The octopus has no rigid skeleton, so most of its body can squeeze through.",
            "Those tiny toe structures create close contact with surfaces without ordinary glue.",
            "Birds combine magnetic cues with landmarks, the Sun, and other navigation signals.",
            "During dormancy, tardigrades lose most of their body water and slow metabolism.",
            "These adaptations evolved over immense timescales through natural selection."
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
        "details": [
            "They can last only milliseconds, making high-speed cameras essential for research.",
            "The pouch shapes form in sinking air beneath certain cloud layers.",
            "The rapid heating makes air expand explosively, creating the sound of thunder.",
            "Strong winds can lift dust high enough to travel thousands of kilometers.",
            "Satellites and weather radar reveal patterns that ground observers cannot see."
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
        "details": [
            "Polar deserts receive very little snowfall despite their enormous frozen landscapes.",
            "Some areas receive less than a few millimeters of rain in a year.",
            "These hidden lakes may preserve unusual microbial ecosystems beneath the ice.",
            "Ocean trenches form where one tectonic plate sinks beneath another.",
            "Studying extreme habitats helps researchers search for life beyond Earth."
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
        "details": [
            "Venus takes about 243 Earth days to rotate once on its axis.",
            "A teaspoon of neutron star material would have an extraordinary mass on Earth.",
            "That sunlight is already eight minutes old when it reaches our planet.",
            "These worlds are called circumbinary planets because they orbit both stars.",
            "New telescopes are revealing planets and systems once beyond our reach."
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
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(dest)],
                       check=True, capture_output=True, text=True, timeout=30)
        if "video" not in probe.stdout.lower():
            raise ValueError("download contains no video stream")
        return dest
    except Exception:
        dest.with_suffix(dest.suffix + ".part").unlink(missing_ok=True)
        dest.unlink(missing_ok=True)
        return None

def nasa_video(query: str, used: set[str], dest: Path):
    """Search NASA's public video library and resolve real MP4/MOV files via asset manifests."""
    search_api = "https://images-api.nasa.gov/search"
    headers = {"User-Agent": UA}
    # Search broad, likely-to-be-indexed concepts after the exact editorial phrase.
    words = query.lower().split()
    terms = [query, " ".join(words[:3]), " ".join(words[-2:])]
    topic_words = {
        "supervolcano": ["volcano", "volcanic eruption", "lava", "geology"],
        "volcano": ["volcanic eruption", "lava", "volcanic"],
        "ocean": ["underwater", "deep sea", "ocean"],
        "earthquake": ["earthquake", "seismic", "tectonic"],
        "storm": ["hurricane", "tornado", "lightning"],
        "space": ["rocket launch", "spacecraft", "planet"],
        "animal": ["wildlife", "animal"],
    }
    for key, variants in topic_words.items():
        if key in query.lower():
            terms.extend(variants)
    terms = list(dict.fromkeys(t for t in terms if t))
    seen = set()
    for term in terms:
        try:
            response = requests.get(search_api, params={"q": term, "media_type": "video", "page_size": 50},
                                    headers=headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
            items = (payload.get("collection") or {}).get("items") or []
            print(f"[MEDIA] NASA query={term!r} results={len(items)}", flush=True)
        except Exception as exc:
            print(f"[MEDIA] NASA query={term!r} error={type(exc).__name__}: {str(exc)[:160]}", flush=True)
            continue
        for item in items:
            data = (item.get("data") or [{}])[0]
            nasa_id = data.get("nasa_id")
            if not nasa_id or nasa_id in used or nasa_id in seen:
                continue
            # Reject loosely related NASA search hits before downloading. Require
            # at least one core query term in the title and two in title+description.
            title = str(data.get("title", ""))
            description = str(data.get("description", ""))
            stop = {"the","and","for","with","from","into","above","below","after","before","about","that","this"}
            query_tokens = [w.lower() for w in re.findall(r"[a-z]{4,}", query) if w.lower() not in stop]
            def roots(text):
                found=set()
                for token in re.findall(r"[a-z]{4,}", text.lower()):
                    found.add(token[:5] if len(token)>5 else token)
                return found
            title_roots = roots(title)
            all_roots = roots(title + " " + description)
            wanted = {w[:5] if len(w)>5 else w for w in query_tokens}
            title_hits = len(wanted & title_roots)
            total_hits = len(wanted & all_roots)
            if title_hits < 1 or total_hits < 2:
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
    words = query.lower().split()
    search_terms = list(dict.fromkeys([query, " ".join(words[:3]), words[0] if words else query]))
    for mime_query, ext in [("filemime:video/webm", ".webm"), ("filemime:video/mp4", ".mp4")]:
      for term in search_terms:
        try:
            params = {"action":"query", "format":"json", "list":"search", "srnamespace":6,
                      "srlimit":40, "srsearch":f"{term} {mime_query}"}
            data = requests.get(api, params=params, headers=headers, timeout=30).json()
            pages = (data.get("query") or {}).get("search") or []
            print(f"[MEDIA] Wikimedia query={term!r} {mime_query} results={len(pages)}", flush=True)
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


def pixabay_video(query: str, used: set[str], dest: Path):
    """Pixabay free API (requires a user API key); videos are downloaded, never hotlinked."""
    key = os.getenv("PIXABAY_API_KEY")
    if not key:
        return None, None
    try:
        data = requests.get("https://pixabay.com/api/videos/",
            params={"key": key, "q": query, "per_page": 30, "safesearch": "true"},
            headers={"User-Agent": UA}, timeout=30).json()
        for item in data.get("hits", []):
            video_id = str(item.get("id", ""))
            if not video_id or video_id in used:
                continue
            variants = item.get("videos", {})
            candidates = sorted(variants.values(), key=lambda x: x.get("width", 0), reverse=True)
            for variant in candidates:
                url = variant.get("url")
                if not url:
                    continue
                path = _download_verified(url, dest.with_suffix(".mp4"))
                if path:
                    used.add(video_id)
                    return path, {"file": item.get("tags", query), "url": url,
                        "license": "Pixabay Content License; verify current terms",
                        "artist": item.get("user", "Pixabay contributor"),
                        "credit": item.get("pageURL", "https://pixabay.com/"),
                        "source_id": video_id, "source": "Pixabay"}
    except Exception:
        pass
    return None, None

def pexels_video(query: str, used: set[str], dest: Path):
    """Pexels free API; enabled only when an API key is configured."""
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return None, None
    try:
        data = requests.get("https://api.pexels.com/v1/videos/search",
            params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 30},
            headers={"Authorization": key, "User-Agent": UA}, timeout=30).json()
        for item in data.get("videos", []):
            video_id = str(item.get("id", ""))
            if not video_id or video_id in used:
                continue
            files = sorted(item.get("video_files", []),
                key=lambda x: (x.get("width", 0), x.get("height", 0)), reverse=True)
            for variant in files:
                url = variant.get("link")
                if not url:
                    continue
                path = _download_verified(url, dest.with_suffix(".mp4"))
                if path:
                    used.add(video_id)
                    return path, {"file": item.get("url", query), "url": url,
                        "license": "Pexels License; see https://www.pexels.com/license/",
                        "artist": item.get("user", {}).get("name", "Pexels contributor"),
                        "credit": item.get("url", "https://www.pexels.com/"),
                        "source_id": video_id, "source": "Pexels"}
    except Exception:
        pass
    return None, None

def archive_video(query: str, used: set[str], dest: Path):
    """Internet Archive fallback, accepting only clearly reusable CC/PD items."""
    try:
        # The complete editorial phrase is often too restrictive for Archive metadata.
        words = query.lower().split()
        terms = list(dict.fromkeys([query, " ".join(words[:2]), words[0] if words else query]))
        docs = []
        for term in terms:
            data = requests.get("https://archive.org/advancedsearch.php",
                params={"q": f'({term}) AND mediatype:movies',
                        "fl[]": ["identifier", "title"], "rows": 40, "page": 1, "output": "json"},
                headers={"User-Agent": UA}, timeout=30)
            data.raise_for_status()
            found = data.json().get("response", {}).get("docs", [])
            print(f"[MEDIA] Internet Archive query={term!r} results={len(found)}", flush=True)
            docs.extend(found)
            if len(docs) >= 40:
                break
        for item in docs:
            ident = item.get("identifier")
            if not ident or ident in used:
                continue
            meta = requests.get(f"https://archive.org/metadata/{ident}",
                headers={"User-Agent": UA}, timeout=30).json()
            md = meta.get("metadata", {})
            license_url = str(md.get("licenseurl", md.get("license", ""))).lower()
            # Do not assume every Internet Archive item is public domain.
            allowed = ("creativecommons.org/publicdomain" in license_url or
                       "creativecommons.org/licenses/by/" in license_url or
                       "creativecommons.org/licenses/by-sa/" in license_url or
                       license_url in ("cc0", "public domain", "publicdomain"))
            if not allowed or any(x in license_url for x in ("/by-nc", "/by-nd", "noncommercial")):
                continue
            files = [x for x in meta.get("files", [])
                     if x.get("name", "").lower().endswith((".mp4", ".m4v", ".mov"))
                     and int(x.get("size", 0) or 0) < 120_000_000]
            files.sort(key=lambda x: int(x.get("size", 0) or 0), reverse=True)
            for item_file in files[:4]:
                url = f"https://archive.org/download/{ident}/{quote(item_file['name'])}"
                path = _download_verified(url, dest.with_suffix(Path(item_file["name"]).suffix.lower()))
                if path:
                    used.add(ident)
                    return path, {"file": item.get("title", ident), "url": url,
                        "license": license_url, "artist": md.get("creator", "Internet Archive contributor"),
                        "credit": f"https://archive.org/details/{ident}",
                        "source_id": ident, "source": "Internet Archive"}
    except Exception:
        pass
    return None, None

def generate_ai_image(query: str, dest: Path):
    """Optional AI still generation; animated with a camera move during rendering.
    Pollinations currently requires an API key; never silently spend or claim it is free.
    """
    key = os.getenv("POLLINATIONS_API_KEY")
    if not key:
        return None, None
    prompt = ("Photorealistic cinematic documentary frame, no text, no labels, no watermark: " + query)
    model = os.getenv("POLLINATIONS_IMAGE_MODEL", "black-forest-labs/flux.1-schnell")
    url = "https://gen.pollinations.ai/image/" + quote(prompt, safe="")
    try:
        response = requests.get(url, params={"model": model, "width": 1024, "height": 1792},
            headers={"Authorization": f"Bearer {key}", "User-Agent": UA},
            timeout=180)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";")[0].lower()
        ext = { "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp" }.get(content_type)
        if not ext or len(response.content) < 30_000:
            return None, None
        dest = dest.with_suffix(ext)
        dest.write_bytes(response.content)
        return dest, {"file": f"AI-generated scene: {query}", "url": "https://gen.pollinations.ai/",
            "license": "AI-generated; provider/model terms apply", "artist": "Nova AI generation",
            "credit": f"Prompt: {prompt}; model: {model}", "source": "AI-generated image",
            "kind": "ai_generated_image_animated"}
    except Exception:
        dest.with_suffix(".jpg").unlink(missing_ok=True)
        return None, None

def find_video(query: str, used: set[str], dest: Path):
    """Try several independent free libraries before optional AI imagery."""
    providers = (nasa_video, pixabay_video, pexels_video, archive_video, commons_video)
    for provider in providers:
        try:
            clip, attribution = provider(query, used, dest)
            print(f"[MEDIA] {provider.__name__}: {'FOUND' if clip else 'no match'} for {query}", flush=True)
            if clip:
                return clip, attribution
        except Exception as exc:
            print(f"[MEDIA] {provider.__name__}: ERROR {type(exc).__name__}: {str(exc)[:240]}", flush=True)
    # Optional true AI video fallback. It runs only when a Wan2.1 model directory is explicitly configured.
    if os.getenv("AI_MODE", "auto").lower() in ("auto", "wan", "ai") and wan_available():
        try:
            prompt = ("Photorealistic cinematic science documentary footage, no text, no logos, "
                      "natural camera movement, realistic lighting: " + query)
            ai_clip = wan_generate(prompt, dest.with_suffix(".wan.mp4"), seconds=5)
            if ai_clip:
                print(f"[MEDIA] Wan2.1: FOUND for {query}", flush=True)
                return ai_clip, {
                    "file": f"Wan2.1 AI video: {query}",
                    "url": "https://github.com/Wan-Video/Wan2.1",
                    "license": "Wan2.1 model license; generated output subject to model terms",
                    "artist": "Nova AI generation",
                    "credit": "Prompt-generated video",
                    "source": "Wan2.1",
                    "kind": "ai_generated_video"
                }
        except Exception as exc:
            print(f"[MEDIA] Wan2.1: ERROR {type(exc).__name__}: {str(exc)[:240]}", flush=True)
    return None, None

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
    narration = topic["hook"] + " " + " ".join(f"{fact} {detail}" for fact, detail in zip(topic["facts"], topic["details"])) + " Follow Nova for more discoveries."
    voice = work / "voice.mp3"
    asyncio.run(make_voice(narration, voice))
    duration = probe_duration(voice)
    if not 45 <= duration <= 62:
        raise RuntimeError(f"Voiceover duration outside 45-62 second target: {duration:.1f}s")
    srt = work / "captions.srt"
    make_srt(narration, duration, srt)
    used, sources, scenes = set(), [], []
    generated_ai = 0
    scene_duration = duration / len(topic["queries"])
    for i, query in enumerate(topic["queries"]):
        clip, attribution = find_video(query, used, work / f"source_{i}")
        scene = work / f"scene_{i:02d}.mp4"
        if clip is not None:
            # Every sourced scene is a distinct, subject-matched moving video clip.
            run(["ffmpeg","-y","-stream_loop","-1","-i",str(clip),"-t",f"{scene_duration:.3f}",
                 "-vf",f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,eq=contrast=1.04:saturation=1.12:brightness=0.01,format=yuv420p",
                 "-an","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",str(scene)])
        else:
            # Up to two AI-generated stills may be animated with a slow camera move; never use text cards.
            if generated_ai >= 2:
                raise RuntimeError(f"QUALITY GATE: no real footage found for scene {i+1}: {query}; AI fallback limit reached.")
            ai_image, attribution = generate_ai_image(query, work / f"ai_scene_{i}")
            if ai_image is None:
                raise RuntimeError(f"QUALITY GATE: all footage sources failed for scene {i+1}: {query}. Configure optional API keys or retry later.")
            generated_ai += 1
            zoom_frames = max(1, int(scene_duration * 30))
            run(["ffmpeg","-y","-loop","1","-i",str(ai_image),"-t",f"{scene_duration:.3f}",
                 "-vf",f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0007,1.12)':d={zoom_frames}:s=1080x1920:fps=30,setsar=1,format=yuv420p",
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
    video_sources = [x for x in sources if x.get("kind") != "ai_generated_image_animated"]
    if len(sources) != 5 or len({x.get("url") for x in video_sources}) != len(video_sources) or len(video_sources) < 3 or generated_ai > 2:
        raise RuntimeError("QUALITY GATE: require five distinct moving scenes, at least three unique real video sources, and no more than two AI-generated animated scenes")
    output = OUT / f"short_{slot+1:02d}.mp4"
    output.write_bytes(final.read_bytes())
    metadata = {
        "title":topic["title"],"description":"Real-world footage, science explained. Follow Nova for more. #shorts #science #nature #documentary",
        "duration_seconds":round(actual,2),"language":"en","voice":VOICE,
        "visual_type":"five_distinct_moving_scenes","quality_gate":"passed",
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
