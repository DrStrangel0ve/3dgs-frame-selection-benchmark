#!/usr/bin/env bash
set -euo pipefail

mkdir -p videos source_captures/colmap_zips source_captures/colmap

download() {
  local url="$1"
  local output="$2"

  if [[ -s "$output" ]]; then
    echo "exists: $output"
    return
  fi

  echo "download: $output"
  curl -fL --retry 3 --retry-delay 2 -o "$output" "$url"
}

extract_zip() {
  local zip_path="$1"
  local marker_dir="$2"
  local output_dir="$3"

  if [[ -d "$marker_dir" ]]; then
    echo "exists: $marker_dir"
    return
  fi

  echo "extract: $zip_path"
  python3 -m zipfile -e "$zip_path" "$output_dir"
}

download "https://storage.googleapis.com/objectron/videos/camera/batch-7/24/video.MOV" \
  "videos/close_object_objectron_camera.MOV"

download "https://commons.wikimedia.org/wiki/Special:Redirect/file/Scanparayzo.webm" \
  "videos/open_close_scanparayzo.webm"

download "https://commons.wikimedia.org/wiki/Special:Redirect/file/Baios_statue_-_Ninfeo_punta_Epitaffio.webm" \
  "videos/open_mid_baios_statue.webm"

download "https://commons.wikimedia.org/wiki/Special:Redirect/file/Gimbal_shot_walking_along_fence_line_(49716812698).webm" \
  "videos/wide_path_gimbal_fence.webm"

download "https://github.com/colmap/colmap/releases/download/3.11.1/gerrard-hall.zip" \
  "source_captures/colmap_zips/gerrard-hall.zip"

download "https://github.com/colmap/colmap/releases/download/3.11.1/south-building.zip" \
  "source_captures/colmap_zips/south-building.zip"

extract_zip "source_captures/colmap_zips/gerrard-hall.zip" \
  "source_captures/colmap/gerrard-hall/images" \
  "source_captures/colmap"

extract_zip "source_captures/colmap_zips/south-building.zip" \
  "source_captures/colmap/south-building/images" \
  "source_captures/colmap"

find videos source_captures/colmap -maxdepth 3 -type d -o -type f | head -80
