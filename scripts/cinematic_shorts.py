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
        "queries": ["supervolcano volcanic caldera eruption", "volcanic ash plume eruption aerial", "volcanic ash falling landscape", "volcano eruption lava flowing", "volcanic crater aerial landscape"]
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

def _topic_tokens(text: str) -> set[str]:
    """Normalize topic words without conflating unrelated words like landscape/landslide."""
    tokens = set()
    for word in re.findall(r"[a-z]{3,}", str(text).lower()):
        if word.startswith("erupt"):
            word = "erupt"
        elif word.startswith("volcan"):
            word = "volcan"
        elif word.endswith("ing") and len(word) > 5:
            word = word[:-3]
        elif word.endswith("ies") and len(word) > 5:
            word = word[:-3] + "y"
        elif word.endswith("es") and len(word) > 5:
            word = word[:-2]
        elif word.endswith("s") and len(word) > 4:
            word = word[:-1]
        tokens.add(word[:6] if len(word) > 6 else word)
    return tokens

def _relevant_result(query: str, title: str, description: str) -> bool:
    wanted = _topic_tokens(query)
    title_lower = title.lower()
    if any(word in title_lower for word in ("profile", "interview")) and not any(
        word in query.lower() for word in ("scientist", "profile", "interview")
    ):
        return False
    # Science-footage synonyms: an eruption clip is often indexed without the
    # phrase "volcanic ash", even when its description documents the ash plume.
    if "ash" in wanted:
        wanted.update({"volcan", "erupt", "plume", "ashfal"})
    if "volcan" in wanted or "superv" in wanted:
        wanted.update({"volcan", "erupt", "lava", "magma"})
    title_tokens = _topic_tokens(title)
    all_tokens = _topic_tokens(title + " " + description)
    title_hits = len(wanted & title_tokens)
    total_hits = len(wanted & all_tokens)
    if "volcan" in wanted and "volcan" in title_tokens:
        return True
    return total_hits >= 2 and (title_hits >= 1 or total_hits >= 3)

def nasa_video(query: str, used: set[str], dest: Path):
    """Search NASA's public video library and resolve real MP4/MOV files via asset manifests."""
    search_api = "https://images-api.nasa.gov/search"
    headers = {"User-Agent": UA}
    # Keep discovery bounded: exact phrase plus two compact variants.
    # Relevance filtering below rejects unrelated results without dozens of API calls.
    words = query.lower().split()
    terms = [query, " ".join(words[:3]), " ".join(words[-2:])]
    if "supervolcano" in query.lower():
        terms.extend(["volcano", "volcanic eruption", "volcanic ash"])
    elif "ash" in query.lower():
        terms.extend(["volcanic ash", "volcano eruption"])
    terms = list(dict.fromkeys(t for t in terms if t))
    seen = set()
    for term in terms:
        try:
            response = requests.get(search_api, params={"q": term, "media_type": "video", "page_size": 40},
                                    headers=headers, timeout=20)
            response.raise_for_status()
            payload = response.json()
            items = (payload.get("collection") or {}).get("items") or []
            print(f"[MEDIA] NASA query={term!r} results={len(items)}", flush=True)
        except Exception as exc:
            print(f"[MEDIA] NASA query={term!r} error={type(exc).__name__}: {str(exc)[:160]}", flush=True)
            continue
        for item in items[:30]:
            data = (item.get("data") or [{}])[0]
            nasa_id = data.get("nasa_id")
            if not nasa_id or nasa_id in used or nasa_id in seen:
                continue
            # Reject loosely related NASA search hits before downloading. Require
            # at least one core query term in the title and two in title+description.
            title = str(data.get("title", ""))
            description = str(data.get("description", ""))
            if not _relevant_result(query, title, description):
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
                      "srlimit":10, "srsearch":f"{term} {mime_query}"}
            data = requests.get(api, params=params, headers=headers, timeout=15).json()
            pages = (data.get("query") or {}).get("search") or []
            print(f"[MEDIA] Wikimedia query={term!r} {mime_query} results={len(pages)}", flush=True)
            for result in pages[:8]:
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

