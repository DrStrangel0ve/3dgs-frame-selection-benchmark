# NCC Threshold Summary

| scene | variant | kept_frames | kept_fraction | ncc_mean | processed_frames | status | psnr | ssim | lpips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| close_object | keep_all | 40 | 1 | 0.880314 | 39 | ok | 22.437 | 0.817038 | 0.366185 |
| close_object | ncc_0_99 | 40 | 1 | 0.880314 | 40 | ok | 21.5326 | 0.815977 | 0.364732 |
| close_object | ncc_0_95 | 39 | 0.975 | 0.880314 | 39 | ok | 22.5049 | 0.825857 | 0.348862 |
| close_object | ncc_0_90 | 31 | 0.775 | 0.870134 | 31 | ok | 21.8894 | 0.816847 | 0.380831 |
| close_object | ncc_0_75 | 13 | 0.325 | 0.792955 | 13 | ok | 17.3541 | 0.761069 | 0.563388 |
| mid_scene | keep_all | 80 | 1 | 0.60361 | 80 | ok | 15.3233 | 0.453026 | 0.799887 |
| mid_scene | ncc_0_99 | 80 | 1 | 0.60361 | 79 | ok | 15.4227 | 0.461894 | 0.799049 |
| mid_scene | ncc_0_95 | 80 | 1 | 0.60361 | 80 | ok | 15.527 | 0.456805 | 0.793742 |
| mid_scene | ncc_0_90 | 78 | 0.975 | 0.602696 | 71 | ok | 15.5272 | 0.488426 | 0.765093 |
| mid_scene | ncc_0_75 | 66 | 0.825 | 0.592992 | 66 | ok | 15.1902 | 0.450555 | 0.825265 |
| wide_path | keep_all | 80 | 1 | 0.605075 | 77 | ok | 16.1142 | 0.440517 | 0.823413 |
| wide_path | ncc_0_99 | 80 | 1 | 0.605075 | 78 | ok | 16.7063 | 0.455752 | 0.80501 |
| wide_path | ncc_0_95 | 80 | 1 | 0.605075 | 77 | ok | 17.5002 | 0.445072 | 0.799778 |
| wide_path | ncc_0_90 | 80 | 1 | 0.605075 | 79 | ok | 17.3056 | 0.460005 | 0.788702 |
| wide_path | ncc_0_75 | 61 | 0.7625 | 0.586412 | 27 | ok | 18.45 | 0.430012 | 0.800662 |

NCC rule: compare each candidate to the previous kept frame, then drop the candidate when NCC is greater than or equal to the threshold.