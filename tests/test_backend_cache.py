import json
import os
import tempfile
import unittest
from unittest.mock import patch

import backend


class RefreshCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_file = os.path.join(self.temp_dir.name, "heatmap_data.json")
        self.cache_dir = self.temp_dir.name
        self.config_dir = os.path.join(self.temp_dir.name, "config")
        self.paths = patch.multiple(
            backend,
            CACHE_DIR=self.cache_dir,
            CACHE_FILE=self.cache_file,
            CONFIG_DIR=self.config_dir,
            CONFIG_FILE=os.path.join(self.config_dir, "config.json"),
        )
        self.paths.start()
        self.addCleanup(self.paths.stop)
        self.addCleanup(self.temp_dir.cleanup)

    def write_cache(self, username):
        with open(self.cache_file, "w", encoding="utf-8") as cache:
            json.dump({
                "username": username,
                "displayName": username.title(),
                "totalContributions": 123,
                "todayCount": 4,
                "weeks": [],
            }, cache)

    def fail_both_fetches(self):
        first = patch.object(backend, "fetch_via_gh", return_value=None)
        second = patch.object(backend, "fetch_via_public_api", return_value=None)
        first.start()
        second.start()
        self.addCleanup(first.stop)
        self.addCleanup(second.stop)

    def test_offline_refresh_never_returns_another_users_cache(self):
        self.write_cache("alice")
        self.fail_both_fetches()

        result = backend.refresh_data("bob")

        self.assertEqual(result["username"], "bob")
        self.assertEqual(result["totalContributions"], 0)
        self.assertFalse(result["stale"])
        self.assertIn("error", result)

    def test_offline_refresh_returns_same_users_cache_with_stale_status(self):
        self.write_cache("Alice")
        self.fail_both_fetches()

        result = backend.refresh_data("alice")

        self.assertEqual(result["username"], "Alice")
        self.assertEqual(result["totalContributions"], 123)
        self.assertTrue(result["stale"])
        self.assertIn("error", result)

    def test_successful_refresh_returns_fresh_data_without_stale_status(self):
        fresh = {
            "username": "bob",
            "displayName": "Bob",
            "totalContributions": 42,
            "todayCount": 2,
            "weeks": [],
        }
        with patch.object(backend, "fetch_via_gh", return_value=None), patch.object(
            backend, "fetch_via_public_api", return_value={"total": {}, "contributions": []}
        ), patch.object(backend, "parse_public_data", return_value=fresh):
            result = backend.refresh_data("bob")

        self.assertEqual(result, fresh)
        self.assertNotIn("stale", result)
        with open(self.cache_file, "r", encoding="utf-8") as cache:
            self.assertEqual(json.load(cache), fresh)


if __name__ == "__main__":
    unittest.main()
