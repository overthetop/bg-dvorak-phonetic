#!/bin/bash
set -euo pipefail

fail() { printf 'Layout %s failed: %s\n' "$action" "$*" >&2; exit 1; }
action=${1:-}
[[ "$action" == install || "$action" == uninstall ]] || { printf 'Usage: %s install|uninstall\n' "$0" >&2; exit 2; }
[[ $(uname -s) == Linux ]] || fail 'Ubuntu GNOME is required.'
os_release=${BGDV_TEST_OS_RELEASE:-/etc/os-release}
[[ -f "$os_release" ]] || fail "missing $os_release"
# shellcheck disable=SC1090
source "$os_release"
[[ ${ID:-} == ubuntu ]] || fail 'only Ubuntu GNOME is supported.'
command -v python3 >/dev/null || fail 'python3 is required for XML validation.'
command -v awk >/dev/null || fail 'awk is required.'

source_dir=$(cd "$(dirname "$0")" && pwd)
root=${BGDV_XKB_ROOT:-/usr/share/X11/xkb}
registry="$root/rules/evdev.xml"
symbols="$root/symbols/bgdv"
[[ -f "$registry" && -d "$root/symbols" ]] || fail "XKB root not found at $root"
if [[ ! -w "$registry" || ! -w "$root/symbols" ]]; then
  [[ ! ${BGDV_XKB_ROOT+x} && ! ${BGDV_TEST_OS_RELEASE+x} ]] || fail 'test XKB root is not writable.'
  command -v sudo >/dev/null || fail 'sudo is required for system XKB writes.'
  exec sudo "$0" "$action"
fi

validate_xml() { python3 -c 'import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1])' "$1"; }
validate_xml "$registry" || fail 'existing XKB registry XML is invalid.'
if [[ -e "$symbols" || -L "$symbols" ]]; then
  [[ -f "$symbols" && ! -L "$symbols" ]] || fail "$symbols is not a regular file."
  head -n 1 "$symbols" | grep -Fxq '// bgdv: managed by bg-dvorak-phonetic' || fail "$symbols is not owned by this project."
fi

begin='<!-- bgdv:begin -->'
end='<!-- bgdv:end -->'
begin_count=$(grep -Fc "$begin" "$registry" || true)
end_count=$(grep -Fc "$end" "$registry" || true)
[[ "$begin_count" -eq "$end_count" && "$begin_count" -le 1 ]] || fail 'inconsistent managed XML markers.'
if [[ "$begin_count" -eq 0 ]] && grep -Fq '<name>bgdv</name>' "$registry"; then
  fail 'an unmanaged bgdv registry entry already exists.'
fi

if [[ "$action" == install ]]; then
  [[ -f "$source_dir/bgdv" && -f "$source_dir/registry-layout.xml" ]] || fail 'layout assets are missing.'
  head -n 1 "$source_dir/bgdv" | grep -Fxq '// bgdv: managed by bg-dvorak-phonetic' || fail 'invalid layout asset.'
  validate_xml "$source_dir/registry-layout.xml" || fail 'invalid registry fragment.'
fi

work=$(mktemp -d "$root/rules/.bgdv.XXXXXX") || fail 'cannot stage changes.'
backup="$work/evdev.xml"
had_symbols=0
committed=0
cleanup() {
  local status recovery_failed
  status=$1
  recovery_failed=0
  if (( status != 0 && committed != 0 )); then
    cp -p "$backup" "$registry" || recovery_failed=1
    if (( had_symbols )); then
      cp -p "$work/bgdv" "$symbols" || recovery_failed=1
    else
      rm -f "$symbols" || recovery_failed=1
    fi
  fi
  if (( recovery_failed )); then
    printf 'Recovery failed; backups are preserved in %s.\n' "$work" >&2
    return
  fi
  rm -rf "$work"
}
trap 'cleanup "$?"' EXIT
cp -p "$registry" "$backup" || fail 'cannot back up XKB registry.'
if [[ -f "$symbols" ]]; then
  cp -p "$symbols" "$work/bgdv" || fail 'cannot back up installed symbols.'
  had_symbols=1
fi

awk -v begin="$begin" -v end="$end" '
  index($0, begin) { skip=1; next }
  index($0, end) { skip=0; next }
  !skip { print }
' "$registry" > "$work/clean.xml" || fail 'cannot prepare registry.'

if [[ "$action" == install ]]; then
  awk -v fragment="$source_dir/registry-layout.xml" -v begin="$begin" -v end="$end" '
    /<\/layoutList>/ && !added {
      print "  " begin
      while ((getline line < fragment) > 0) print "  " line
      close(fragment)
      print "  " end
      added=1
    }
    { print }
    END { if (!added) exit 1 }
  ' "$work/clean.xml" > "$work/next.xml" || fail 'cannot find layoutList in registry.'
else
  cp "$work/clean.xml" "$work/next.xml" || fail 'cannot prepare removal.'
fi
validate_xml "$work/next.xml" || fail 'updated XKB registry XML is invalid.'
cp -p "$registry" "$work/next-metadata.xml" || fail 'cannot preserve registry metadata.'
cat "$work/next.xml" > "$work/next-metadata.xml" || fail 'cannot stage registry.'
committed=1
mv "$work/next-metadata.xml" "$registry" || fail 'cannot write XKB registry.'
if [[ "$action" == install ]]; then
  cp "$source_dir/bgdv" "$symbols" || fail 'cannot install XKB symbols.'
  printf 'Installed Bulgarian (Dvorak phonetic). Open Settings > Keyboard > Input Sources and add it. Sign out and back in if it is not listed.\n'
else
  rm -f "$symbols" || fail 'cannot remove XKB symbols.'
  printf 'Removed Bulgarian (Dvorak phonetic). Remove it from Input Sources if still selected.\n'
fi
validate_xml "$registry" || fail 'installed XKB registry XML is invalid.'
committed=0
