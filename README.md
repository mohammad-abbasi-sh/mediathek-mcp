# mediathek-mcp 📺

mcp-name: io.github.mohammad-abbasi-sh/mediathek-mcp

Unofficial **read-only** MCP server for the **German Mediathek** via the free [MediathekViewWeb](https://mediathekviewweb.de) API — search the programmes of ARD, ZDF, 3sat, ARTE, Phoenix, tagesschau24, KiKA and the regional channels. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory" (Sepehr-style pipeline). Not affiliated with MediathekView, ARD or ZDF.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "mediathek": {
      "command": "uvx",
      "args": ["mediathek-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m mediathek_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `mediathek_search_programmes` | Search programmes by title, topic or description — `query` (e.g. "Tagesschau"), optional `channel` (e.g. "ZDF"), `limit` 1..50 |
| `mediathek_latest_broadcasts` | Newest programmes across all channels, newest first — `limit` 1..50 |
| `mediathek_by_channel` | Newest programmes of one channel — `channel` (e.g. "ZDF", "ARD", "3sat", "ARTE.DE", "PHOENIX"), `limit` 1..50 |
| `mediathek_by_topic` | All episodes of one show/series — `topic` (e.g. "heute journal"), `limit` 1..50 |
| `mediathek_programme_detail` | Full detail of one programme: all video URLs (low/standard/HD), subtitle URL, website link — `title` (exact), optional `channel` |
| `mediathek_list_channels` | Channels in the film list (curated list — the API has no channel-list endpoint) |

Example output (`mediathek_search_programmes` / "Tagesschau"):

```json
{"query": "Tagesschau", "channel": null, "total_results": 8823, "count": 3,
 "film_list_updated": "2026-11-09T10:19:00+00:00", "programmes": [
  {"id": "+sU90jI0m7KCrRqsj5aYEh9Owg7tr+3K9IRl39v+A8o=",
   "channel": "tagesschau24", "topic": "tagesschau in 100 Sekunden",
   "title": "tagesschau in 100 Sekunden",
   "description": "tagesschau in 100 Sekunden",
   "broadcast": "2026-11-09T04:43:00+00:00", "duration_seconds": 170,
   "duration": "2:50",
   "video_url": "https://tagesschau-progressive.ard-mcdn.de/video/2026/1109/TV-20261109-0445-5500.webxl.h264.mp4",
   "video_url_hd": "https://tagesschau-progressive.ard-mcdn.de/video/2026/1109/TV-20261109-0445-5500.webxxl.h264.mp4",
   "video_url_low": "https://tagesschau-progressive.ard-mcdn.de/video/2026/1109/TV-20261109-0257-3000.webm.h264.mp4",
   "subtitle_url": "", "website_url": "https://www.ardmediathek.de/video/...",
   "size_bytes": 40894464},
  ...]}
```

Notes:
- The film list holds ~700,000 programmes and is updated several times a day; results are newest first.
- "Latest broadcasts" searches the most common letter across title/topic/description — the API returns nothing for an empty query and has no wildcard, so this is effectively the newest programmes.
- Channel filtering in `mediathek_search_programmes` is applied client-side over the newest 50 text matches (the API has no AND query); `mediathek_by_channel` queries the channel directly.
- `total_results` is capped at 10,000 by the API for very broad queries.
- Video URLs are direct MP4 links (low / standard / HD); `subtitle_url` is empty when no subtitles exist.
- Data: MediathekViewWeb public API — no key, no login, read-only.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — offline, parses real captured API fixtures (19 tests)
- `tests/test_live.py` — cautious live requests against mediathekviewweb.de (6 tests)

Tests: 25/25 green (19 offline + 6 live, 2026-11-09).

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