def youtube_video(query: str, used: set[str], dest: Path):
    """Search YouTube, then try several individual results until one downloads."""
    import shutil
    ytdlp = shutil.which("yt-dlp")
    if not ytdlp:
        print("[MEDIA] yt-dlp executable is missing", flush=True)
        return None, None

    common = [ytdlp, "--no-warnings", "--ignore-errors", "--no-progress",
              "--js-runtimes", "node", "--remote-components", "ejs:github"]
    try:
        search_cmd = common + ["--flat-playlist", "--dump-single-json", f"ytsearch15:{query}"]
        search_proc = subprocess.run(search_cmd, capture_output=True, text=True, timeout=120)
        if search_proc.returncode != 0 or not search_proc.stdout.strip():
            print(
                f"[MEDIA] YouTube search failed for {query}: "
                f"{search_proc.stderr[-900:]}",
                flush=True
            )
            return None, None
        try:
            search_data = json.loads(search_proc.stdout)
        except json.JSONDecodeError:
            print(f"[MEDIA] YouTube returned invalid search JSON for {query}: {search_proc.stdout[-500:]}", flush=True)
            return None, None

        entries = search_data.get("entries") or []
        print(f"[MEDIA] YouTube search results for {query}: {len(entries)}", flush=True)
        for entry in entries[:12]:
            video_id = str(entry.get("id") or "")
            if not video_id or video_id in used:
                continue
            duration = entry.get("duration")
            if duration is not None and not 8 <= float(duration) <= 180:
                continue
            webpage = str(entry.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}")
            outtmpl = str(dest.with_suffix(".%(ext)s"))
            for old_file in dest.parent.glob(dest.stem + ".*"):
                if old_file.is_file():
                    old_file.unlink(missing_ok=True)

            clip = None
            proc = None
            info = {}
            # Data-center IPs can be challenged by YouTube's default web client.
            # Try clients that do not require a logged-in browser session first.
            for player_client in ("android_vr", "web_embedded", "tv"):
                download_cmd = common + [
                    "--extractor-args", f"youtube:player_client={player_client}",
                    "--no-playlist", "--max-filesize", "120M",
                    "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]",
                    "--merge-output-format", "mp4", "-o", outtmpl, "--print-json", webpage
                ]
                proc = subprocess.run(download_cmd, capture_output=True, text=True, timeout=240)
                files = sorted(
                    [p for p in dest.parent.glob(dest.stem + ".*")
                     if p.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov")],
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )
                clip = next((p for p in files if p.exists() and p.stat().st_size > 100_000), None)
                if clip:
                    for line in reversed(proc.stdout.splitlines()):
                        try:
                            candidate = json.loads(line)
                            if candidate.get("id"):
                                info = candidate
                                break
                        except Exception:
                            continue
                    print(f"[MEDIA] YouTube downloaded {video_id} using {player_client}", flush=True)
                    break
                print(
                    f"[MEDIA] YouTube {video_id} via {player_client}: "
                    f"{proc.stderr[-300:]}",
                    flush=True
                )
            if not clip:
                print(
                    f"[MEDIA] YouTube candidate {video_id} unavailable: "
                    f"{proc.stderr[-450:]}",
                    flush=True
                )
                continue

            info = {}
            for line in reversed(proc.stdout.splitlines()):
                try:
                    candidate = json.loads(line)
                    if candidate.get("id"):
                        info = candidate
                        break
                except Exception:
                    continue
            used.add(video_id)
            return clip, {
                "file": str(info.get("title") or entry.get("title") or query),
                "url": str(info.get("webpage_url") or webpage),
                "license": str(info.get("license") or "YouTube source; license not verified"),
                "artist": str(info.get("uploader") or entry.get("uploader") or ""),
                "credit": str(info.get("webpage_url") or webpage),
                "source": "YouTube",
                "source_id": video_id
            }
    except Exception as exc:
        print(f"[MEDIA] YouTube error for {query}: {type(exc).__name__}: {str(exc)[:240]}", flush=True)
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
                        "fl[]": ["identifier", "title"], "rows": 10, "page": 1, "output": "json"},
                headers={"User-Agent": UA}, timeout=18)
            data.raise_for_status()
            found = data.json().get("response", {}).get("docs", [])
            print(f"[MEDIA] Internet Archive query={term!r} results={len(found)}", flush=True)
            docs.extend(found)
            if len(docs) >= 10:
                break
        for item in docs[:8]:
            ident = item.get("identifier")
            if not ident or ident in used:
                continue
            meta = requests.get(f"https://archive.org/metadata/{ident}",
                headers={"User-Agent": UA}, timeout=30).json()
            md = meta.get("metadata", {})
            title = str(item.get("title", ""))
            description = " ".join(str(md.get(key, "")) for key in
                                   ("description", "subject", "keywords", "notes", "creator"))
            if not _relevant_result(query, title, description):
                print(f"[MEDIA] Internet Archive rejected unrelated item: {title[:120]}", flush=True)
                continue
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

