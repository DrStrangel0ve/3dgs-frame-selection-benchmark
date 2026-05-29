#!/usr/bin/env python3
"""Extract video frames and build NCC-filtered image variants."""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image


THRESHOLDS: tuple[float | None, ...] = (None, 0.99, 0.95, 0.90, 0.75)


@dataclass(frozen=True)
class VideoSpec:
    scene_id: str
    source_type: str
    local_path: Path | None = None
    image_dir: Path | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="configs/videos.json")
    parser.add_argument("--output-root", default="frames")
    parser.add_argument(
        "--fps",
        type=float,
        default=0.0,
        help="Frames per second to extract. Use 0 to keep every decoded video frame.",
    )
    parser.add_argument("--max-frames", type=int, default=0, help="Use 0 for no frame cap.")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument(
        "--metric-size",
        default="160x90",
        help="Resize used only for NCC computation, WIDTHxHEIGHT.",
    )
    return parser.parse_args()


def load_manifest(path: Path) -> list[VideoSpec]:
    data = json.loads(path.read_text(encoding="utf-8"))
    specs: list[VideoSpec] = []
    for item in data["videos"]:
        source_type = item.get("source_type", "video")
        specs.append(
            VideoSpec(
                scene_id=item["scene_id"],
                source_type=source_type,
                local_path=Path(item["local_path"]) if item.get("local_path") else None,
                image_dir=Path(item["image_dir"]) if item.get("image_dir") else None,
            )
        )
    return specs


def run(cmd: list[str]) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def extract_raw_frames(video_path: Path, raw_dir: Path, fps: float, width: int) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(raw_dir.glob("frame_*.jpg"))
    if existing:
        return existing

    vf = f"scale={width}:-2" if fps <= 0 else f"fps={fps},scale={width}:-2"
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            vf,
            "-q:v",
            "2",
            str(raw_dir / "frame_%05d.jpg"),
        ]
    )
    return sorted(raw_dir.glob("frame_*.jpg"))


def list_source_images(image_dir: Path) -> list[Path]:
    extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    return sorted(path for path in image_dir.iterdir() if path.suffix.lower() in extensions)


def resize_to_width(image: Image.Image, width: int) -> Image.Image:
    if image.width == width:
        return image
    height = max(2, int(round(image.height * width / image.width)))
    if height % 2:
        height += 1
    return image.resize((width, height), Image.Resampling.LANCZOS)


def prepare_image_sequence(image_dir: Path, raw_dir: Path, max_frames: int, width: int) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    sources = select_evenly(list_source_images(image_dir), max_frames)
    existing = sorted(raw_dir.glob("frame_*.jpg"))
    if len(existing) == len(sources):
        return existing

    for old in existing:
        old.unlink()
    for idx, source in enumerate(sources):
        with Image.open(source) as image:
            image = resize_to_width(image.convert("RGB"), width)
            image.save(raw_dir / f"frame_{idx:05d}.jpg", quality=95)
    return sorted(raw_dir.glob("frame_*.jpg"))


def select_evenly(paths: list[Path], max_frames: int) -> list[Path]:
    if max_frames <= 0 or len(paths) <= max_frames:
        return paths
    indices = np.linspace(0, len(paths) - 1, max_frames)
    return [paths[int(round(idx))] for idx in indices]


def parse_metric_size(value: str) -> tuple[int, int]:
    width, height = value.lower().split("x", maxsplit=1)
    return int(width), int(height)


def gray_array(path: Path, size: tuple[int, int]) -> np.ndarray:
    with Image.open(path) as image:
        image = image.convert("L").resize(size, Image.Resampling.BILINEAR)
        return np.asarray(image, dtype=np.float32)


def ncc(a: np.ndarray, b: np.ndarray) -> float:
    a0 = a - float(a.mean())
    b0 = b - float(b.mean())
    denom = math.sqrt(float((a0 * a0).sum()) * float((b0 * b0).sum()))
    if denom < 1e-8:
        return 1.0 if float(np.abs(a - b).mean()) < 1e-6 else 0.0
    return float((a0 * b0).sum() / denom)


def variant_name(threshold: float | None) -> str:
    if threshold is None:
        return "keep_all"
    return f"ncc_{threshold:.2f}".replace(".", "_")


