#!/usr/bin/env python3
"""严格抓取全部上游；任一失败时不污染上一份完整输入。"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile

from source_catalog import default_catalog, load_catalog, parse_source_updated


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--catalog", type=pathlib.Path, default=default_catalog())
    parser.add_argument("--report", type=pathlib.Path)
    args = parser.parse_args()

    if shutil.which("curl") is None:
        fail("curl is required")
    sources = load_catalog(args.catalog)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    report: dict[str, object] = {
        "schema": 1,
        "fetched_at": now.isoformat().replace("+00:00", "Z"),
        "sources": {},
    }

    with tempfile.TemporaryDirectory(prefix="lito-filter-fetch-", dir=output.parent) as temp_name:
        stage = pathlib.Path(temp_name)
        for source in sources:
            destination = stage / source.file
            print(f"fetch {source.id}: {source.url}")
            subprocess.run(
                [
                    "curl", "--fail", "--silent", "--show-error", "--location",
                    "--retry", "3", "--retry-all-errors", "--connect-timeout", "20",
                    "--max-time", "180", "--output", str(destination), source.url,
                ],
                check=True,
            )
            size = destination.stat().st_size
            if not source.min_bytes <= size <= source.max_bytes:
                fail(
                    f"{source.id} outside size gate: {size} bytes "
                    f"(expected {source.min_bytes}..{source.max_bytes})"
                )
            prefix = destination.read_bytes()[:512].lstrip().lower()
            if prefix.startswith((b"<!doctype html", b"<html")):
                fail(f"{source.id} returned HTML instead of a filter list")
            updated = parse_source_updated(destination)
            if updated is None:
                fail(f"{source.id} has no recognized upstream timestamp")
            age_hours = (now - updated).total_seconds() / 3600
            if age_hours < -6:
                fail(f"{source.id} timestamp is unexpectedly in the future: {updated.isoformat()}")
            if age_hours > source.max_age_hours:
                fail(
                    f"{source.id} is stale: {age_hours:.1f}h old "
                    f"(limit {source.max_age_hours}h)"
                )
            report["sources"][source.id] = {
                "url": source.url,
                "file": source.file,
                "bytes": size,
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "updated_at": updated.isoformat().replace("+00:00", "Z"),
                "age_hours": round(max(age_hours, 0), 2),
            }

        output.mkdir(parents=True, exist_ok=True)
        for source in sources:
            os.replace(stage / source.file, output / source.file)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"fetched {len(sources)} sources into {output}")


if __name__ == "__main__":
    main()
