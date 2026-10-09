#!/usr/bin/env bash
# Генерация launcher-иконок Android из векторной отрисовки ImageMagick.
# Знак: янтарная лупа с голубым стеклом — «нуар-детектив».
# Запуск из корня репозитория: bash tools/make_icons.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RES="$ROOT/android/app/src/main/res"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

BG="#0a0f1c"
AMBER="#ffd23a"
CYAN="#59d8ff"

# --- знак на прозрачном фоне 1024x1024 ---
convert -size 1024x1024 xc:none \
  -fill "$AMBER" -stroke none -draw "circle 470,420 470,150" \
  -fill "$BG" -draw "circle 470,420 470,215" \
  -fill "$CYAN" -draw "circle 470,420 470,320" \
  -fill "$AMBER" -stroke "$AMBER" -strokewidth 84 \
  -draw "stroke-linecap round line 610,560 840,790" \
  "$WORK/mark.png"

# --- задник: тёмный скруглённый квадрат ---
convert -size 1024x1024 xc:none \
  -fill "$BG" -stroke none -draw "roundrectangle 0,0 1023,1023 220,220" \
  "$WORK/bg.png"

square() { # size out mark_pct
  local s="$1" out="$2" pct="$3"
  convert "$WORK/mark.png" -resize "${pct}%" "$WORK/m.png"
  convert "$WORK/bg.png" "$WORK/m.png" -gravity center -composite \
    -resize "${s}x${s}!" "$out"
}

round() { # size out mark_pct
  local s="$1" out="$2" pct="$3"
  convert "$WORK/mark.png" -resize "${pct}%" "$WORK/m.png"
  convert "$WORK/bg.png" "$WORK/m.png" -gravity center -composite \
    -resize "${s}x${s}!" "$WORK/r.png"
  convert "$WORK/r.png" \
    \( +clone -alpha extract -fill black -colorize 100 \
       -fill white -draw "circle $((s/2)),$((s/2)) $((s/2)),0" \) \
    -alpha off -compose CopyOpacity -composite "$out"
}

foreground() { # size out
  local s="$1" out="$2"
  convert "$WORK/mark.png" -resize "61%" "$WORK/f.png"
  convert -size "${s}x${s}" xc:none "$WORK/f.png" -gravity center -composite "$out"
}

declare -A D=( [mdpi]=48 [hdpi]=72 [xhdpi]=96 [xxhdpi]=144 [xxxhdpi]=192 )
declare -A F=( [mdpi]=108 [hdpi]=162 [xhdpi]=216 [xxhdpi]=324 [xxxhdpi]=432 )

for d in "${!D[@]}"; do
  dir="$RES/mipmap-$d"
  mkdir -p "$dir"
  square   "${D[$d]}" "$dir/ic_launcher.png" 78
  round    "${D[$d]}" "$dir/ic_launcher_round.png" 78
  foreground "${F[$d]}" "$dir/ic_launcher_foreground.png"
done

# обновляем цвет адаптивного задника
cat > "$RES/values/ic_launcher_background.xml" <<XML
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">$BG</color>
</resources>
XML

echo "[OK] иконки Android обновлены в $RES"
