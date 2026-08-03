#!/usr/bin/env python3
"""从严格构建报告生成可审计的每日发布状态。"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fetch_report", type=pathlib.Path)
    parser.add_argument("build_report", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    fetch = json.loads(args.fetch_report.read_text(encoding="utf-8"))
    build = json.loads(args.build_report.read_text(encoding="utf-8"))
    repository = os.environ.get("GITHUB_REPOSITORY", "local")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    status = {
        "schema": 1,
        "version": build["version"],
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "repository": repository,
        "commit": os.environ.get("GITHUB_SHA", "local"),
        "workflow_run": f"https://github.com/{repository}/actions/runs/{run_id}" if run_id else None,
        "counts": build["counts"],
        "sources": {
            source_id: {
                "updated_at": item["updated_at"],
                "bytes": item["bytes"],
                "sha256": item["sha256"],
            }
            for source_id, item in sorted(fetch["sources"].items())
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
