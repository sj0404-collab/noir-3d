#!/usr/bin/env bash
# Рендер сцены в PNG через headless chromium (SwiftShader).
# usage: tools/shot.sh <url> <out.png> [width] [height] [waitMs]
URL="$1"; OUT="$2"; W="${3:-1280}"; H="${4:-720}"; WAIT="${5:-12000}"
CHROME="${CHROME:-chromium}"
mkdir -p "$(dirname "$OUT")"
LOG="$(dirname "$OUT")/chrome.log"

timeout 240 "$CHROME" \
  --headless \
  --no-sandbox \
  --disable-gpu-sandbox \
  --use-gl=angle --use-angle=swiftshader \
  --enable-unsafe-swiftshader \
  --disable-dev-shm-usage \
  --hide-scrollbars \
  --force-device-scale-factor=1 \
  --window-size="$W,$H" \
  --virtual-time-budget="$WAIT" \
  --screenshot="$OUT" \
  "$URL" > "$LOG" 2>&1

if [ -s "$OUT" ]; then
  echo "OK: $OUT ($(stat -c%s "$OUT") bytes)"
else
  echo "FAIL: $OUT не создан; хвост лога:" >&2
  tail -20 "$LOG" >&2
  exit 1
fi
