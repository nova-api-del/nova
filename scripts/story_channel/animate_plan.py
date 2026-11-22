#!/usr/bin/env python3
"""Choose which scenes of a story get an AI-animated clip (the rest stay stills with camera moves)."""
from __future__ import annotations


def pick_animation_scenes(story: dict, limit: int = 5) -> list[int]:
    """Return 1-based scene numbers to animate, at most `limit`.

    Uses the story's own `key_moment: true` flags when present (the hook and the big turns),
    always includes scene 1 (the hook), and otherwise spreads the picks evenly.
    """
    scenes = story.get("scenes") or []
    total = len(scenes)
    if total == 0 or limit <= 0:
        return []
    flagged = [i + 1 for i, s in enumerate(scenes) if s.get("key_moment")]
    picks = [1] + [n for n in flagged if n != 1]
    if len(picks) < min(limit, total):
        step = max(1, total // limit)
        for n in range(1, total + 1, step):
            if n not in picks:
                picks.append(n)
            if len(picks) >= limit:
                break
    return sorted(set(picks))[:limit]
