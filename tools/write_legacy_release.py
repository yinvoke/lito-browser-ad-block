#!/usr/bin/env python3
"""从 v2 快照派生 v1 兼容视图。

老 APK 的 FilterSnapshot 按旧六文件集做严格校验(manifest 文件集必须逐项相等),
v2 新增的 privacy_domains.txt 会让整包被拒收。这里把 v2 目录里的旧六文件原样复制,
再按旧文件集重写 manifest —— 除了少一个文件和 manifest 本身,字节与 v2 完全一致。
"""

from __future__ import annotations

import argparse
import pathlib
import shutil

from validate_snapshot import LEGACY_FILES, validate, write_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=pathlib.Path, help="v2 快照目录(含 privacy_domains.txt)")
    parser.add_argument("output", type=pathlib.Path, help="v1 兼容视图输出目录")
    args = parser.parse_args()
    release = args.release.resolve()
    output = args.output.resolve()
    if release == output:
        raise SystemExit("output must differ from release")
    # 先按 v2 全量校验,保证派生源本身是完好的
    validate(release)
    output.mkdir(parents=True, exist_ok=True)
    for name in LEGACY_FILES:
        shutil.copyfile(release / name, output / name)
    version = (release / "version.txt").read_text(encoding="utf-8").strip()
    write_manifest(output, version, LEGACY_FILES)
    counts = validate(output, legacy=True)
    print(f"legacy view written: {output} ({counts['version']})")


if __name__ == "__main__":
    main()
