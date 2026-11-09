"""Offline tests — parse real captured MediathekViewWeb responses, no network."""
import json
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from mediathek_mcp import domain as dom
from mediathek_mcp import server as srv

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def _result(name):
    return _load(name)["result"]


class TestCompact(unittest.TestCase):
    def test_search_fixture_shape(self):
        out = dom.compact_results(_result("search-tagesschau.json"))
        self.assertEqual(out["total_results"], 8823)
        self.assertEqual(out["count"], 3)
        self.assertEqual(len(out["programmes"]), 3)

    def test_compact_programme_fields(self):
        p = dom.compact_programme(_result("search-tagesschau.json")["results"][0])
        self.assertEqual(p["channel"], "tagesschau24")
        self.assertEqual(p["topic"], "tagesschau in 100 Sekunden")
        self.assertEqual(p["title"], "tagesschau in 100 Sekunden")
        self.assertEqual(p["duration_seconds"], 170)
        self.assertEqual(p["duration"], "2:50")
        self.assertTrue(p["broadcast"].startswith("2026-11-09T"))
        self.assertTrue(p["video_url"].endswith(".mp4"))
        self.assertTrue(p["video_url_hd"].endswith(".mp4"))
        self.assertTrue(p["website_url"].startswith("https://www.ardmediathek.de/"))
        self.assertEqual(p["size_bytes"], 40894464)

    def test_topic_fixture_duration(self):
        p = dom.compact_programme(_result("by-topic-heute-journal.json")["results"][0])
        self.assertEqual(p["channel"], "ZDF")
        self.assertEqual(p["topic"], "heute journal")
        self.assertEqual(p["duration_seconds"], 1786)
        self.assertEqual(p["duration"], "29:46")

    def test_channel_fixture_all_zdf(self):
        out = dom.compact_results(_result("by-channel-zdf.json"))
        self.assertTrue(all(p["channel"] == "ZDF" for p in out["programmes"]))
        self.assertEqual(out["total_results"], 10000)

    def test_latest_fixture(self):
        out = dom.compact_results(_result("latest.json"))
        self.assertEqual(out["count"], 2)
        self.assertTrue(all(p["broadcast"] for p in out["programmes"]))


class TestHelpers(unittest.TestCase):
    def test_duration_hms(self):
        self.assertEqual(dom._duration_hms(170), "2:50")
        self.assertEqual(dom._duration_hms(3661), "1:01:01")
        self.assertEqual(dom._duration_hms(45), "0:45")
        self.assertIsNone(dom._duration_hms(None))

    def test_validate_limit(self):
        self.assertEqual(dom.validate_limit(10), 10)
        with self.assertRaises(ValueError):
            dom.validate_limit(0)
        with self.assertRaises(ValueError):
            dom.validate_limit(51)

    def test_normalise_channel(self):
        self.assertEqual(dom.normalise_channel("zdf"), "ZDF")
        self.assertEqual(dom.normalise_channel(" ARTE.de "), "ARTE.DE")
        self.assertEqual(dom.normalise_channel("phoenix"), "PHOENIX")
        # Unknown names pass through unchanged.
        self.assertEqual(dom.normalise_channel("SomeChannel"), "SomeChannel")
        with self.assertRaises(ValueError):
            dom.normalise_channel("  ")

    def test_find_exact_title(self):
        results = _result("by-topic-heute-journal.json")["results"]
        title = "heute journal vom 8. November 2026 (S2026/E333)"
        found = dom.find_exact_title(results, title, None)
        self.assertIsNotNone(found)
        self.assertEqual(found["channel"], "ZDF")
        # Case-insensitive match.
        self.assertIsNotNone(dom.find_exact_title(results, title.upper(), None))
        # Channel restriction.
        self.assertIsNotNone(dom.find_exact_title(results, title, "zdf"))
        self.assertIsNone(dom.find_exact_title(results, title, "ARD"))
        # No match.
        self.assertIsNone(dom.find_exact_title(results, "does not exist", None))


class TestServerToolsOffline(unittest.TestCase):
    """Server tools with the HTTP layer mocked to return fixture data."""

    def test_search_programmes(self):
        with mock.patch(
            "mediathek_mcp.http.search",
            return_value=_result("search-tagesschau.json"),
        ):
            out = json.loads(srv.mediathek_search_programmes("Tagesschau"))
        self.assertNotIn("error", out)
        self.assertEqual(out["query"], "Tagesschau")
        self.assertEqual(out["count"], 3)
        self.assertEqual(out["programmes"][0]["channel"], "tagesschau24")

    def test_search_programmes_empty_query(self):
        out = json.loads(srv.mediathek_search_programmes("  "))
        self.assertIn("error", out)

    def test_search_programmes_bad_limit(self):
        out = json.loads(srv.mediathek_search_programmes("Tagesschau", limit=99))
        self.assertIn("error", out)

    def test_search_programmes_with_channel_filters(self):
        # Fixture has 3 tagesschau24 results; filtering to ZDF yields none.
        with mock.patch(
            "mediathek_mcp.http.search",
            return_value=_result("search-tagesschau.json"),
        ):
            out = json.loads(
                srv.mediathek_search_programmes("Tagesschau", channel="ZDF")
            )
        self.assertNotIn("error", out)
        self.assertEqual(out["channel"], "ZDF")
        self.assertEqual(out["count"], 0)
        self.assertEqual(out["total_results"], 0)

    def test_latest_broadcasts(self):
        with mock.patch(
            "mediathek_mcp.http.search",
            return_value=_result("latest.json"),
        ):
            out = json.loads(srv.mediathek_latest_broadcasts(limit=2))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 2)

    def test_by_channel(self):
        with mock.patch(
            "mediathek_mcp.http.search",
            return_value=_result("by-channel-zdf.json"),
        ) as m:
            out = json.loads(srv.mediathek_by_channel("zdf", limit=2))
        self.assertNotIn("error", out)
        self.assertEqual(out["channel"], "ZDF")
        # Normalised channel is what reaches the API.
        self.assertEqual(m.call_args.args[1], "ZDF")

    def test_by_topic(self):
        with mock.patch(
            "mediathek_mcp.http.search",
            return_value=_result("by-topic-heute-journal.json"),
        ):
            out = json.loads(srv.mediathek_by_topic("heute journal"))
        self.assertNotIn("error", out)
        self.assertEqual(out["topic"], "heute journal")
        self.assertEqual(out["count"], 2)

    def test_programme_detail_found(self):
        with mock.patch(
            "mediathek_mcp.http.search",
            return_value=_result("by-topic-heute-journal.json"),
        ):
            out = json.loads(
                srv.mediathek_programme_detail(
                    "heute journal vom 8. November 2026 (S2026/E333)"
                )
            )
        self.assertNotIn("error", out)
        self.assertEqual(out["channel"], "ZDF")
        self.assertTrue(out["video_url"].endswith(".mp4"))

    def test_programme_detail_missing(self):
        with mock.patch(
            "mediathek_mcp.http.search",
            return_value=_result("by-topic-heute-journal.json"),
        ):
            out = json.loads(
                srv.mediathek_programme_detail("no such programme title")
            )
        self.assertIn("error", out)
        self.assertIn("hint", out)

    def test_list_channels(self):
        out = json.loads(srv.mediathek_list_channels())
        self.assertGreaterEqual(out["count"], 10)
        channels = [c["channel"] for c in out["channels"]]
        for want in ("ARD", "ZDF", "3sat", "ARTE.DE", "PHOENIX", "tagesschau24"):
            self.assertIn(want, channels)


if __name__ == "__main__":
    unittest.main()
