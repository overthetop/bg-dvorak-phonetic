#!/bin/bash
set -euo pipefail

version=${1:-}
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { printf 'Usage: %s MAJOR.MINOR.PATCH\n' "$0" >&2; exit 2; }
command -v zip >/dev/null || { printf 'zip is required.\n' >&2; exit 1; }
repo=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$repo/dist"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

for platform in ubuntu macos; do
  package="bg-dvorak-phonetic-$version-$platform"
  directory="$work/$package"
  mkdir -p "$directory"
  if [[ "$platform" == ubuntu ]]; then
    cp "$repo/linux/bgdv" "$repo/linux/registry-layout.xml" "$repo/linux/manage.sh" "$repo/linux/install.sh" "$repo/linux/uninstall.sh" "$directory/"
    cp "$repo/docs/install-ubuntu.txt" "$directory/INSTALL.txt"
  else
    cp -R "$repo/mac-os/bg-dvorak-phonetic.bundle" "$directory/"
    cp "$repo/mac-os/install.command" "$repo/mac-os/uninstall.command" "$directory/"
    cp "$repo/docs/install-macos.txt" "$directory/INSTALL.txt"
  fi
  (cd "$work" && zip -qr "$work/$package.zip" "$package")
  mv -f "$work/$package.zip" "$repo/dist/$package.zip"
  printf '%s\n' "$repo/dist/$package.zip"
done
