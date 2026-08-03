#!/usr/bin/env python3
"""校验 Lito 编译快照的格式、排序和最低安全规模。"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

from source_catalog import default_catalog, load_catalog


FILES = (
    "adblock_domains.txt",
    "network_exceptions.txt",
    "cosmetic_generic.txt",
    "cosmetic_specific.json",
    "sources.json",
    "version.txt",
)
MANIFEST = "manifest.txt"
MANIFEST_HEADER = "LITO-FILTER-MANIFEST-2"
MANIFEST_LIMIT = 64 << 10
FILE_LIMITS = {
    "adblock_domains.txt": 16 << 20,
    "network_exceptions.txt": 2 << 20,
    "cosmetic_generic.txt": 8 << 20,
    "cosmetic_specific.json": 16 << 20,
    "sources.json": 64 << 10,
    "version.txt": 64,
}
DOMAIN_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?\.[a-z0-9-]+$")


def fail(message: str) -> None:
    raise ValueError(message)


def canonical_manifest(root: pathlib.Path, version: str) -> bytes:
    lines = [MANIFEST_HEADER, f"version={version}"]
    for name in FILES:
        path = root / name
        lines.append(
            f"file\t{name}\t{path.stat().st_size}\t{hashlib.sha256(path.read_bytes()).hexdigest()}"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_manifest(root: pathlib.Path, version: str) -> None:
    (root / MANIFEST).write_bytes(canonical_manifest(root, version))


def sorted_unique_lines(path: pathlib.Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or any(not line for line in lines):
        fail(f"{path.name} must contain non-empty lines")
    if lines != sorted(set(lines)):
        fail(f"{path.name} must be sorted and unique")
    return lines


def validate(root: pathlib.Path, catalog: pathlib.Path | None = None) -> dict[str, int | str]:
    root = root.resolve()
    if not root.is_dir():
        fail(f"snapshot directory missing: {root}")
    for name in FILES:
        path = root / name
        if not path.is_file():
            fail(f"missing snapshot file: {name}")
        size = path.stat().st_size
        if not 1 <= size <= FILE_LIMITS[name]:
            fail(f"snapshot file outside size limit: {name} ({size} bytes)")

    version = (root / "version.txt").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d{12}", version):
        fail("version.txt must contain YYYYMMDDHHmm")
    manifest = root / MANIFEST
    if not manifest.is_file() or not 1 <= manifest.stat().st_size <= MANIFEST_LIMIT:
        fail("manifest.txt is missing or outside size limit")
    if manifest.read_bytes() != canonical_manifest(root, version):
        fail("manifest.txt does not exactly describe the snapshot")

    domains = sorted_unique_lines(root / "adblock_domains.txt")
    if any(not DOMAIN_RE.fullmatch(domain) for domain in domains):
        fail("adblock_domains.txt contains an invalid domain")
    exceptions = sorted_unique_lines(root / "network_exceptions.txt")
    generic = sorted_unique_lines(root / "cosmetic_generic.txt")

    specific = json.loads((root / "cosmetic_specific.json").read_text(encoding="utf-8"))
    if not isinstance(specific, dict) or list(specific) != sorted(specific):
        fail("cosmetic_specific.json must be an object with sorted host keys")
    specific_rules = 0
    for host, selectors in specific.items():
        if not isinstance(host, str) or not host or not isinstance(selectors, list) or not selectors:
            fail("cosmetic_specific.json contains an invalid host entry")
        if selectors != sorted(set(selectors)) or any(not isinstance(item, str) or not item for item in selectors):
            fail(f"cosmetic selectors must be sorted and unique: {host}")
        specific_rules += len(selectors)

    source_meta = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    expected_source_ids = {source.id for source in load_catalog(catalog)}
    if not isinstance(source_meta, dict) or set(source_meta) != expected_source_ids:
        fail(
            "sources.json key mismatch: "
            f"expected {sorted(expected_source_ids)}, got {sorted(source_meta) if isinstance(source_meta, dict) else '?'}"
        )
    if any(not isinstance(value, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", value)
           for value in source_meta.values()):
        fail("sources.json contains an invalid date")

    counts: dict[str, int | str] = {
        "version": version,
        "domains": len(domains),
        "network_exceptions": len(exceptions),
        "cosmetic_generic": len(generic),
        "cosmetic_specific_hosts": len(specific),
        "cosmetic_specific_rules": specific_rules,
    }
    floors = {
        "domains": 200_000,
        "network_exceptions": 50,
        "cosmetic_generic": 500,
        "cosmetic_specific_hosts": 500,
        "cosmetic_specific_rules": 1_000,
    }
    for key, minimum in floors.items():
        if int(counts[key]) < minimum:
            fail(f"snapshot below safety floor: {key}={counts[key]}, minimum={minimum}")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=pathlib.Path)
    parser.add_argument("--catalog", type=pathlib.Path, default=default_catalog())
    args = parser.parse_args()
    try:
        counts = validate(args.snapshot, args.catalog)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(counts, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
