#!/usr/bin/env python3
"""Persistent least-recently-used topic selection for Nova Shorts Factory."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Sequence


def _load(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "last_used": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("last_used"), dict):
        raise ValueError(f"Invalid topic history file: {path}")
    return data


def choose_topic(topics: Sequence[str], history_file: Path, today: str, slot: int = 0) -> int:
    """Return the least-recently-used topic index, deterministically breaking ties."""
    if not topics:
        raise ValueError("topics must not be empty")
    date_value = date.fromisoformat(today)
    history = _load(Path(history_file))
    last_used = history["last_used"]
    offset = (date_value.toordinal() + slot) % len(topics)
    return min(
        range(len(topics)),
        key=lambda index: (
            last_used.get(topics[index], ""),
            (index - offset) % len(topics),
        ),
    )


def record_topic(history_file: Path, topic: str, today: str) -> None:
    """Persist a topic only after its video has passed output validation."""
    date.fromisoformat(today)
    path = Path(history_file)
    history = _load(path)
    history.setdefault("version", 1)
    history["last_used"][topic] = today
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
