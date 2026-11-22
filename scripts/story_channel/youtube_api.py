#!/usr/bin/env python3
"""Minimal YouTube Data/Analytics API client (requests only, no Google libraries).

Secrets come from environment variables and are never printed:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""
from __future__ import annotations
import os
from datetime import date, timedelta
from pathlib import Path

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD_API = "https://www.googleapis.com/upload/youtube/v3"
ANALYTICS_API = "https://youtubeanalytics.googleapis.com/v2/reports"


class YouTubeAuthError(RuntimeError):
    pass


def have_credentials() -> bool:
    return all(os.environ.get(k, "").strip() for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))


def access_token() -> str:
    if not have_credentials():
        raise YouTubeAuthError("Missing YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN")
    resp = requests.post(TOKEN_URL, data={
        "client_id": os.environ["YT_CLIENT_ID"].strip(),
        "client_secret": os.environ["YT_CLIENT_SECRET"].strip(),
        "refresh_token": os.environ["YT_REFRESH_TOKEN"].strip(),
        "grant_type": "refresh_token",
    }, timeout=30)
    if resp.status_code != 200:
        raise YouTubeAuthError(f"Token refresh failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json()["access_token"]


def _headers(token: str, **extra) -> dict:
    return {"Authorization": f"Bearer {token}", **extra}


def upload_video(path: Path, title: str, description: str, tags: list[str], token: str,
                 privacy: str = "private", category_id: str = "24", synthetic: bool = True) -> str:
    """Resumable upload. Returns the new video id."""
    path = Path(path)
    tag_list, total = [], 0
    for tag in tags:
        tag = tag.strip().replace("<", "").replace(">", "")
        if tag and total + len(tag) + 1 <= 450:
            tag_list.append(tag)
            total += len(tag) + 1
    body = {
        "snippet": {
            "title": title[:100], "description": description[:4900], "tags": tag_list,
            "categoryId": category_id, "defaultLanguage": "en", "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy, "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": synthetic,
        },
    }
    size = path.stat().st_size
    last_error = None
    for attempt in range(1, 4):
        try:
            init = requests.post(
                f"{UPLOAD_API}/videos", params={"uploadType": "resumable", "part": "snippet,status"},
                headers=_headers(token, **{"Content-Type": "application/json; charset=UTF-8",
                                           "X-Upload-Content-Type": "video/mp4",
                                           "X-Upload-Content-Length": str(size)}),
                json=body, timeout=60)
            if init.status_code != 200:
                raise RuntimeError(f"upload init failed ({init.status_code}): {init.text[:400]}")
            session_url = init.headers["Location"]
            with path.open("rb") as handle:
                done = requests.put(session_url, data=handle, timeout=3600,
                                    headers={"Content-Type": "video/mp4", "Content-Length": str(size)})
            if done.status_code in (200, 201):
                return done.json()["id"]
            raise RuntimeError(f"upload failed ({done.status_code}): {done.text[:400]}")
        except Exception as exc:  # retry network/5xx problems, then give up
            last_error = exc
            print(f"[YT] upload attempt {attempt} failed: {str(exc)[:300]}", flush=True)
            if "(4" in str(exc) and "(429" not in str(exc):
                break
    raise RuntimeError(f"YouTube upload failed: {last_error}")


def set_thumbnail(video_id: str, image_path: Path, token: str) -> bool:
    resp = requests.post(f"{UPLOAD_API}/thumbnails/set", params={"videoId": video_id},
                         headers=_headers(token, **{"Content-Type": "image/jpeg"}),
                         data=Path(image_path).read_bytes(), timeout=120)
    if resp.status_code != 200:
        print(f"[YT] thumbnail not set ({resp.status_code}): {resp.text[:300]}", flush=True)
        return False
    return True


def list_channel_videos(token: str, limit: int = 50) -> list[dict]:
    chan = requests.get(f"{API}/channels", params={"part": "contentDetails,snippet", "mine": "true"},
                        headers=_headers(token), timeout=30)
    chan.raise_for_status()
    items = chan.json().get("items") or []
    if not items:
        return []
    uploads = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    pl = requests.get(f"{API}/playlistItems", params={"part": "contentDetails", "playlistId": uploads,
                      "maxResults": min(limit, 50)}, headers=_headers(token), timeout=30)
    pl.raise_for_status()
    ids = [x["contentDetails"]["videoId"] for x in pl.json().get("items", [])]
    if not ids:
        return []
    vids = requests.get(f"{API}/videos", params={"part": "snippet,statistics,contentDetails,status",
                        "id": ",".join(ids)}, headers=_headers(token), timeout=30)
    vids.raise_for_status()
    out = []
    for v in vids.json().get("items", []):
        st = v.get("statistics", {})
        out.append({
            "id": v["id"], "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"],
            "privacy": (v.get("status") or {}).get("privacyStatus"),
            "duration": v["contentDetails"]["duration"],
            "views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)),
            "comments": int(st.get("commentCount", 0)),
        })
    return out


def video_analytics(token: str, days: int = 28) -> dict[str, dict]:
    """Per-video retention numbers. Returns {} when the analytics scope is missing."""
    end = date.today()
    resp = requests.get(ANALYTICS_API, params={
        "ids": "channel==MINE", "startDate": (end - timedelta(days=days)).isoformat(),
        "endDate": end.isoformat(), "dimensions": "video", "sort": "-views", "maxResults": 50,
        "metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained",
    }, headers=_headers(token), timeout=30)
    if resp.status_code != 200:
        print(f"[YT] analytics unavailable ({resp.status_code}): {resp.text[:200]}", flush=True)
        return {}
    cols = [c["name"] for c in resp.json().get("columnHeaders", [])]
    result = {}
    for row in resp.json().get("rows", []):
        item = dict(zip(cols, row))
        result[item.pop("video")] = item
    return result
