#!/usr/bin/env python3
"""Write one original English survival story (JSON) with a free Groq model.

Needs GROQ_API_KEY. Reads data/story_channel/character.json (your own character)
and, when available, data/story_channel/insights.json (what worked on your channel).
"""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "story_channel"
OUT = ROOT / "output" / "story"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELS = [os.getenv("GROQ_MODEL", "").strip(), "llama-3.3-70b-versatile", "openai/gpt-oss-120b", "llama-3.1-8b-instant"]
MIN_SCENES, MIN_WORDS = 30, 1100


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def build_prompt(character: dict, insights: dict) -> tuple[str, str]:
    top = [f'- "{v["title"]}" ({v["views"]} views, {v.get("averageViewPercentage", "n/a")}% watched)'
           for v in insights.get("top", [])[:5]]
    used = insights.get("published_titles", [])[:60]
    system = (
        "You write original, factual-feeling survival stories for an animated YouTube channel narrated in English. "
        "Return ONLY valid JSON. Never imitate or retell another creator's story; invent a fresh scenario. "
        "Keep it family-friendly with no graphic injury. Survival details must be realistic and not dangerous advice."
    )
    user = f"""Write ONE new story about a character named {character['name']} ({character['look']}) in an extreme survival challenge
(e.g. lost somewhere remote, stranded, trapped by weather). Pick a fresh location and a numeric hook such as "30 Days ...".

Structure: shocking first line hook, escalating problems day by day, clever realistic survival decisions, a turning point,
an emotional ending, and a short closing line asking viewers to subscribe. Simple spoken English (grade 6-8), short sentences.

Length: {MIN_SCENES + 6} scenes. Each scene narration 30-40 words (total about 1300-1500 words, roughly 9-10 minutes).

{"Past videos that performed best (learn the pattern, do NOT repeat them):" + chr(10) + chr(10).join(top) if top else ""}
{"Titles already published (do not repeat): " + "; ".join(used) if used else ""}

JSON schema:
{{
 "title": "max 90 chars, curiosity-driven, includes the numeric hook",
 "description": "2-3 sentence summary, then a line saying visuals and voice are AI-generated, then 3 hashtags",
 "tags": ["10-15 short tags"],
 "thumb_text": "2-4 punchy words for the thumbnail",
 "thumbnail_visual": "one vivid scene description for the thumbnail image, character reacting with strong emotion",
 "scenes": [
   {{"narration": "30-40 words", "visual": "concrete visual description of the moment (setting, action, mood, no text)", "has_character": true}}
 ]
}}"""
    return system, user


def call_groq(system: str, user: str) -> dict:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise SystemExit("GROQ_API_KEY is missing")
    last = None
    for model in [m for m in dict.fromkeys(MODELS) if m]:
        resp = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {key}"}, timeout=180, json={
            "model": model, "temperature": 0.9, "max_tokens": 7000,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        })
        if resp.status_code == 200:
            print(f"[STORY] model: {model}", flush=True)
            return json.loads(resp.json()["choices"][0]["message"]["content"])
        last = f"{model}: {resp.status_code} {resp.text[:200]}"
        print(f"[STORY] {last}", flush=True)
    raise SystemExit(f"All Groq models failed. Last error: {last}")


def validate(story: dict) -> list[str]:
    problems = []
    for field in ("title", "description", "tags", "thumb_text", "thumbnail_visual", "scenes"):
        if not story.get(field):
            problems.append(f"missing {field}")
    scenes = story.get("scenes") or []
    if len(scenes) < MIN_SCENES:
        problems.append(f"only {len(scenes)} scenes (need {MIN_SCENES}+)")
    words = sum(len(re.findall(r"\b[\w'-]+\b", s.get("narration", ""))) for s in scenes)
    if words < MIN_WORDS:
        problems.append(f"only {words} narration words (need {MIN_WORDS}+)")
    for i, s in enumerate(scenes, 1):
        if not s.get("narration") or not s.get("visual"):
            problems.append(f"scene {i} incomplete")
            break
    return problems


def main() -> int:
    character = _load(DATA / "character.json", {})
    if not character:
        raise SystemExit("data/story_channel/character.json is missing")
    system, user = build_prompt(character, _load(DATA / "insights.json", {}))
    story = None
    for attempt in range(1, 4):
        candidate = call_groq(system, user)
        problems = validate(candidate)
        if not problems:
            story = candidate
            break
        print(f"[STORY] attempt {attempt} rejected: {'; '.join(problems)}", flush=True)
        user += f"\n\nYour previous answer was rejected: {'; '.join(problems)}. Fix this and return the full JSON again."
    if not story:
        raise SystemExit("Could not get a valid story after 3 attempts")
    story["character"] = character
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "story.json").write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding="utf-8")
    words = sum(len(s["narration"].split()) for s in story["scenes"])
    print(f"[STORY] {story['title']} | {len(story['scenes'])} scenes | ~{words} words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