def _download_image(url: str, dest: Path):
    """Download and validate a still image without accepting HTML/error responses."""
    try:
        from PIL import Image
        response = requests.get(url, headers={"User-Agent": UA}, timeout=45)
        response.raise_for_status()
        if len(response.content) < 12_000 or len(response.content) > 35_000_000:
            return None
        tmp = dest.with_suffix(".part")
        tmp.write_bytes(response.content)
        with Image.open(tmp) as im:
            im.verify()
            fmt = (im.format or "").lower()
        ext = {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}.get(fmt)
        if not ext:
            tmp.unlink(missing_ok=True)
            return None
        final = dest.with_suffix(ext)
        tmp.replace(final)
        return final
    except Exception:
        dest.with_suffix(".part").unlink(missing_ok=True)
        return None

def nasa_image(query: str, used: set[str], dest: Path):
    """NASA public image fallback with topic-specific search variants."""
    words = query.lower().split()
    terms = [query]
    if "supervolcano" in query.lower():
        terms.extend(["volcano", "volcanic eruption", "volcanic ash"])
    elif "ash" in query.lower():
        terms.extend(["volcanic ash", "volcano eruption"])
    for term in dict.fromkeys(terms):
        try:
            data = requests.get("https://images-api.nasa.gov/search",
                params={"q": term, "media_type": "image", "page_size": 30},
                headers={"User-Agent": UA}, timeout=15)
            data.raise_for_status()
            items = (data.json().get("collection") or {}).get("items") or []
            for item in items[:20]:
                meta = (item.get("data") or [{}])[0]
                ident = meta.get("nasa_id")
                title = str(meta.get("title", ""))
                desc = str(meta.get("description", ""))
                if not ident or ident in used or not _relevant_result(term, title, desc):
                    continue
                manifest = requests.get(f"https://images-api.nasa.gov/asset/{ident}",
                    headers={"User-Agent": UA}, timeout=15)
                manifest.raise_for_status()
                assets = (manifest.json().get("collection") or {}).get("items") or []
                urls = [x.get("href", "") for x in assets]
                urls = [u for u in urls if re.search(r"\.(jpg|jpeg|png)(?:$|\?)", u, re.I)]
                for url in urls[:3]:
                    path = _download_image(url, dest)
                    if path:
                        used.add(ident)
                        return path, {"file": title, "url": url,
                            "license": "NASA media usage guidance applies",
                            "artist": meta.get("center", "NASA"), "credit": desc[:500],
                            "source_id": ident, "source": "NASA", "kind": "licensed_image_animated"}
        except Exception as exc:
            print(f"[MEDIA] NASA image query={term!r} error={type(exc).__name__}: {str(exc)[:140]}", flush=True)
    return None, None

