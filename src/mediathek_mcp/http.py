"""HTTP layer for mediathek_mcp — plain httpx POSTs against the free
MediathekViewWeb API (mediathekviewweb.de/api/query).

No key, no login. The API is a community service over the public film
list of the German public broadcasters (ARD, ZDF, 3sat, ARTE, Phoenix
and the regional channels). One POST per query; the body selects the
fields to search, sort order and page size.
"""
from __future__ import annotations

import os
import time
import ssl

import httpx

BASE = "https://mediathekviewweb.de/api/query"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
TIMEOUT = 25.0
MAX_SIZE = 50


class MediathekError(RuntimeError):
    pass


def _verify():
    """TLS trust store: the OS bundle when present, else httpx/certifi.

    The OS bundle matters behind MITM egress proxies (their CA is in the
    system store, not in certifi) and is the right default on Linux
    anyway; on systems without it we fall back to certifi.
    """
    for path in (
        "/etc/ssl/certs/ca-certificates.crt",
        ssl.get_default_verify_paths().openssl_cafile,
    ):
        if path and os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return True


def _client() -> httpx.Client:
    # NOTE: we read the proxy URL from the environment but never log it.
    # trust_env=False because httpx fails to parse bracketed IPv6 entries
    # (e.g. [::1]) that some environments put in no_proxy.
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    return httpx.Client(
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        timeout=TIMEOUT,
        proxy=proxy or None,
        trust_env=False,
        verify=_verify(),
    )


def query(
    queries: list[dict],
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    size: int = 10,
    offset: int = 0,
) -> dict:
    """Run one MediathekViewWeb query and return the ``result`` object.

    ``queries`` is a list of {"fields": [...], "query": "..."} objects
    (OR-combined by the API). ``sort_by`` is "timestamp" (newest first
    with desc) or "title". Raises MediathekError on any failure.
    """
    if not 1 <= size <= MAX_SIZE:
        raise MediathekError(f"size out of range: {size} (expected 1..{MAX_SIZE})")
    body = {
        "queries": queries,
        "sortBy": sort_by,
        "sortOrder": sort_order,
        "future": False,
        "offset": max(0, offset),
        "size": size,
    }
    last_exc: Exception | None = None
    r: httpx.Response | None = None
    for attempt in range(2):
        try:
            with _client() as c:
                r = c.post(BASE, json=body)
        except httpx.HTTPError as e:
            last_exc = e
            if attempt == 0:
                time.sleep(1.0)
                continue
            raise MediathekError(f"network error querying MediathekViewWeb: {e}") from e
        if r.status_code in (429, 500, 502, 503):
            if attempt == 0:
                time.sleep(1.0)
                continue
        break
    assert r is not None  # loop always assigns r or raises
    if r.status_code == 429:
        raise MediathekError(
            "MediathekViewWeb rate-limited the request (HTTP 429) — try again later"
        )
    if r.status_code != 200:
        raise MediathekError(
            f"MediathekViewWeb returned HTTP {r.status_code} for {BASE}"
        )
    try:
        data = r.json()
    except ValueError as e:
        raise MediathekError("MediathekViewWeb returned invalid JSON") from e
    if data.get("err"):
        raise MediathekError(f"MediathekViewWeb error: {data['err']}")
    result = data.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("results"), list):
        raise MediathekError("unexpected MediathekViewWeb response shape")
    return result


def search(
    fields: list[str],
    text: str,
    size: int = 10,
    sort_by: str = "timestamp",
) -> dict:
    """Single-field-set text search; returns the ``result`` object."""
    return query(
        [{"fields": fields, "query": text}],
        sort_by=sort_by,
        size=size,
    )


def health_check() -> dict:
    """One polite probe of the source site.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `mediathek_health` tool
    and the daily smoke CI. Added 2026-11-10 (fleet audit fix).
    """
    url = "https://mediathekviewweb.de/api/query"
    try:
        search(["title"], "a", size=1)
    except MediathekError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
