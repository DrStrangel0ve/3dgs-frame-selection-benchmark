#!/usr/bin/env python3
"""Download videos listed in a manifest that contains source_url/local_path fields."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("configs/open_videos_full.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    for video in manifest["videos"]:
        if video.get("source_type", "video") != "video":
            continue
        output = Path(video["local_path"])
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() and output.stat().st_size > 0:
            print(f"exists: {output}")
            continue
        print(f"download: {output}")
        subprocess.run(["curl", "-fL", "--retry", "3", "--retry-delay", "2", "-o", str(output), video["source_url"]], check=True)


if __name__ == "__main__":
    main()
