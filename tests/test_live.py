"""Live tests — hit the real mediathekviewweb.de API. Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set MEDIATHEK_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from mediathek_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("MEDIATHEK_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="MEDIATHEK_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_search_live(self):
        out = json.loads(srv.mediathek_search_programmes("Tagesschau", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(p["title"] and p["channel"] for p in out["programmes"]))
        self.assertTrue(all(p["video_url"] for p in out["programmes"]))
        print(f"\nLIVE search 'Tagesschau': {out['count']} results, "
              f"total {out['total_results']}")

    def test_latest_live(self):
        out = json.loads(srv.mediathek_latest_broadcasts(limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(p["broadcast"] for p in out["programmes"]))
        print(f"\nLIVE latest: {out['programmes'][0]['channel']} — "
              f"{out['programmes'][0]['title']}")

    def test_by_channel_live(self):
        out = json.loads(srv.mediathek_by_channel("ZDF", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(p["channel"] == "ZDF" for p in out["programmes"]))
        print(f"\nLIVE ZDF newest: {out['programmes'][0]['title']}")

    def test_by_topic_live(self):
        out = json.loads(srv.mediathek_by_topic("heute journal", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(
            all(p["topic"] == "heute journal" for p in out["programmes"])
        )

    def test_programme_detail_live(self):
        found = json.loads(srv.mediathek_search_programmes("Tagesschau", limit=1))
        title = found["programmes"][0]["title"]
        out = json.loads(srv.mediathek_programme_detail(title))
        self.assertNotIn("error", out)
        self.assertEqual(out["title"], title)
        self.assertTrue(out["video_url"])
        self.assertTrue(out["video_url_hd"])
        print(f"\nLIVE detail: {title} — {out['duration']} "
              f"({out['channel']})")

    def test_list_channels_live(self):
        out = json.loads(srv.mediathek_list_channels())
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 10)
