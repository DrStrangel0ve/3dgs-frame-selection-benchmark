#!/usr/bin/env bash
set -euo pipefail

pattern="${1:-outputs/*/*/*/config.yml}"

for config in $pattern; do
  experiment="$(echo "$config" | cut -d/ -f2)"
  output_dir="exports/${experiment}"
  output_file="${output_dir}/${experiment}.ply"

  mkdir -p "$output_dir"
  if [[ -s "$output_file" ]]; then
    echo "exists: $output_file"
    continue
  fi

  echo "export: $experiment"
  ns-export gaussian-splat \
    --load-config "$config" \
    --output-dir "$output_dir" \
    --output-filename "${experiment}.ply" \
    --ply-color-mode rgb
done

