#!/bin/bash
# Record a gate check demo using asciinema.
# Output: visuals/gate_demo.cast
# Convert to GIF: agg visuals/gate_demo.cast visuals/gate_demo.gif

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if ! command -v asciinema >/dev/null 2>&1; then
    echo "asciinema not installed."
    echo "Install with: brew install asciinema"
    echo "Then re-run this script."
    exit 0
fi

mkdir -p "$PROJECT_DIR/visuals"

OUTPUT="$PROJECT_DIR/visuals/gate_demo.cast"
DEMO_DIR=$(mktemp -d /tmp/gate_demo_recording.XXXXXX)

echo "Recording gate check demo..."
echo "  Output: $OUTPUT"
echo "  Temp dir: $DEMO_DIR"

asciinema rec "$OUTPUT" \
  --title "External Gate — Cooperation Gate Check" \
  --command "python3 $SCRIPT_DIR/gate_mlx_model.py --port 8899 --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit --output-dir $DEMO_DIR"

echo ""
echo "Recording saved to $OUTPUT"
echo "Convert to GIF: agg $OUTPUT ${OUTPUT%.cast}.gif"

# Cleanup
rm -rf "$DEMO_DIR"
