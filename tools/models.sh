#!/usr/bin/env bash
# Пересборка всех моделей из tools/make_*.py через Blender.
#
# usage: tools/models.sh [--out public/models] [--only make_env,make_vehicles]
#
# Blender ищется в $BLENDER, затем ../tmp/blender-*/blender,
# /opt/tools/blender/blender, затем в PATH. Остальные аргументы уходят
# генераторам как есть (их разбирает noirlib.parse_args).
set -euo pipefail
cd "$(dirname "$0")/.."

find_blender() {
  if [ -n "${BLENDER:-}" ]; then
    printf '%s\n' "$BLENDER"
    return 0
  fi
  local c
  for c in ../tmp/blender-*/blender /opt/tools/blender/blender; do
    if [ -x "$c" ]; then
      printf '%s\n' "$c"
      return 0
    fi
  done
  command -v blender 2>/dev/null || true
}

BL="$(find_blender)"
if [ -z "$BL" ]; then
  echo "blender не найден. Задай BLENDER=/путь/к/blender" >&2
  exit 1
fi

OUT="public/models"
PASSTHROUGH=()
while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    *) PASSTHROUGH+=("$1"); shift ;;
  esac
done

echo "· blender: $BL ($("$BL" --version | head -1))"
echo "· out: $OUT"
mkdir -p "$OUT"

fail=0
for f in tools/make_*.py; do
  echo "=== $f"
  if ! "$BL" -b -P "$f" -- --out "$OUT" ${PASSTHROUGH[@]+"${PASSTHROUGH[@]}"}; then
    echo "FAIL: $f" >&2
    fail=1
  fi
done

echo "=== готово, моделей в $OUT:"
ls -l "$OUT"/*.glb 2>/dev/null || true
exit "$fail"