def commons_image(query: str, used: set[str], dest: Path):
    """Wikimedia Commons still-image fallback, restricted to reusable licenses."""
    api = "https://commons.wikimedia.org/w/api.php"
    terms = list(dict.fromkeys([query, " ".join(query.split()[:3]), query.split()[0] if query.split() else query]))
    for term in terms:
        try:
            search = requests.get(api, params={"action":"query","format":"json","list":"search",
                "srnamespace":6,"srlimit":10,"srsearch":f"{term} filemime:image/jpeg"},
                headers={"User-Agent": UA}, timeout=15)
            search.raise_for_status()
            results = (search.json().get("query") or {}).get("search") or []
            for result in results[:8]:
                title = result.get("title", "")
                if not title or title in used:
                    continue
                detail = requests.get(api, params={"action":"query","format":"json","titles":title,
                    "prop":"imageinfo","iiprop":"url|mime|size|extmetadata"},
                    headers={"User-Agent": UA}, timeout=25)
                detail.raise_for_status()
                page = next(iter((detail.json().get("query") or {}).get("pages", {}).values()), {})
                info = (page.get("imageinfo") or [{}])[0]
                url, mime = info.get("url"), info.get("mime", "")
                if not url or mime not in ("image/jpeg","image/png","image/webp") or info.get("size",0)>35_000_000:
                    continue
                extmeta = info.get("extmetadata") or {}
                def clean(k):
                    raw = str((extmeta.get(k) or {}).get("value", ""))
                    return re.sub("<[^>]+>", "", raw).strip()
                license_name = clean("LicenseShortName")
                license_url = clean("LicenseUrl").lower()
                if any(x in license_url for x in ("/by-nc", "/by-nd", "noncommercial", "noderivatives")):
                    continue
                if not (license_name.lower() in ("cc0","public domain","pd") or
                        any(x in license_url for x in ("creativecommons.org/licenses/by/","creativecommons.org/licenses/by-sa/"))):
                    continue
                path = _download_image(url, dest)
                if path:
                    used.add(title)
                    return path, {"file": title, "url": url, "license": license_name,
                        "artist": clean("Artist"), "credit": clean("Attribution"),
                        "source": "Wikimedia Commons", "kind": "licensed_image_animated"}
        except Exception as exc:
            print(f"[MEDIA] Wikimedia image fallback error: {type(exc).__name__}: {str(exc)[:120]}", flush=True)
    return None, None

def find_image(query: str, used: set[str], dest: Path):
    for provider in (nasa_image, commons_image):
        image, attribution = provider(query, used, dest)
        if image:
            print(f"[MEDIA] {provider.__name__}: FOUND for {query}", flush=True)
            return image, attribution
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
    """Use YouTube footage only; no silent AI or third-party fallback."""
    try:
        clip, attribution = youtube_video(query, used, dest)
        print(f"[MEDIA] YouTube: {'FOUND' if clip else 'no match'} for {query}", flush=True)
        return clip, attribution
    except Exception as exc:
        print(f"[MEDIA] YouTube ERROR {type(exc).__name__}: {str(exc)[:240]}", flush=True)
        return None, None


async def _make_voice(text: str, path: Path):
    words = len(re.findall(r"\b[\w'-]+\b", text))
    # Aim for roughly 55 seconds while keeping a natural speaking rate.
    rate = round((words / 145 / (55 / 60) - 1) * 100)
    rate = max(-10, min(30, rate))
    communicate = edge_tts.Communicate(text, VOICE, rate=f"{rate:+d}%")
    await communicate.save(str(path))


def _ffprobe_streams(path: Path):
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
    ], text=True)
    return json.loads(raw)


