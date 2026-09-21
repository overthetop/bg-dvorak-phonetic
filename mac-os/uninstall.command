#!/bin/bash
set -euo pipefail

fail() { printf 'Removal failed: %s\n' "$*" >&2; exit 1; }
[[ $(uname -s) == Darwin ]] || fail 'this uninstaller requires macOS.'
bundle="$HOME/Library/Keyboard Layouts/bg-dvorak-phonetic.bundle"
if [[ ! -e "$bundle" ]]; then
  printf 'Layout is already absent.\n'
  exit 0
fi
[[ -d "$bundle" && ! -L "$bundle" ]] || fail 'destination is not an owned bundle directory.'
identifier=$(plutil -extract CFBundleIdentifier raw -o - "$bundle/Contents/Info.plist") || fail 'cannot identify installed bundle.'
[[ "$identifier" == org.sil.ukelele.keyboardlayout.bg-dvorak-phonetic ]] || fail 'installed bundle has a different identifier.'
rm -rf "$bundle" || fail "cannot remove $bundle"
printf 'Removed %s. Remove the input source from System Settings if it is still listed.\n' "$bundle"
