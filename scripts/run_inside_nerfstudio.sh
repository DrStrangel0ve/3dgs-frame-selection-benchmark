#!/usr/bin/env bash
set -u

MAX_ITERS="${MAX_ITERS:-500}"
FPS="${FPS:-0}"
MAX_FRAMES="${MAX_FRAMES:-0}"
WIDTH="${WIDTH:-960}"
TRAIN_TIMEOUT_MIN="${TRAIN_TIMEOUT_MIN:-60}"
MIN_IMAGES="${MIN_IMAGES:-12}"
SCENES="${SCENES:-}"
VARIANTS="${VARIANTS:-keep_all ncc_0_99 ncc_0_95 ncc_0_90 ncc_0_75}"
SCENES_CSV="${SCENES_CSV:-}"
VARIANTS_CSV="${VARIANTS_CSV:-}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%d_%H%M%S)}"
MATCHING_METHOD="${MATCHING_METHOD:-sequential}"
SFM_TOOL="${SFM_TOOL:-colmap}"
CAMERA_TYPE="${CAMERA_TYPE:-perspective}"
NS_PROCESS_EXTRA_ARGS="${NS_PROCESS_EXTRA_ARGS:---matching-method $MATCHING_METHOD --sfm-tool $SFM_TOOL --camera-type $CAMERA_TYPE}"
NS_TRAIN_EXTRA_ARGS="${NS_TRAIN_EXTRA_ARGS:-}"
MANIFEST="${MANIFEST:-configs/videos.json}"
EXPORT_MODELS="${EXPORT_MODELS:-1}"
EXPORT_COLOR_MODE="${EXPORT_COLOR_MODE:-rgb}"
PYTHON="${PYTHON:-python3}"

if [[ -n "$SCENES_CSV" ]]; then
  SCENES="${SCENES_CSV//,/ }"
fi

if [[ -n "$VARIANTS_CSV" ]]; then
  VARIANTS="${VARIANTS_CSV//,/ }"
fi

if [[ -z "$SCENES" ]]; then
  SCENES="$("$PYTHON" - "$MANIFEST" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(" ".join(item["scene_id"] for item in data["videos"]))
PY
)"
fi

mkdir -p exports results/logs results/metrics results/status outputs processed

"$PYTHON" - <<PY
import json
from pathlib import Path

payload = {
    "run_id": "$RUN_ID",
    "max_iters": int("$MAX_ITERS"),
    "fps": float("$FPS"),
    "max_frames": int("$MAX_FRAMES"),
    "width": int("$WIDTH"),
    "scenes": "$SCENES".split(),
    "variants": "$VARIANTS".split(),
    "manifest": "$MANIFEST",
    "ns_process_extra_args": "$NS_PROCESS_EXTRA_ARGS",
    "ns_train_extra_args": "$NS_TRAIN_EXTRA_ARGS",
    "export_models": "$EXPORT_MODELS",
}
Path("results/run_config.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

echo "run_id=${RUN_ID}"
nvidia-smi || true
command -v ns-train
command -v ns-process-data
command -v ns-eval
command -v ffmpeg
command -v colmap
command -v "$PYTHON"

"$PYTHON" scripts/prepare_ncc_variants.py \
  --manifest "$MANIFEST" \
  --fps "$FPS" \
  --max-frames "$MAX_FRAMES" \
  --width "$WIDTH"

write_status() {
  local scene="$1"
  local variant="$2"
  local stage="$3"
  local status="$4"
  local message="$5"
  local path="results/status/${scene}_${variant}.json"
  "$PYTHON" - "$path" "$scene" "$variant" "$stage" "$status" "$message" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = {
    "scene": sys.argv[2],
    "variant": sys.argv[3],
    "stage": sys.argv[4],
    "status": sys.argv[5],
    "message": sys.argv[6],
}
path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY
}

find_config() {
  local experiment="$1"
  find "outputs/${experiment}" -path "*/${RUN_ID}/config.yml" -print 2>/dev/null | sort | tail -n 1
}

for scene in $SCENES; do
  for variant in $VARIANTS; do
    experiment="${scene}_${variant}"
    images_dir="frames/${scene}/${variant}/images"
    processed_dir="processed/${scene}/${variant}"
    process_log="results/logs/${experiment}_process.log"
    train_log="results/logs/${experiment}_train.log"
    eval_log="results/logs/${experiment}_eval.log"
    metrics_path="results/metrics/${experiment}.json"
    export_dir="exports/${experiment}"
    status_path="results/status/${experiment}.json"

    rm -f -- "$metrics_path" "$status_path"

    count="$(find "$images_dir" -maxdepth 1 -type f -name '*.jpg' 2>/dev/null | wc -l | tr -d ' ')"
    if [[ "$count" -lt "$MIN_IMAGES" ]]; then
      echo "skip ${experiment}: only ${count} images"
      write_status "$scene" "$variant" "prepare" "skipped" "only ${count} images"
      continue
    fi

    echo "process ${experiment} (${count} images)"
    case "$processed_dir" in
      processed/*/*) rm -rf -- "$processed_dir" ;;
      *) echo "refusing to clean unexpected path: $processed_dir"; continue ;;
    esac
    if ! ns-process-data images \
      --data "$images_dir" \
      --output-dir "$processed_dir" \
      $NS_PROCESS_EXTRA_ARGS \
      >"$process_log" 2>&1; then
      echo "failed process ${experiment}; see ${process_log}"
      write_status "$scene" "$variant" "process" "failed" "$process_log"
      continue
    fi

    echo "train ${experiment}"
    if ! timeout "${TRAIN_TIMEOUT_MIN}m" ns-train splatfacto \
      --data "$processed_dir" \
      --output-dir outputs \
      --experiment-name "$experiment" \
      --timestamp "$RUN_ID" \
      --max-num-iterations "$MAX_ITERS" \
      --steps-per-save "$MAX_ITERS" \
      --steps-per-eval-all-images "$MAX_ITERS" \
      --vis tensorboard \
      $NS_TRAIN_EXTRA_ARGS \
      >"$train_log" 2>&1; then
      echo "failed train ${experiment}; see ${train_log}"
      write_status "$scene" "$variant" "train" "failed" "$train_log"
      continue
    fi

    config_path="$(find_config "$experiment")"
    if [[ -z "$config_path" ]]; then
      echo "failed config lookup ${experiment}"
      write_status "$scene" "$variant" "train" "failed" "missing config.yml"
      continue
    fi

    echo "eval ${experiment}"
    if ! ns-eval \
      --load-config "$config_path" \
      --output-path "$metrics_path" \
      >"$eval_log" 2>&1; then
      echo "failed eval ${experiment}; see ${eval_log}"
      write_status "$scene" "$variant" "eval" "failed" "$eval_log"
      continue
    fi

    if [[ "$EXPORT_MODELS" == "1" ]]; then
      echo "export ${experiment}"
      mkdir -p "$export_dir"
      if ! ns-export gaussian-splat \
        --load-config "$config_path" \
        --output-dir "$export_dir" \
        --output-filename "${experiment}.ply" \
        --ply-color-mode "$EXPORT_COLOR_MODE" \
        >>"$eval_log" 2>&1; then
        echo "failed export ${experiment}; see ${eval_log}"
        write_status "$scene" "$variant" "export" "failed" "$eval_log"
        continue
      fi
    fi

    write_status "$scene" "$variant" "done" "ok" "$metrics_path"
  done
done

"$PYTHON" scripts/summarize_results.py --manifest "$MANIFEST"
