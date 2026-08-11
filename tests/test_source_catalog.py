from __future__ import annotations

import datetime as dt
import pathlib
import tempfile
import unittest

from tools.source_catalog import load_catalog, parse_source_updated


class SourceCatalogTest(unittest.TestCase):
    def parse(self, header: str, offset_minutes: int = 0) -> dt.datetime | None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "filter.txt"
            path.write_text(header, encoding="utf-8")
            return parse_source_updated(path, offset_minutes)

    def test_antiad_compact_timestamp_uses_declared_utc_plus_8(self) -> None:
        self.assertEqual(
            dt.datetime(2026, 8, 4, 20, 6, 36, tzinfo=dt.timezone.utc),
            self.parse("#VER=20260805040636\n", 480),
        )

    def test_explicit_iso_timezone_ignores_source_default(self) -> None:
        self.assertEqual(
            dt.datetime(2026, 8, 5, 4, 6, 36, tzinfo=dt.timezone.utc),
            self.parse("! TimeUpdated: 2026-08-05T04:06:36Z\n", 480),
        )

    def test_explicit_english_utc_ignores_source_default(self) -> None:
        self.assertEqual(
            dt.datetime(2026, 8, 10, 7, 40, tzinfo=dt.timezone.utc),
            self.parse("! Last modified: 10 Aug 2026 07:40 UTC\n", 480),
        )

    def test_catalog_uses_hagezi_mirror_and_antiad_timezone(self) -> None:
        sources = {source.id: source for source in load_catalog()}
        self.assertTrue(sources["hagezi_pro"].url.startswith("https://gitlab.com/hagezi/mirror/"))
        self.assertTrue(sources["hagezi_tif"].url.startswith("https://gitlab.com/hagezi/mirror/"))
        self.assertEqual(480, sources["antiad"].timestamp_utc_offset_minutes)


if __name__ == "__main__":
    unittest.main()
