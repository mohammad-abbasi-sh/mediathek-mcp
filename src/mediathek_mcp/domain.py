"""Domain logic: shape MediathekViewWeb responses into compact dicts (stdlib only)."""
from __future__ import annotations

from datetime import datetime, timezone

# Channels in the MediathekView film list, as seen in live probes and the
# project's public channel list. The API itself has no channel-list
# endpoint, so this is a curated list — search_by_channel passes any
# other channel name through to the API unchanged.
CHANNELS = [
    {"channel": "ARD", "name": "Das Erste"},
    {"channel": "ZDF", "name": "Zweites Deutsches Fernsehen"},
    {"channel": "3sat", "name": "3sat"},
    {"channel": "ARTE.DE", "name": "ARTE (deutsch)"},
    {"channel": "ARTE.FR", "name": "ARTE (französisch)"},
    {"channel": "PHOENIX", "name": "Phoenix"},
    {"channel": "tagesschau24", "name": "tagesschau24"},
    {"channel": "KiKA", "name": "Kinderkanal"},
    {"channel": "ONE", "name": "ONE"},
    {"channel": "WDR", "name": "Westdeutscher Rundfunk"},
    {"channel": "NDR", "name": "Norddeutscher Rundfunk"},
    {"channel": "BR", "name": "Bayerischer Rundfunk"},
    {"channel": "SWR", "name": "Südwestrundfunk"},
    {"channel": "MDR", "name": "Mitteldeutscher Rundfunk"},
    {"channel": "HR", "name": "Hessischer Rundfunk"},
    {"channel": "RBB", "name": "Rundfunk Berlin-Brandenburg"},
    {"channel": "SR", "name": "Saarländischer Rundfunk"},
]

_KNOWN = {c["channel"].lower(): c["channel"] for c in CHANNELS}

# Broad single-letter query used for "latest broadcasts": the API returns
# nothing for an empty query and no wildcard exists, so we search the
# most common letter across title/topic/description, newest first. The
# result is effectively the newest programmes in the film list.
LATEST_QUERY = "e"
LATEST_FIELDS = ["title", "topic", "description"]


def validate_limit(limit: int) -> int:
    """Clamp/validate the page size (API-side max is 50)."""
    if not 1 <= limit <= 50:
        raise ValueError(f"limit out of range: {limit} (expected 1..50)")
    return limit


def normalise_channel(channel: str) -> str:
    """Canonical capitalisation for known channels; unknown names pass through."""
    key = (channel or "").strip()
    if not key:
        raise ValueError("channel must not be empty")
    return _KNOWN.get(key.lower(), key)


def _iso(ts) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


def _duration_hms(seconds) -> str | None:
    if seconds is None:
        return None
    try:
        s = int(seconds)
    except (TypeError, ValueError):
        return None
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def compact_programme(p: dict) -> dict:
    """One programme, compact: no internal ids beyond the API's own id."""
    return {
        "id": p.get("id") or "",
        "channel": p.get("channel") or "",
        "topic": p.get("topic") or "",
        "title": p.get("title") or "",
        "description": p.get("description") or "",
        "broadcast": _iso(p.get("timestamp")),
        "duration_seconds": p.get("duration"),
        "duration": _duration_hms(p.get("duration")),
        "video_url": p.get("url_video") or "",
        "video_url_hd": p.get("url_video_hd") or "",
        "video_url_low": p.get("url_video_low") or "",
        "subtitle_url": p.get("url_subtitle") or "",
        "website_url": p.get("url_website") or "",
        "size_bytes": p.get("size"),
    }


def compact_results(result: dict) -> dict:
    """The API's result object, compacted for tool output."""
    info = result.get("queryInfo") or {}
    return {
        "total_results": info.get("totalResults"),
        "film_list_updated": _iso(info.get("filmlisteTimestamp")),
        "count": len(result.get("results") or []),
        "programmes": [compact_programme(p) for p in result.get("results") or []],
    }


def find_exact_title(results: list, title: str, channel: str | None) -> dict | None:
    """First result whose title matches exactly (case-insensitive), optionally
    restricted to one channel. Returns the raw API entry or None."""
    want = (title or "").strip().lower()
    chan = (channel or "").strip().lower()
    for p in results or []:
        if (p.get("title") or "").strip().lower() != want:
            continue
        if chan and (p.get("channel") or "").strip().lower() != chan:
            continue
        return p
    return None
