# NCC Threshold Summary

| scene | variant | kept_frames | kept_fraction | ncc_mean | processed_frames | status | psnr | ssim | lpips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| open_close_scanparayzo | keep_all | 976 | 1 | 0.996379 |  | missing_metrics |  |  |  |
| open_close_scanparayzo | ncc_0_99 | 170 | 0.17418 | 0.993294 | 2 | failed |  |  |  |
| open_close_scanparayzo | ncc_0_95 | 67 | 0.0686475 | 0.972364 | 2 | failed |  |  |  |
| open_close_scanparayzo | ncc_0_90 | 31 | 0.0317623 | 0.948234 | 30 | ok | 18.3222 | 0.900717 | 0.205718 |
| open_close_scanparayzo | ncc_0_75 | 3 | 0.00307377 | 0.853899 |  | skipped |  |  |  |
| open_mid_baios_statue | keep_all | 242 | 1 | 0.940505 | 5 | failed |  |  |  |
| open_mid_baios_statue | ncc_0_99 | 173 | 0.714876 | 0.939691 | 4 | failed |  |  |  |
| open_mid_baios_statue | ncc_0_95 | 135 | 0.557851 | 0.931871 | 134 | ok | 20.7819 | 0.622283 | 0.70493 |
| open_mid_baios_statue | ncc_0_90 | 97 | 0.400826 | 0.910484 | 93 | ok | 20.6879 | 0.596844 | 0.710817 |
| open_mid_baios_statue | ncc_0_75 | 47 | 0.194215 | 0.825538 | 2 | failed |  |  |  |
| open_wide_gimbal_fence | keep_all | 832 | 1 | 0.986062 |  | missing_metrics |  |  |  |
| open_wide_gimbal_fence | ncc_0_99 | 562 | 0.675481 | 0.982631 | 5 | failed |  |  |  |
| open_wide_gimbal_fence | ncc_0_95 | 248 | 0.298077 | 0.961673 | 2 | failed |  |  |  |
| open_wide_gimbal_fence | ncc_0_90 | 135 | 0.16226 | 0.936726 | 4 | failed |  |  |  |
| open_wide_gimbal_fence | ncc_0_75 | 33 | 0.0396635 | 0.845066 | 3 | failed |  |  |  |

NCC rule: compare each candidate to the previous kept frame, then drop the candidate when NCC is greater than or equal to the threshold.