def _render_scene(source: Path, destination: Path, seconds: float):
    duration = probe_duration(source)
    if duration < 2:
        raise RuntimeError(f"Downloaded YouTube source is too short: {source.name}")
    segment = min(seconds, duration)
    offset = max(0.0, min(duration - segment, (duration - segment) * 0.27))
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,fps=30,format=yuv420p"
    )
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-stream_loop", "-1", "-ss", f"{offset:.3f}", "-i", str(source), "-t", f"{seconds:.3f}",
        "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-movflags", "+faststart", str(destination)
    ])
    return segment


def build(slot: int):
    OUT.mkdir(parents=True, exist_ok=True)
    topic = TOPICS[slot % len(TOPICS)]
    slug = re.sub(r"[^a-z0-9]+", "_", topic["title"].lower()).strip("_")[:48]
    scene_dir = OUT / f"cinematic_{slug}_{slot}"
    scene_dir.mkdir(parents=True, exist_ok=True)

    narration = " ".join([
        topic["hook"],
        *[f"{fact} {detail}" for fact, detail in zip(topic["facts"], topic["details"])]
    ])
    voice_path = OUT / f"voice_{slot}.mp3"
    asyncio.run(_make_voice(narration, voice_path))
    voice_seconds = probe_duration(voice_path)
    if not 45 <= voice_seconds <= 64:
        raise RuntimeError(
            f"Narration duration outside required 45-64 seconds: {voice_seconds:.1f}s. "
            "Adjust narration or TTS rate before publishing."
        )

    segment_seconds = voice_seconds / 5
    used_ids = set()
    rendered_scenes = []
    source_records = []

    for index, query in enumerate(topic["queries"], start=1):
        source_path = scene_dir / f"youtube_source_{index:02d}.mp4"
        clip, attribution = find_video(query, used_ids, source_path)
        if not clip:
            raise RuntimeError(
                f"YOUTUBE-ONLY BUILD FAILED: no usable YouTube footage for scene {index}: {query}"
            )
        scene_path = scene_dir / f"scene_{index:02d}.mp4"
        _render_scene(clip, scene_path, segment_seconds)
        rendered_scenes.append(scene_path)
        record = dict(attribution or {})
        record.update({
            "kind": "youtube_video",
            "query": query,
            "scene": index,
            "source": "YouTube",
        })
        source_records.append(record)
        print(f"[BUILD] Rendered scene {index}/5 from YouTube: {record.get('url', '')}", flush=True)

    concat_file = scene_dir / "scenes.txt"
    concat_file.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in rendered_scenes),
        encoding="utf-8"
    )
    silent_video = scene_dir / "joined_scenes.mp4"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(silent_video)
    ])

    final_video = OUT / f"short_{slot}.mp4"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(silent_video), "-i", str(voice_path),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", f"{voice_seconds:.3f}", "-movflags", "+faststart", str(final_video)
    ])

    streams = _ffprobe_streams(final_video).get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
    if (video_stream.get("width"), video_stream.get("height")) != (W, H):
        raise RuntimeError("Rendered output is not 1080x1920.")
    if not audio_stream:
        raise RuntimeError("Rendered output has no narration audio.")

    metadata = {
        "title": topic["title"],
        "hook": topic["hook"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "slot": slot,
        "duration_seconds": round(probe_duration(final_video), 2),
        "voice_duration_seconds": round(voice_seconds, 2),
        "resolution": f"{W}x{H}",
        "visual_type": "five_distinct_animated_scenes",
        "quality_gate": "passed",
        "sources": source_records,
        "narration": narration,
        "video_file": final_video.name,
        "note": "YouTube footage sources are recorded for manual rights and attribution review before publication."
    }
    metadata_path = OUT / f"short_{slot}.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[BUILD] SUCCESS: {final_video} ({metadata['duration_seconds']}s)", flush=True)
    return final_video


def main():
    parser = argparse.ArgumentParser(description="Build a cinematic YouTube-footage Short.")
    parser.add_argument("--slot", type=int, default=0)
    args = parser.parse_args()
    build(args.slot)


if __name__ == "__main__":
    main()
