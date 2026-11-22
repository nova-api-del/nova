#!/usr/bin/env python3
"""Nova GTA 6 long-form factory: ~8-10 minute cinematic trailer-footage documentary."""
from __future__ import annotations
from pathlib import Path
import sys, re, json, asyncio, os
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cinematic_shorts as cs

# Warm, conversational neural narration.
cs.VOICE = os.getenv("GTA6_LONG_VOICE", "en-US-AndrewNeural")

TOPIC = {
    "title": "GTA 6: The Biggest Details Hidden in Vice City",
    "hook": "GTA 6 is not just bringing Vice City back. Rockstar is building a world that looks bigger, busier, stranger, and more alive than anything the series has shown before.",
    "sections": [
        ("The return of Vice City", "The first thing that stands out is the return of Vice City, but this is not a simple remake of the old map. The modern setting is surrounded by the wider state of Leonida, giving the story room to move between dense streets, highways, beaches, rural roads, wetlands, and small communities."),
        ("Jason and Lucia", "At the center are Jason and Lucia, a pair whose relationship sits directly inside the criminal story. The trailers make their partnership feel important, because every escape, robbery, argument, and quiet moment can change the way we understand their lives."),
        ("A world built for modern crime", "This version of Vice City is set in a world shaped by phones, social media, viral moments, cameras, businesses, traffic, nightlife, and constant public activity. That changes what a GTA city can feel like. The environment is no longer just scenery between missions; it can become part of the story."),
        ("The nightlife", "Vice City has always been associated with nightlife, neon, music, luxury, and danger. GTA 6 appears to push that identity much further, with crowded venues, illuminated streets, waterfront locations, and scenes that make the city feel active after dark rather than simply changing the lighting."),
        ("The beaches", "The coastline is another major part of the visual identity. Beaches, marinas, boats, highways, and waterfront neighborhoods create a sharp contrast with the darker criminal side of the story. Rockstar can use those contrasts to make the same state feel like several different worlds."),
        ("The wetlands", "Then the environment suddenly changes. Leonida is not only skyscrapers and beaches. Wetlands, dirt roads, vegetation, wildlife, and remote areas give the map a completely different atmosphere. These spaces could also create missions that feel nothing like a traditional city chase."),
        ("The highways", "Highways are more important than they first appear. A large open-world crime story needs routes connecting distant locations, and the trailers show a world where driving itself can become part of the spectacle. Traffic, bridges, exits, roadside businesses, and changing scenery make long journeys feel like events."),
        ("Cars and movement", "Vehicles are one of the foundations of GTA, and the footage shows a huge variety of modern cars and driving situations. The important detail is not simply how many vehicles exist, but how naturally they fit into the world around them."),
        ("Crowds", "Crowds are another huge part of the illusion. A convincing city needs people doing different things instead of standing around like background props. GTA 6 footage repeatedly emphasizes crowds, pedestrians, performers, customers, and people reacting to their surroundings."),
        ("Wildlife", "Wildlife expands that feeling beyond the cities. Animals make remote environments feel less empty and create the impression that Leonida is an ecosystem rather than a collection of mission locations. That matters because exploration becomes more interesting when something unexpected can happen away from the main roads."),
        ("The small details", "The most impressive details may be the ones that last only a second. Reflections, weather, signs, storefronts, clothing, vehicle interiors, animations, phone screens, and tiny background events all contribute to the same goal: making the world feel observed rather than generated."),
        ("The social media era", "GTA 6 also seems designed for an era where almost every strange event can become a piece of online content. That gives Rockstar a new way to satirize modern culture. A character can be ridiculous, a crowd can react, and the world can feel like it is constantly recording itself."),
        ("The criminal dynamic", "The biggest question is how all this detail serves the story. Jason and Lucia are not simply tourists in Vice City. Their choices put them inside a network of crime, money, pressure, and consequences. A huge world only matters if the characters have reasons to move through it."),
        ("From luxury to danger", "One of the strongest visual contrasts is the jump from luxury to danger. One moment can look like a holiday destination; the next can feel like a crime scene. That contrast is exactly what makes Vice City such a strong setting for a modern GTA game."),
        ("How big is Leonida?", "The trailers reveal enough variety to suggest a world that extends far beyond the familiar city skyline. The real test will be how much of that variety players can actually explore, and how much of it changes when the player interacts with it."),
        ("The animation detail", "Character animation is another area where the footage stands out. Body movement, facial reactions, driving poses, swimming, walking, fighting, and small interactions all sell the idea that characters have weight and behavior rather than simply moving from marker to marker."),
        ("The cinematic presentation", "Rockstar's trailers are edited to show the world at its most cinematic, so we should separate what is confirmed gameplay from what is trailer presentation. Even so, the density of locations, characters, vehicles, and environmental detail gives a strong indication of the production ambition."),
        ("What we still do not know", "There are still major questions. We do not know every system, every mission, every location, or exactly how the final game will behave once millions of players start interacting with it. The trailers are evidence of the direction, not a complete manual for the finished game."),
        ("Why the wait matters", "That uncertainty is part of the excitement. GTA 6 has become one of the most anticipated games ever, and every new frame gets examined for clues. The reason is simple: Rockstar is not just returning to Vice City. It is attempting to redefine what a living open world can look like."),
        ("The first five minutes matter", "A strong opening has to do more than list features. It needs to give viewers a reason to stay. That is why the most interesting question is not how many buildings are on the map, but what could happen when Jason and Lucia move through a city that never seems to stand still. Every street can introduce a new character, a new risk, or an unexpected opportunity."),
        ("The relationship at the center", "The partnership between Jason and Lucia could give the entire adventure its emotional engine. Crime stories become memorable when the people involved have something to lose. Trust, loyalty, ambition, and fear can turn even a simple plan into a complicated decision. The trailers hint at that tension, but the full story will reveal how far each character is willing to go."),
        ("A city that tells stories", "Look beyond the main characters for a moment. A crowded gas station, a roadside shop, a busy beach, or a late-night restaurant can make a location feel like it existed before the player arrived. These little moments are powerful because they suggest that the world has its own rhythm, even when the player is not watching."),
        ("The sound of Vice City", "Visuals are only half of immersion. Engines passing in the distance, conversations in public spaces, music spilling out of clubs, waves along the coast, and sudden changes in the weather can make a location feel real. A carefully layered soundscape can make the difference between looking at a digital city and feeling as if you are standing inside it."),
        ("Weather and atmosphere", "Weather can also change the personality of a place. A sunny street, a humid evening, a sudden storm, or reflections after rainfall can transform the same route into a different experience. If these conditions influence traffic, visibility, crowds, and the mood of a scene, they become more than decoration."),
        ("The freedom to explore", "Open-world games are at their best when curiosity is rewarded. A road that looks unimportant might lead to a hidden location. A quiet stretch of coastline might reveal a new activity. A distant building might become the setting for a mission later in the story. The promise of Leonida is that exploration could feel worthwhile even when there is no mission marker telling players where to go."),
        ("The pressure of every decision", "A criminal story also needs consequences. A chase is exciting in the moment, but it becomes more meaningful when the player feels the pressure behind it. Who can be trusted? What happens when a plan goes wrong? How much attention is too much? The strongest missions make players think about those questions while the action is unfolding."),
        ("Separating fact from speculation", "There is one important thing to remember while studying every trailer frame: not every detail confirms a gameplay feature. Some shots are cinematic, some are carefully staged, and some may represent systems that change before release. It is exciting to make predictions, but the most honest breakdown keeps confirmed footage separate from theories."),
        ("What could make it unforgettable", "The graphics will attract attention, but the moments players remember may be much smaller. A conversation that changes the mood, a close escape through traffic, a surprising encounter away from the city, or a quiet drive after a difficult mission can stay with someone longer than a spectacular explosion. Great open worlds create stories players make themselves."),
        ("The countdown to Leonida", "Until the game is in players' hands, every new trailer will create more questions than answers. That is part of the fun. We can examine the locations, compare details, and debate what the footage might mean, while remembering that the finished experience is what matters. When the doors finally open, the real test will be whether Leonida feels like a world worth getting lost in."),
        ("The final question", "When players finally enter Leonida, the most important test will not be the graphics. It will be whether the world feels unpredictable. If the streets, beaches, wetlands, highways, crowds, characters, and wildlife all work together, Vice City could become a place players remember for years.")
    ],
    "queries": [
        "GTA 6 official trailer Vice City Rockstar",
        "GTA VI Jason Lucia official trailer",
        "GTA 6 Vice City night neon trailer",
        "GTA 6 beach Vice City trailer",
        "GTA 6 Leonida highway trailer",
        "GTA 6 swamp wetlands Leonida trailer",
        "GTA 6 wildlife animals trailer",
        "GTA 6 Jason driving car trailer",
        "GTA 6 Lucia driving car trailer",
        "GTA 6 nightclub Vice City trailer",
        "GTA 6 crowd pedestrians Vice City trailer",
        "GTA 6 social media phone trailer",
        "GTA 6 police chase trailer",
        "GTA 6 boat marina trailer",
        "GTA 6 helicopter trailer",
        "GTA 6 rural Leonida trailer",
        "GTA 6 motel trailer",
        "GTA 6 highway traffic trailer",
        "GTA 6 Vice City downtown trailer",
        "GTA 6 sunset beach trailer",
        "GTA 6 swamp boat trailer",
        "GTA 6 Jason Lucia car scene trailer",
        "GTA 6 Vice City street daytime trailer",
        "GTA 6 Vice City nightlife trailer",
        "GTA 6 Florida inspired locations trailer",
        "GTA 6 Rockstar gameplay footage",
        "GTA 6 Vice City cars trailer",
        "GTA 6 Leonida locations trailer",
        "GTA 6 characters trailer Rockstar",
        "GTA 6 trailer details Vice City"
    ]
}

