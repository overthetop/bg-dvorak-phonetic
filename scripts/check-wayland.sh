#!/bin/bash
set -euo pipefail

output=${1:?pass an output keymap path}
repo=$(cd "$(dirname "$0")/.." && pwd)
runtime=$(mktemp -d)
chmod 700 "$runtime"
trap 'rm -rf "$runtime"' EXIT
export XDG_RUNTIME_DIR="$runtime"
export MUTTER_DEBUG_DUMMY_MODE_SPECS=1024x768
cc -o "$runtime/dump-wayland-keymap" "$repo/scripts/dump-wayland-keymap.c" \
  $(pkg-config --cflags --libs wayland-client)

dbus-run-session -- bash -euo pipefail -c '
  gsettings set org.gnome.desktop.input-sources sources "[(\"xkb\", \"bgdv\")]"
  timeout 40s mutter --wayland --no-x11 --sm-disable --headless -- "$2" "$1"
' bash "$output" "$runtime/dump-wayland-keymap"
grep -Fq 'Cyrillic_a' "$output"
printf 'Headless GNOME Wayland advertised the installed layout.\n'
