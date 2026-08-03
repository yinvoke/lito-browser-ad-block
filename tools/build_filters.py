#!/usr/bin/env python3
"""把上游规则编译成 Lito 运行期使用的六个紧凑文件。"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re

from source_catalog import default_catalog, load_catalog, metadata_dates
from validate_snapshot import write_manifest


PROC = (
    ":has(", ":has-text(", ":contains(", ":matches-css", ":xpath(", ":upward(",
    ":nth-ancestor(", ":remove(", ":style(", ":min-text-length", ":watch-attr",
    ":matches-attr", ":matches-path", ":matches-property", ":-abp-",
)
DOMAIN_RE = re.compile(r"^\|\|([a-z0-9._\-]+)\^$")
EXCEPTION_RE = re.compile(r"^@@\|\|([a-z0-9._\-]+)(/[^\s$*^|#]+)$", re.I)
HOSTS_RE = re.compile(r"^(?:0\.0\.0\.0|127\.0\.0\.1)\s+([a-z0-9._\-]+)$")
BARE_RE = re.compile(r"^([a-z0-9][a-z0-9.\-]+\.[a-z]{2,})$")


def is_proc(selector: str) -> bool:
    return any(marker in selector for marker in PROC)


def add_specific(specific: dict[str, set[str]], domains: str, selector: str) -> None:
    for domain in domains.split(","):
        domain = domain.strip().lower()
        if not domain or domain.startswith("~"):
            return
        specific.setdefault(domain, set()).add(selector)


def write_text(path: pathlib.Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--catalog", type=pathlib.Path, default=default_catalog())
    parser.add_argument("--report", type=pathlib.Path)
    args = parser.parse_args()

    raw_dir = args.raw.resolve()
    output = args.output.resolve()
    sources = load_catalog(args.catalog)
    missing = [source.file for source in sources if not (raw_dir / source.file).is_file()]
    if missing:
        raise SystemExit(f"missing source files: {', '.join(missing)}")

    domains: set[str] = set()
    network_exceptions: set[str] = set()
    generic: set[str] = set()
    specific: dict[str, set[str]] = {}

    for source in sources:
        path = raw_dir / source.file
        with path.open(encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                if line[0] in "!#[" and not line.startswith("##"):
                    continue
                if line.startswith("@@"):
                    match = EXCEPTION_RE.match(line)
                    if match:
                        network_exceptions.add((match.group(1) + match.group(2)).lower())
                    continue
                if any(marker in line for marker in ("##", "#@#", "#?#", "#$#", "#%#")):
                    if any(marker in line for marker in ("#@#", "#?#", "#$#", "#%#")):
                        continue
                    left, _, selector = line.partition("##")
                    selector = selector.strip()
                    if not selector or is_proc(selector) or "+js" in selector or selector.startswith("^"):
                        continue
                    if left == "":
                        generic.add(selector)
                    else:
                        add_specific(specific, left, selector)
                    continue
                if not source.network:
                    continue
                match = DOMAIN_RE.match(line)
                if match:
                    domain = match.group(1).lower().strip(".")
                    if "*" not in domain and "." in domain:
                        domains.add(domain)
                    continue
                match = HOSTS_RE.match(line)
                if match:
                    domain = match.group(1).lower().strip(".")
                    if domain != "localhost" and "." in domain:
                        domains.add(domain)
                    continue
                match = BARE_RE.match(line)
                if match:
                    domains.add(match.group(1).lower().strip("."))

    before_prune = len(domains)
    domains = {
        domain for domain in domains
        if not any(
            ".".join(domain.split(".")[index:]) in domains
            for index in range(1, domain.count(".") + 1)
        )
    }
    output.mkdir(parents=True, exist_ok=True)
    write_text(output / "adblock_domains.txt", "\n".join(sorted(domains)))
    write_text(output / "network_exceptions.txt", "\n".join(sorted(network_exceptions)))
    write_text(output / "cosmetic_generic.txt", "\n".join(sorted(generic)))
    normalized_specific = {host: sorted(selectors) for host, selectors in specific.items()}
    write_text(
        output / "cosmetic_specific.json",
        json.dumps(normalized_specific, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
    )
    source_dates = metadata_dates(raw_dir, sources)
    write_text(
        output / "sources.json",
        json.dumps(source_dates, separators=(",", ":"), sort_keys=True),
    )
    version = os.environ.get("LITO_FILTER_VERSION")
    if version is None:
        version = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M")
    if not re.fullmatch(r"\d{12}", version):
        raise SystemExit("LITO_FILTER_VERSION must be YYYYMMDDHHmm")
    write_text(output / "version.txt", version + "\n")
    write_manifest(output, version)

    specific_rules = sum(len(selectors) for selectors in normalized_specific.values())
    report = {
        "schema": 1,
        "version": version,
        "sources": source_dates,
        "counts": {
            "domains_before_parent_prune": before_prune,
            "domains": len(domains),
            "network_exceptions": len(network_exceptions),
            "cosmetic_generic": len(generic),
            "cosmetic_specific_hosts": len(normalized_specific),
            "cosmetic_specific_rules": specific_rules,
        },
        "source_sha256": {
            source.id: hashlib.sha256((raw_dir / source.file).read_bytes()).hexdigest()
            for source in sources
        },
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"parent-pruned    : {before_prune:>7} -> {len(domains)}")
    print(f"sources          : {source_dates}")
    print(f"version          : {version}")
    print(f"domains          : {len(domains):>7}")
    print(f"network except   : {len(network_exceptions):>7}  path prefixes")
    print(f"cosmetic generic : {len(generic):>7}  selectors")
    print(f"cosmetic specific: {len(normalized_specific):>7}  hosts / {specific_rules} rules")


if __name__ == "__main__":
    main()