def make_narration():
    return " ".join([TOPIC["hook"]] + [f"{h}. {body}" for h, body in TOPIC["sections"]])

async def make_voice(text, path):
    # A steady -5% pace sounds less rushed and leaves room for emphasis.
    os.environ["TTS_FIXED_RATE"] = os.getenv("TTS_FIXED_RATE", "-5")
    return await cs._make_voice(text, path)

def build(slot: int):
    cs.OUT.mkdir(parents=True, exist_ok=True)
    scene_dir = cs.OUT / f"gta6_long_{slot}"
    scene_dir.mkdir(parents=True, exist_ok=True)
    narration = make_narration()
    voice_path = cs.OUT / f"gta6_long_voice_{slot}.mp3"
    subtitle_path = asyncio.run(make_voice(narration, voice_path))
    voice_seconds = cs.probe_duration(voice_path)
    if not 480 <= voice_seconds <= 660:
        raise RuntimeError(f"GTA6 long narration must be 8-11 minutes; got {voice_seconds:.1f}s")
    segment_seconds = voice_seconds / len(TOPIC["queries"])
    used, scenes, sources = set(), [], []
    for i, query in enumerate(TOPIC["queries"], 1):
        source = scene_dir / f"source_{i:02d}.mp4"
        clip, attribution = cs.find_video(query, used, source)
        if not clip:
            raise RuntimeError(f"YOUTUBE-ONLY BUILD FAILED at scene {i}: {query}")
        rendered = scene_dir / f"scene_{i:02d}.mp4"
        cs._render_scene(clip, rendered, segment_seconds)
        scenes.append(rendered)
        rec = dict(attribution or {})
        rec.update({"scene": i, "query": query, "kind": "youtube_video", "source": "YouTube"})
        sources.append(rec)
        print(f"[BUILD] {i}/{len(TOPIC['queries'])} ready", flush=True)
    concat = scene_dir / "scenes.txt"
    concat.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in scenes), encoding="utf-8")
    silent = scene_dir / "joined.mp4"
    cs.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(concat),
            "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-an","-movflags","+faststart",str(silent)])
    final = cs.OUT / f"gta6_long_{slot}.mp4"
    cs.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(silent),"-i",str(voice_path),
            "-map","0:v:0","-map","1:a:0","-vf",f"subtitles={subtitle_path.as_posix()}",
            "-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","192k","-ar","48000","-t",f"{voice_seconds:.3f}",
            "-movflags","+faststart",str(final)])
    streams = cs._ffprobe_streams(final).get("streams", [])
    v = next((s for s in streams if s.get("codec_type")=="video"), {})
    a = next((s for s in streams if s.get("codec_type")=="audio"), {})
    if (v.get("width"),v.get("height")) != (1080,1920) or not a:
        raise RuntimeError("Final GTA6 long video format validation failed")
    meta = {
        "title": TOPIC["title"], "hook": TOPIC["hook"], "duration_seconds": round(cs.probe_duration(final),2),
        "resolution":"1080x1920", "scene_count":len(scenes), "quality_gate":"passed",
        "visual_type":"30 distinct animated YouTube-footage scenes", "sources":sources,
        "narration":narration, "video_file":final.name,
        "note":"YouTube footage sources are recorded for manual rights and attribution review before publication."
    }
    (cs.OUT / f"gta6_long_{slot}.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"[BUILD] SUCCESS: {final} ({meta['duration_seconds']}s)", flush=True)
    return final

if __name__ == "__main__":
    build(0)
