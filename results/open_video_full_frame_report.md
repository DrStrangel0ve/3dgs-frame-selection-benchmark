# Open Video Full-Frame NCC Report

This run uses open-license source videos and removes the earlier temporal sampling step:

- `FPS=0`: extract every decoded frame.
- `MAX_FRAMES=0`: no max-frame cap.
- `WIDTH=640`: spatial resize only, used to keep COLMAP and Splatfacto tractable on the 8 GB GPU.
- Splatfacto iterations: 150 per trained variant.

## Sources

| Scene | Video | License | Frames |
| --- | --- | --- | ---: |
| `open_close_scanparayzo` | `videos/open_close_scanparayzo.webm` | CC0 1.0 | 976 |
| `open_mid_baios_statue` | `videos/open_mid_baios_statue.webm` | CC0 1.0 | 242 |
| `open_wide_gimbal_fence` | `videos/wide_path_gimbal_fence.webm` | Public domain, U.S. Bureau of Land Management | 832 |

## Metrics

Blank metric cells mean the variant trained or was skipped, but `ns-eval` could not produce PSNR/SSIM/LPIPS because COLMAP/Nerfstudio did not leave a usable eval split.

| Scene | Variant | Kept frames | Kept fraction | Processed frames | Status | PSNR | SSIM | LPIPS |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `open_close_scanparayzo` | `keep_all` | 976 | 1.0000 |  | mapper timeout |  |  |  |
| `open_close_scanparayzo` | `ncc_0_99` | 170 | 0.1742 | 2 | eval failed |  |  |  |
| `open_close_scanparayzo` | `ncc_0_95` | 67 | 0.0686 | 2 | eval failed |  |  |  |
| `open_close_scanparayzo` | `ncc_0_90` | 31 | 0.0318 | 30 | ok | 18.3222 | 0.900717 | 0.205718 |
| `open_close_scanparayzo` | `ncc_0_75` | 3 | 0.0031 |  | skipped |  |  |  |
| `open_mid_baios_statue` | `keep_all` | 242 | 1.0000 | 5 | eval failed |  |  |  |
| `open_mid_baios_statue` | `ncc_0_99` | 173 | 0.7149 | 4 | eval failed |  |  |  |
| `open_mid_baios_statue` | `ncc_0_95` | 135 | 0.5579 | 134 | ok | 20.7819 | 0.622283 | 0.704930 |
| `open_mid_baios_statue` | `ncc_0_90` | 97 | 0.4008 | 93 | ok | 20.6879 | 0.596844 | 0.710817 |
| `open_mid_baios_statue` | `ncc_0_75` | 47 | 0.1942 | 2 | eval failed |  |  |  |
| `open_wide_gimbal_fence` | `keep_all` | 832 | 1.0000 |  | not run |  |  |  |
| `open_wide_gimbal_fence` | `ncc_0_99` | 562 | 0.6755 | 5 | eval failed |  |  |  |
| `open_wide_gimbal_fence` | `ncc_0_95` | 248 | 0.2981 | 2 | eval failed |  |  |  |
| `open_wide_gimbal_fence` | `ncc_0_90` | 135 | 0.1623 | 4 | eval failed |  |  |  |
| `open_wide_gimbal_fence` | `ncc_0_75` | 33 | 0.0397 | 3 | eval failed |  |  |  |

## Exported Splats

Exported Gaussian splat `.ply` files are under `exports/`. Some failed-metric variants still have a `.ply` export because training completed, but COLMAP/Nerfstudio did not provide an eval split.

| Model | Size |
| --- | ---: |
| `exports/open_close_scanparayzo_ncc_0_90/open_close_scanparayzo_ncc_0_90.ply` | 13.5 KB |
| `exports/open_close_scanparayzo_ncc_0_95/open_close_scanparayzo_ncc_0_95.ply` | 14.7 KB |
| `exports/open_close_scanparayzo_ncc_0_99/open_close_scanparayzo_ncc_0_99.ply` | 8.9 KB |
| `exports/open_mid_baios_statue_keep_all/open_mid_baios_statue_keep_all.ply` | 12.4 KB |
| `exports/open_mid_baios_statue_ncc_0_75/open_mid_baios_statue_ncc_0_75.ply` | 8.2 KB |
| `exports/open_mid_baios_statue_ncc_0_90/open_mid_baios_statue_ncc_0_90.ply` | 747.0 KB |
| `exports/open_mid_baios_statue_ncc_0_95/open_mid_baios_statue_ncc_0_95.ply` | 911.7 KB |
| `exports/open_mid_baios_statue_ncc_0_99/open_mid_baios_statue_ncc_0_99.ply` | 58.5 KB |
| `exports/open_wide_gimbal_fence_ncc_0_75/open_wide_gimbal_fence_ncc_0_75.ply` | 54.4 KB |
| `exports/open_wide_gimbal_fence_ncc_0_90/open_wide_gimbal_fence_ncc_0_90.ply` | 147.3 KB |
| `exports/open_wide_gimbal_fence_ncc_0_95/open_wide_gimbal_fence_ncc_0_95.ply` | 78.2 KB |
| `exports/open_wide_gimbal_fence_ncc_0_99/open_wide_gimbal_fence_ncc_0_99.ply` | 165.6 KB |

## Notes

The full-frame `Scanparayzo/keep_all` COLMAP mapper ran for about four hours on 976 frames and was stopped. The wide `keep_all` variant was not run after that because the filtered wide variants already showed that COLMAP recovered only a few usable poses from this handheld path.

