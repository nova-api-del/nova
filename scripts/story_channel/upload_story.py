#!/usr/bin/env python3
"""Upload output/story/video.mp4 to YouTube (private by default) and set the thumbnail."""
from __future__ import annotations
import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import youtube_api as yt

OUT = Path(__file__).resolve().parents[2] / "output" / "story"


def main() -> int:
    story = json.loads((OUT / "story.json").read_text(encoding="utf-8"))
    privacy = os.getenv("YT_PRIVACY", "private").lower()
    if privacy not in ("private", "unlisted", "public"):
        raise SystemExit(f"Invalid YT_PRIVACY: {privacy}")
    token = yt.access_token()
    video_id = yt.upload_video(
        OUT / "video.mp4", story["title"], story["description"], story.get("tags", []), token,
        privacy=privacy, synthetic=os.getenv("YT_SYNTHETIC", "true").lower() == "true")
    thumb_ok = yt.set_thumbnail(video_id, OUT / "thumbnail.jpg", token) if (OUT / "thumbnail.jpg").exists() else False
    (OUT / "published.json").write_text(json.dumps(
        {"video_id": video_id, "privacy": privacy, "thumbnail_set": thumb_ok, "title": story["title"]}, indent=2))
    print(f"Uploaded: https://youtu.be/{video_id} ({privacy}); thumbnail set: {thumb_ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
