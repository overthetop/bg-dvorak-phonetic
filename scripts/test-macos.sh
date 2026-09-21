#!/bin/bash
set -euo pipefail

archive=${1:?pass the macOS release ZIP}
[[ $(uname -s) == Darwin ]] || { printf 'macOS runner required.\n' >&2; exit 1; }
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
unzip -q "$archive" -d "$work"
package=$(find "$work" -mindepth 1 -maxdepth 1 -type d -name '*-macos' -print -quit)
[[ -n "$package" ]] || { printf 'macOS archive is empty.\n' >&2; exit 1; }
plutil -lint "$package/bg-dvorak-phonetic.bundle/Contents/Info.plist"
export HOME="$work/home"
mkdir -p "$HOME"
"$package/install.command"
"$package/install.command"
installed="$HOME/Library/Keyboard Layouts/bg-dvorak-phonetic.bundle"
[[ -f "$installed/Contents/Info.plist" ]]
"$package/uninstall.command"
[[ ! -e "$installed" ]]

mv "$package/bg-dvorak-phonetic.bundle" "$work/missing.bundle"
if "$package/install.command" >"$work/error.log" 2>&1; then exit 1; fi
grep -Fq 'missing' "$work/error.log"
mv "$work/missing.bundle" "$package/bg-dvorak-phonetic.bundle"
printf '<plist><dict>' > "$package/bg-dvorak-phonetic.bundle/Contents/Info.plist"
if "$package/install.command" >"$work/error.log" 2>&1; then
  printf 'Malformed bundle was accepted.\n' >&2
  exit 1
fi
if ! grep -Fq 'invalid bundle Info.plist' "$work/error.log"; then
  cat "$work/error.log" >&2
  exit 1
fi
printf 'macOS archive checks passed.\n'
