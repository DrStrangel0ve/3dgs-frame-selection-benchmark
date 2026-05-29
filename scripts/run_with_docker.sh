#!/usr/bin/env bash
set -euo pipefail

IMAGE="${NERFSTUDIO_IMAGE:-ghcr.io/nerfstudio-project/nerfstudio:latest}"
WORKSPACE="$(pwd)"
CACHE_DIR="${HOME}/.cache"

mkdir -p "$CACHE_DIR" results/metrics results/status

docker run \
  --gpus all \
  --rm \
  -u "$(id -u)" \
  -e HOME=/home/user \
  -e USER=user \
  -e LOGNAME=user \
  -e XDG_CACHE_HOME=/home/user/.cache \
  -e MPLCONFIGDIR=/home/user/.cache/matplotlib \
  -e TORCHINDUCTOR_CACHE_DIR=/home/user/.cache/torchinductor \
  -e MAX_ITERS \
  -e FPS \
  -e MAX_FRAMES \
  -e WIDTH \
  -e TRAIN_TIMEOUT_MIN \
  -e MIN_IMAGES \
  -e SCENES \
  -e SCENES_CSV \
  -e VARIANTS \
  -e VARIANTS_CSV \
  -e RUN_ID \
  -e MANIFEST \
  -e MATCHING_METHOD \
  -e SFM_TOOL \
  -e CAMERA_TYPE \
  -e NS_PROCESS_EXTRA_ARGS \
  -e NS_TRAIN_EXTRA_ARGS \
  -e EXPORT_MODELS \
  -e EXPORT_COLOR_MODE \
  -v "${WORKSPACE}:/workspace" \
  -v "${CACHE_DIR}:/home/user/.cache" \
  -p 7007:7007 \
  --shm-size=12gb \
  -w /workspace \
  "$IMAGE" \
  bash scripts/run_inside_nerfstudio.sh
