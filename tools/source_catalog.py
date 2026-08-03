#!/usr/bin/env python3
"""共享的上游目录解析与头部更新时间识别。"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import pathlib
import re
from typing import Iterable


@dataclasses.dataclass(frozen=True)
class Source:
    id: str
    name: str
    file: str
    layer: str
    url: str
    homepage: str
    license: str
    license_url: str
    min_bytes: int
    max_bytes: int
    max_age_hours: int

    @property
    def network(self) -> bool:
        return self.layer == "network"


def default_catalog() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent / "sources.json"


def load_catalog(path: pathlib.Path | None = None) -> list[Source]:
    catalog_path = (path or default_catalog()).resolve()
    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    if raw.get("schema") != 1 or not isinstance(raw.get("sources"), list):
        raise ValueError("sources.json schema must be 1")
    sources = [Source(**item) for item in raw["sources"]]
    if not sources:
        raise ValueError("source catalog is empty")
    if len({s.id for s in sources}) != len(sources):
        raise ValueError("source ids must be unique")
    if len({s.file for s in sources}) != len(sources):
        raise ValueError("source filenames must be unique")
    for source in sources:
        if not re.fullmatch(r"[a-z0-9_]+", source.id):
            raise ValueError(f"unsafe source id: {source.id}")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*\.txt", source.file):
            raise ValueError(f"unsafe source filename: {source.file}")
        if source.layer not in {"network", "cosmetic"}:
            raise ValueError(f"bad source layer: {source.id}")
        if not source.url.startswith("https://"):
            raise ValueError(f"source URL must use HTTPS: {source.id}")
        if source.min_bytes < 1 or source.max_bytes < source.min_bytes:
            raise ValueError(f"bad source size limits: {source.id}")
        if source.max_age_hours < 1:
            raise ValueError(f"bad source freshness limit: {source.id}")
    return sources


MONTHS = {name: index for index, name in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"),
    start=1,
)}


def parse_source_updated(path: pathlib.Path) -> dt.datetime | None:
    """从常见过滤规则头部读取 UTC 更新时间。"""
    text = path.read_bytes()[:131072].decode("utf-8", errors="replace")
    for line in text.splitlines()[:80]:
        iso = re.search(
            r"(?:Last modified|TimeUpdated)\s*[:=]\s*"
            r"(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)",
            line,
            re.I,
        )
        if iso:
            value = iso.group(1).replace("Z", "+00:00")
            parsed = dt.datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)

        english = re.search(
            r"Last modified\s*[:=]\s*(\d{1,2})\s+([A-Za-z]{3})\s+(20\d{2})"
            r"(?:\s+(\d{1,2}):(\d{2}))?",
            line,
            re.I,
        )
        if english and english.group(2).lower() in MONTHS:
            return dt.datetime(
                int(english.group(3)), MONTHS[english.group(2).lower()], int(english.group(1)),
                int(english.group(4) or 0), int(english.group(5) or 0), tzinfo=dt.timezone.utc,
            )

        compact = re.search(r"^[#!]\s*(?:VER|Version)\s*[:=]\s*(20\d{12})", line, re.I)
        if compact:
            return dt.datetime.strptime(compact.group(1), "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
    return None


def metadata_dates(raw_dir: pathlib.Path, sources: Iterable[Source]) -> dict[str, str]:
    result: dict[str, str] = {}
    for source in sources:
        updated = parse_source_updated(raw_dir / source.file)
        if updated is not None:
            result[source.id] = updated.strftime("%Y-%m-%d")
    return result
