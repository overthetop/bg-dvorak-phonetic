#!/bin/bash
set -euo pipefail

output=${1:?pass an output keymap path}
runtime=$(mktemp -d)
chmod 700 "$runtime"
trap 'rm -rf "$runtime"' EXIT
export XDG_RUNTIME_DIR="$runtime"
export MUTTER_DEBUG_DUMMY_MODE_SPECS=1024x768

dbus-run-session -- bash -euo pipefail -c '
  gsettings set org.gnome.desktop.input-sources sources "[(\"xkb\", \"bgdv\")]"
  timeout 40s mutter --wayland --no-x11 --sm-disable --headless -- \
    bash -c "xkbcli dump-keymap-wayland > \"\$1\"" bash "$1"
' bash "$output"
grep -Fq 'Cyrillic_a' "$output"
printf 'Headless GNOME Wayland advertised the installed layout.\n'
