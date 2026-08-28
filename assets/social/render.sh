#!/usr/bin/env bash
# Regenerate the two social cards from their HTML sources.
#
#   bash assets/social/render.sh
#
# linkedin-card.png  1200x627 (1.91:1)  -> Open Graph / LinkedIn / Twitter.
#                                          Copied into public/assets/img/social-card.png,
#                                          which is the file the live pages reference.
# github-card.png    1280x640 (2:1)     -> repo Settings > Social preview (manual upload;
#                                          GitHub has no API for it).
set -euo pipefail
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$CHROME" ] || { echo "Chrome not found at $CHROME" >&2; exit 1; }

shot () {  # shot <html> <out> <w> <h>
  "$CHROME" --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --screenshot="$PWD/$2" --window-size="$3,$4" "file://$PWD/$1" >/dev/null 2>&1
  echo "  $2  ${3}x${4}"
}
shot card-linkedin.html linkedin-card.png 1200 627
shot card-github.html   github-card.png   1280 640

cp linkedin-card.png ../../public/assets/img/social-card.png
echo "  copied linkedin-card.png -> public/assets/img/social-card.png"
