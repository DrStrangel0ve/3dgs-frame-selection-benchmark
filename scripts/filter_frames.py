#!/usr/bin/env python3
"""Filter video frames by similarity to the previous kept frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input video path.")
    parser.add_argument("--output", required=True, help="Directory for kept JPEG frames and selection.json.")
    parser.add_argument(
        "--metric",
        choices=["keep_all", "ncc", "mse", "ssim"],
        default="keep_all",
        help="Similarity metric used to decide whether to drop a candidate frame.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="NCC/SSIM drop when score >= threshold. MSE drops when score <= threshold.",
    )
    parser.add_argument("--fps", type=float, default=0.0, help="0 keeps every decoded frame; positive values sample by time.")
    parser.add_argument("--resize-width", type=int, default=640, help="Resize width used for metric computation and output.")
    parser.add_argument("--quality", type=int, default=95, help="JPEG quality for kept frames.")
    return parser.parse_args()


def normalize_frame(frame: np.ndarray, resize_width: int) -> np.ndarray:
    if resize_width > 0 and frame.shape[1] != resize_width:
        scale = resize_width / frame.shape[1]
        frame = cv2.resize(frame, (resize_width, max(1, round(frame.shape[0] * scale))), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return gray.astype(np.float32) / 255.0


def resized_color(frame: np.ndarray, resize_width: int) -> np.ndarray:
    if resize_width <= 0 or frame.shape[1] == resize_width:
        return frame
    scale = resize_width / frame.shape[1]
    return cv2.resize(frame, (resize_width, max(1, round(frame.shape[0] * scale))), interpolation=cv2.INTER_AREA)


def ncc_score(a: np.ndarray, b: np.ndarray) -> float:
    a0 = a - float(a.mean())
    b0 = b - float(b.mean())
    denom = np.sqrt(float(np.sum(a0 * a0)) * float(np.sum(b0 * b0)))
    if denom == 0:
        return 1.0 if np.allclose(a, b) else 0.0
    return float(np.sum(a0 * b0) / denom)


def mse_score(a: np.ndarray, b: np.ndarray) -> float:
    diff = a - b
    return float(np.mean(diff * diff))


def ssim_score(a: np.ndarray, b: np.ndarray) -> float:
    try:
        from skimage.metrics import structural_similarity
    except ImportError as exc:
        raise RuntimeError("SSIM requires scikit-image: pip install scikit-image") from exc
    return float(structural_similarity(a, b, data_range=1.0))


def similarity(metric: str, previous: np.ndarray, current: np.ndarray) -> float:
    if metric == "ncc":
        return ncc_score(previous, current)
    if metric == "mse":
        return mse_score(previous, current)
    if metric == "ssim":
        return ssim_score(previous, current)
    raise ValueError(f"Unsupported metric for similarity: {metric}")


def should_drop(metric: str, score: float, threshold: float) -> bool:
    if metric == "mse":
        return score <= threshold
    return score >= threshold


def should_consider(timestamp_ms: float, fps: float, next_timestamp_ms: float) -> tuple[bool, float]:
    if fps <= 0:
        return True, next_timestamp_ms
    if timestamp_ms + 1e-6 < next_timestamp_ms:
        return False, next_timestamp_ms
    step = 1000.0 / fps
    while next_timestamp_ms <= timestamp_ms + 1e-6:
        next_timestamp_ms += step
    return True, next_timestamp_ms


def main() -> None:
    args = parse_args()
    if args.metric != "keep_all" and args.threshold is None:
        raise SystemExit("--threshold is required for ncc, mse, and ssim")

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise SystemExit(f"Could not open video: {input_path}")

    previous_kept: np.ndarray | None = None
    raw_frames = 0
    considered = 0
    kept = 0
    dropped = 0
    records: list[dict[str, Any]] = []
    next_timestamp_ms = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        timestamp_ms = float(cap.get(cv2.CAP_PROP_POS_MSEC))
        raw_frames += 1

        include, next_timestamp_ms = should_consider(timestamp_ms, args.fps, next_timestamp_ms)
        if not include:
            continue
        considered += 1

        metric_frame = normalize_frame(frame, args.resize_width)
        score: float | None = None
        decision = "keep"
        if args.metric != "keep_all" and previous_kept is not None:
            score = similarity(args.metric, previous_kept, metric_frame)
            if should_drop(args.metric, score, float(args.threshold)):
                dropped += 1
                decision = "drop"
                records.append(
                    {
                        "source_index": raw_frames - 1,
                        "timestamp_ms": timestamp_ms,
                        "decision": decision,
                        "score": score,
                    }
                )
                continue

        kept += 1
        previous_kept = metric_frame
        frame_name = f"frame_{kept:06d}.jpg"
        cv2.imwrite(str(output_dir / frame_name), resized_color(frame, args.resize_width), [cv2.IMWRITE_JPEG_QUALITY, args.quality])
        records.append(
            {
                "source_index": raw_frames - 1,
                "kept_index": kept,
                "timestamp_ms": timestamp_ms,
                "decision": decision,
                "score": score,
                "file": frame_name,
            }
        )

    cap.release()
    manifest = {
        "input": str(input_path),
        "metric": args.metric,
        "threshold": args.threshold,
        "fps": args.fps,
        "resize_width": args.resize_width,
        "raw_frames_read": raw_frames,
        "frames_considered": considered,
        "kept_count": kept,
        "dropped_count": dropped,
        "drop_rate": (dropped / considered) if considered else 0.0,
        "records": records,
    }
    (output_dir / "selection.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in manifest if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