def copy_kept_images(kept: list[Path], image_dir: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(image_dir.glob("*.jpg"))
    for old in existing:
        old.unlink()
    for idx, source in enumerate(kept):
        shutil.copy2(source, image_dir / f"frame_{idx:05d}.jpg")


def percentile(values: Iterable[float], q: float) -> float | None:
    values = list(values)
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=np.float32), q))


def write_selection(
    scene_dir: Path,
    variant: str,
    threshold: float | None,
    source_frames: list[Path],
    kept_frames: list[Path],
    pair_rows: list[dict[str, object]],
) -> None:
    ncc_values = [float(row["ncc"]) for row in pair_rows]
    payload = {
        "variant": variant,
        "threshold": threshold,
        "raw_frame_count": len(source_frames),
        "kept_frame_count": len(kept_frames),
        "dropped_frame_count": len(source_frames) - len(kept_frames),
        "kept_fraction": len(kept_frames) / len(source_frames) if source_frames else 0.0,
        "comparison": "candidate frame against previous kept frame",
        "drop_rule": "drop candidate when NCC >= threshold",
        "ncc_min": min(ncc_values) if ncc_values else None,
        "ncc_mean": float(np.mean(ncc_values)) if ncc_values else None,
        "ncc_median": percentile(ncc_values, 50),
        "ncc_p95": percentile(ncc_values, 95),
        "ncc_max": max(ncc_values) if ncc_values else None,
        "kept_source_files": [path.name for path in kept_frames],
    }
    variant_dir = scene_dir / variant
    variant_dir.mkdir(parents=True, exist_ok=True)
    (variant_dir / "selection.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with (variant_dir / "selection_pairs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["index", "previous", "candidate", "ncc", "kept"])
        writer.writeheader()
        writer.writerows(pair_rows)


def build_variants(spec: VideoSpec, output_root: Path, args: argparse.Namespace) -> None:
    scene_id = spec.scene_id
    scene_dir = output_root / scene_id
    fps_tag = "full" if args.fps <= 0 else str(args.fps).replace(".", "_")
    if spec.source_type == "video":
        if spec.local_path is None or not spec.local_path.exists():
            raise FileNotFoundError(spec.local_path)
        raw_dir = scene_dir / f"_raw_{spec.local_path.stem}_fps{fps_tag}_w{args.width}"
        raw_frames = extract_raw_frames(spec.local_path, raw_dir, args.fps, args.width)
        source_frames = select_evenly(raw_frames, args.max_frames)
    elif spec.source_type == "images":
        if spec.image_dir is None or not spec.image_dir.exists():
            raise FileNotFoundError(spec.image_dir)
        raw_dir = scene_dir / f"_raw_{spec.image_dir.parent.name}_images_w{args.width}"
        source_frames = prepare_image_sequence(spec.image_dir, raw_dir, args.max_frames, args.width)
    else:
        raise ValueError(f"Unsupported source_type: {spec.source_type}")
    metric_size = parse_metric_size(args.metric_size)

    arrays = [gray_array(path, metric_size) for path in source_frames]
    for threshold in THRESHOLDS:
        variant = variant_name(threshold)
        kept = [source_frames[0]] if source_frames else []
        kept_arrays = [arrays[0]] if arrays else []
        pair_rows: list[dict[str, object]] = []
        for idx in range(1, len(arrays)):
            previous_name = kept[-1].name
            score = ncc(kept_arrays[-1], arrays[idx])
            keep = threshold is None or score < threshold
            if keep:
                kept.append(source_frames[idx])
                kept_arrays.append(arrays[idx])
            pair_rows.append(
                {
                    "index": idx,
                    "previous": previous_name,
                    "candidate": source_frames[idx].name,
                    "ncc": f"{score:.8f}",
                    "kept": int(keep),
                }
            )

        variant_dir = scene_dir / variant
        copy_kept_images(kept, variant_dir / "images")
        write_selection(scene_dir, variant, threshold, source_frames, kept, pair_rows)
        print(f"{scene_id}/{variant}: kept {len(kept)} of {len(source_frames)} frames")


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_root)
    for spec in load_manifest(Path(args.manifest)):
        build_variants(spec, output_root, args)


if __name__ == "__main__":
    main()
