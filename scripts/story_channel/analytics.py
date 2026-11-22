#!/usr/bin/env python3
"""Pull channel results into data/story_channel/insights.json so new stories learn from them."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import youtube_api as yt

ROOT = Path(__file__).resolve().parents[2]
INSIGHTS = ROOT / "data" / "story_channel" / "insights.json"


def main() -> int:
    if not yt.have_credentials():
        print("::notice::YouTube credentials are not configured; skipping analytics.")
        return 0
    token = yt.access_token()
    videos = yt.list_channel_videos(token)
    extra = yt.video_analytics(token)
    for video in videos:
        video.update({k: v for k, v in extra.get(video["id"], {}).items() if k != "views"})
    ranked = sorted(videos, key=lambda v: (v["views"], v.get("averageViewPercentage", 0)), reverse=True)
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "published_titles": [v["title"] for v in videos],
        "top": ranked[:5],
        "weakest": ranked[-3:] if len(ranked) > 5 else [],
        "videos": ranked,
    }
    INSIGHTS.parent.mkdir(parents=True, exist_ok=True)
    INSIGHTS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved insights for {len(videos)} videos")
    for v in ranked[:5]:
        print(f"  {v['views']:>8} views  {v.get('averageViewPercentage', '-')}% watched  {v['title'][:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
