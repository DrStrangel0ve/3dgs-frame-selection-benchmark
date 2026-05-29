# 3DGS Frame Selection Benchmark

Benchmark how frame-to-frame similarity filtering changes Gaussian splatting reconstructions. The first target is Nerfstudio Splatfacto on open-license videos, comparing raw all-frame input against NCC, MSE, and SSIM frame rejection.

This repo is the broader home for the frame-selection workload. The first NCC-only run lives in [DrStrangel0ve/3d-gaussian-splatting-ncc](https://github.com/DrStrangel0ve/3d-gaussian-splatting-ncc).

## Workload

- Extract every decoded video frame by default.
- Compare each candidate frame with the previous kept frame.
- Drop the candidate when the selected metric says the frames are too similar.
- Run `ns-process-data` and `ns-train splatfacto` for each threshold.
- Track PSNR, SSIM, LPIPS, registered COLMAP images, kept-frame count, train time, and exported `.ply` size.

## Starting Matrix

| Variant | Metric | Threshold meaning |
| --- | --- | --- |
| `keep_all` | none | keep every decoded frame |
| `ncc_0_99` | NCC | drop when NCC >= 0.99 |
| `ncc_0_95` | NCC | drop when NCC >= 0.95 |
| `ncc_0_90` | NCC | drop when NCC >= 0.90 |
| `ncc_0_75` | NCC | drop when NCC >= 0.75 |
| `ssim_*` | SSIM | drop when SSIM >= threshold |
| `mse_*` | MSE | drop when MSE <= threshold |

## Quick Start

```bash
python scripts/filter_frames.py --input data/videos/example.mp4 --output frames/example/keep_all --metric keep_all
python scripts/filter_frames.py --input data/videos/example.mp4 --output frames/example/ncc_0_95 --metric ncc --threshold 0.95
```

Then process and train with Nerfstudio, ideally from WSL or a CUDA-ready Linux environment:

```bash
ns-process-data images --data frames/example/ncc_0_95 --output-dir processed/example/ncc_0_95
ns-train splatfacto --data processed/example/ncc_0_95
```

## Repository Shape

- `configs/workload_matrix.json` defines the intended threshold sweep.
- `scripts/filter_frames.py` is a metric-based frame keeper for full-frame video inputs.
- `results/` is reserved for summary tables and metric JSON files.

## License

MIT for code and project scaffolding. Dataset and video licenses should be tracked per source.
