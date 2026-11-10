"""MCP server: unofficial read-only access to the German Mediathek via
MediathekViewWeb (mediathekviewweb.de) — no key, no login."""
from __future__ import annotations

import json
from datetime import datetime, timezone
import sys

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for the German Mediathek via the free \
MediathekViewWeb API (mediathekviewweb.de) — no key, no login. It \
searches the programmes of the German public broadcasters (ARD, ZDF, \
3sat, ARTE, Phoenix, tagesschau24, KiKA and the regional channels) in \
the MediathekView film list (~700,000 entries, updated several times a \
day). Searches match title, topic and description; results are newest \
first. "Latest broadcasts" searches the most common letter across \
title/topic/description because the API returns nothing for an empty \
query and has no wildcard — the result is effectively the newest \
programmes. Video URLs are direct MP4 links (low / standard / HD); \
subtitle_url is empty when no subtitles exist. Built by Mohammad Abbasi \
(mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir — Germany MCP factory.\
"""


_SOURCE = "mediathekviewweb.de"
_DISCLAIMER = "Unofficial read-only data from mediathekviewweb.de; verify on the site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)

mcp = FastMCP("mediathek-mcp", instructions=INSTRUCTIONS)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


@mcp.tool()
def mediathek_search_programmes(
    query: str, channel: str | None = None, limit: int = 10
) -> str:
    """Search Mediathek programmes by title, topic or description. \
query: free text, e.g. "Tagesschau" or "Tatort". channel: optional, \
e.g. "ZDF" (see mediathek_list_channels). limit: 1..50 (default 10)."""
    try:
        if not (query or "").strip():
            return _ok({"error": "query must not be empty"})
        lim = _dom.validate_limit(limit)
        if channel:
            # The API OR-combines query objects (no AND), so fetch the
            # newest text matches and filter to the channel client-side.
            chan = _dom.normalise_channel(channel)
            result = _http.search(
                ["title", "topic", "description"], query.strip(), size=50
            )
            filtered = [
                p for p in result.get("results") or []
                if (p.get("channel") or "").lower() == chan.lower()
            ]
            result = {**result, "results": filtered[:lim]}
            out = _dom.compact_results(result)
            out["total_results"] = len(filtered)
            out["note"] = (
                "channel filter applied client-side over the newest 50 "
                "text matches (the API has no AND query)"
            )
            return _ok({"query": query.strip(), "channel": chan, **out})
        result = _http.search(
            ["title", "topic", "description"], query.strip(), size=lim
        )
    except (_http.MediathekError, ValueError) as e:
        return _err(e)
    return _ok({"query": query.strip(), "channel": channel, **_dom.compact_results(result)})


@mcp.tool()
def mediathek_latest_broadcasts(limit: int = 10) -> str:
    """Newest programmes across all channels, newest first. \
limit: 1..50 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        result = _http.search(_dom.LATEST_FIELDS, _dom.LATEST_QUERY, size=lim)
    except (_http.MediathekError, ValueError) as e:
        return _err(e)
    return _ok(_dom.compact_results(result))


@mcp.tool()
def mediathek_by_channel(channel: str, limit: int = 10) -> str:
    """Newest programmes of one channel, newest first. channel: e.g. \
"ZDF", "ARD", "3sat", "ARTE.DE", "PHOENIX" (see mediathek_list_channels). \
limit: 1..50 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        chan = _dom.normalise_channel(channel)
        result = _http.search(["channel"], chan, size=lim)
    except (_http.MediathekError, ValueError) as e:
        return _err(e)
    return _ok({"channel": chan, **_dom.compact_results(result)})


@mcp.tool()
def mediathek_by_topic(topic: str, limit: int = 10) -> str:
    """All episodes of one show/series (topic), newest first. topic: \
e.g. "heute journal" or "Tagesschau". limit: 1..50 (default 10)."""
    try:
        if not (topic or "").strip():
            return _ok({"error": "topic must not be empty"})
        lim = _dom.validate_limit(limit)
        result = _http.search(["topic"], topic.strip(), size=lim)
    except (_http.MediathekError, ValueError) as e:
        return _err(e)
    return _ok({"topic": topic.strip(), **_dom.compact_results(result)})


@mcp.tool()
def mediathek_programme_detail(title: str, channel: str | None = None) -> str:
    """Full detail of one programme: all video URLs (low/standard/HD), \
subtitle URL and website link. title: exact programme title, e.g. \
"heute journal vom 8. November 2026 (S2026/E333)". channel: optional, \
e.g. "ZDF", to disambiguate same-named titles."""
    try:
        if not (title or "").strip():
            return _ok({"error": "title must not be empty"})
        result = _http.search(["title"], title.strip(), size=50)
        found = _dom.find_exact_title(
            result.get("results") or [],
            title.strip(),
            _dom.normalise_channel(channel) if channel else None,
        )
    except (_http.MediathekError, ValueError) as e:
        return _err(e)
    if not found:
        return _ok({
                "error": f"no programme with exact title {title.strip()!r}"
                + (f" on channel {channel!r}" if channel else ""),
                "hint": "use mediathek_search_programmes first to get an exact title",
            })
    return _ok(_dom.compact_programme(found))


@mcp.tool()
def mediathek_list_channels() -> str:
    """Channels in the MediathekView film list (curated list — the API \
has no channel-list endpoint)."""
    return _ok({
            "count": len(_dom.CHANNELS),
            "channels": _dom.CHANNELS,
            "note": "curated list of the channels in the film list; "
            "mediathek_by_channel also accepts any other channel name "
            "and passes it to the API unchanged.",
        })


@mcp.tool()
def mediathek_health() -> str:
    """Check whether mediathekviewweb.de is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
