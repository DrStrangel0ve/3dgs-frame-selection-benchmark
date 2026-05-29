#!/usr/bin/env python3
"""Aggregate NCC frame-selection stats and Nerfstudio eval metrics."""

from __future__ import annotations

import csv
import json
import argparse
from pathlib import Path
from typing import Any


VARIANTS = ("keep_all", "ncc_0_99", "ncc_0_95", "ncc_0_90", "ncc_0_75")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="configs/videos.json")
    return parser.parse_args()


def scenes_from_manifest(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [item["scene_id"] for item in data["videos"]]


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def find_metric(payload: Any, names: tuple[str, ...]) -> float | None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = key.lower()
            if lowered in names and isinstance(value, (int, float)):
                return float(value)
            found = find_metric(value, names)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = find_metric(value, names)
            if found is not None:
                return found
    return None


def processed_frame_count(scene: str, variant: str) -> int | None:
    transforms = read_json(Path("processed") / scene / variant / "transforms.json")
    if not transforms:
        return None
    frames = transforms.get("frames")
    return len(frames) if isinstance(frames, list) else None


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def row_for(scene: str, variant: str) -> dict[str, Any]:
    selection = read_json(Path("frames") / scene / variant / "selection.json") or {}
    metrics = read_json(Path("results") / "metrics" / f"{scene}_{variant}.json")
    status = read_json(Path("results") / "status" / f"{scene}_{variant}.json") or {}

    row: dict[str, Any] = {
        "scene": scene,
        "variant": variant,
        "threshold": selection.get("threshold"),
        "raw_frames": selection.get("raw_frame_count"),
        "kept_frames": selection.get("kept_frame_count"),
        "dropped_frames": selection.get("dropped_frame_count"),
        "kept_fraction": selection.get("kept_fraction"),
        "ncc_mean": selection.get("ncc_mean"),
        "ncc_median": selection.get("ncc_median"),
        "ncc_p95": selection.get("ncc_p95"),
        "ncc_min": selection.get("ncc_min"),
        "ncc_max": selection.get("ncc_max"),
        "processed_frames": processed_frame_count(scene, variant),
        "status": status.get("status", "missing_metrics" if metrics is None else "ok"),
        "stage": status.get("stage", "eval" if metrics is not None else ""),
        "psnr": find_metric(metrics, ("psnr",)) if metrics else None,
        "ssim": find_metric(metrics, ("ssim",)) if metrics else None,
        "lpips": find_metric(metrics, ("lpips",)) if metrics else None,
        "metrics_path": f"results/metrics/{scene}_{variant}.json" if metrics else "",
    }
    return row


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "scene",
        "variant",
        "threshold",
        "raw_frames",
        "kept_frames",
        "dropped_frames",
        "kept_fraction",
        "ncc_mean",
        "ncc_median",
        "ncc_p95",
        "ncc_min",
        "ncc_max",
        "processed_frames",
        "status",
        "stage",
        "psnr",
        "ssim",
        "lpips",
        "metrics_path",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: fmt(row.get(key)) for key in fieldnames})


def write_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    columns = [
        "scene",
        "variant",
        "kept_frames",
        "kept_fraction",
        "ncc_mean",
        "processed_frames",
        "status",
        "psnr",
        "ssim",
        "lpips",
    ]
    lines = [
        "# NCC Threshold Summary",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    lines.append("")
    lines.append("NCC rule: compare each candidate to the previous kept frame, then drop the candidate when NCC is greater than or equal to the threshold.")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = [row_for(scene, variant) for scene in scenes_from_manifest(Path(args.manifest)) for variant in VARIANTS]
    write_csv(rows, Path("results/summary.csv"))
    write_markdown(rows, Path("results/summary.md"))
    print("wrote results/summary.csv and results/summary.md")


if __name__ == "__main__":
    main()
