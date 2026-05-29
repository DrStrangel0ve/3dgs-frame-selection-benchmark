# Project Plan

## Milestone 1: Full-frame filtering baseline

- Keep raw all-frame extractions as the control.
- Sweep NCC thresholds `0.99`, `0.95`, `0.90`, and `0.75`.
- Add MSE and SSIM sweeps with comparable frame-retention reporting.
- Record frame counts before COLMAP so redundancy is visible before training.

## Milestone 2: Nerfstudio integration

- Add a WSL/Docker runner for `ns-process-data images`.
- Train `splatfacto` with a fixed iteration budget per variant.
- Export Gaussian `.ply` assets for every trained variant.
- Aggregate `ns-eval` PSNR, SSIM, and LPIPS into one summary table.

## Milestone 3: Selection analysis

- Plot retained-frame count against quality metrics.
- Compare previous-raw-frame and previous-kept-frame filtering.
- Add per-scene notes for COLMAP failures, sparse tracks, and bad eval splits.
- Publish a small report for each source video.
