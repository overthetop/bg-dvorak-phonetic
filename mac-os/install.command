#!/bin/bash
set -euo pipefail

fail() { printf 'Installation failed: %s\n' "$*" >&2; exit 1; }
[[ $(uname -s) == Darwin ]] || fail 'this installer requires macOS.'
command -v plutil >/dev/null || fail 'plutil is unavailable.'

source_dir=$(cd "$(dirname "$0")" && pwd)
bundle=bg-dvorak-phonetic.bundle
source_bundle="$source_dir/$bundle"
[[ -d "$source_bundle" ]] || fail "missing $source_bundle"
plutil -lint "$source_bundle/Contents/Info.plist" >/dev/null || fail 'invalid bundle Info.plist.'
keylayout="$source_bundle/Contents/Resources/bg-dvorak-phonetic.keylayout"
[[ -s "$keylayout" ]] || fail 'keylayout file is missing or empty.'
if ! grep -q '<keyboard ' "$keylayout" || ! grep -q '</keyboard>' "$keylayout"; then
  fail 'keylayout structure is missing.'
fi

destination_dir="$HOME/Library/Keyboard Layouts"
mkdir -p "$destination_dir" || fail "cannot create $destination_dir"
staging=$(mktemp -d "$destination_dir/.bg-dvorak-phonetic.XXXXXX") || fail 'cannot create staging directory.'
backup=
cleanup() {
  local status
  status=$1
  if (( status != 0 )) && [[ -n "$backup" && -d "$backup" ]]; then
    if ! mv "$backup" "$destination_dir/$bundle"; then
      printf 'Recovery needed: restore %s manually.\n' "$backup" >&2
      return
    fi
  fi
  rm -rf "$staging"
}
trap 'cleanup "$?"' EXIT
cp -R "$source_bundle" "$staging/$bundle" || fail 'cannot stage the bundle.'
if [[ -e "$destination_dir/$bundle" || -L "$destination_dir/$bundle" ]]; then
  [[ -d "$destination_dir/$bundle" && ! -L "$destination_dir/$bundle" ]] || fail 'destination is not an owned bundle directory.'
  plutil -lint "$destination_dir/$bundle/Contents/Info.plist" >/dev/null || fail 'existing bundle is not this layout.'
  existing_id=$(plutil -extract CFBundleIdentifier raw -o - "$destination_dir/$bundle/Contents/Info.plist") || fail 'cannot identify existing bundle.'
  [[ "$existing_id" == org.sil.ukelele.keyboardlayout.bg-dvorak-phonetic ]] || fail 'existing bundle has a different identifier.'
  backup="$staging/previous.bundle"
  mv "$destination_dir/$bundle" "$backup" || fail 'cannot back up existing bundle.'
fi
mv "$staging/$bundle" "$destination_dir/$bundle" || fail 'cannot install bundle.'
printf 'Installed %s\n' "$destination_dir/$bundle"
printf 'Open System Settings > Keyboard > Text Input > Edit > Add, then select Bulgarian (Dvorak phonetic). Sign out and back in if it is not listed.\n'
