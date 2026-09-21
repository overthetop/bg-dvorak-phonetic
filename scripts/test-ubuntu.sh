#!/bin/bash
set -euo pipefail

archive=${1:?pass the Ubuntu release ZIP}
repo=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
system_installed=0
mutation_pending=0
cleanup() {
  local status
  status=$1
  trap - EXIT
  if (( mutation_pending )) && ! sudo cp "$work/original-bgdv" /usr/share/X11/xkb/symbols/bgdv; then
    printf 'Could not restore the original XKB symbols.\n' >&2
    status=1
  fi
  if (( system_installed )) && ! "$package/uninstall.sh"; then
    printf 'Could not remove the installed XKB layout.\n' >&2
    status=1
  fi
  rm -rf "$work" || status=1
  exit "$status"
}
trap 'cleanup "$?"' EXIT
unzip -q "$archive" -d "$work"
package=$(find "$work" -mindepth 1 -maxdepth 1 -type d -name '*-ubuntu' -print -quit)
[[ -n "$package" ]] || { printf 'Ubuntu archive is empty.\n' >&2; exit 1; }

# A disposable registry first exercises ownership, repeat installs, and errors.
mkdir -p "$work/xkb/rules" "$work/xkb/symbols"
printf 'ID=ubuntu\n' > "$work/os-release"
printf '%s\n' '<?xml version="1.0"?>' '<xkbConfigRegistry>' '<layoutList>' '<layout><configItem><name>us</name></configItem></layout>' '</layoutList>' '</xkbConfigRegistry>' > "$work/xkb/rules/evdev.xml"
export BGDV_TEST_OS_RELEASE="$work/os-release" BGDV_XKB_ROOT="$work/xkb"
"$package/install.sh"
system_installed=1
"$package/install.sh"
[[ $(grep -Fc '<name>bgdv</name>' "$work/xkb/rules/evdev.xml") -eq 1 ]]
python3 -c 'import sys, xml.etree.ElementTree as E; E.parse(sys.argv[1])' "$work/xkb/rules/evdev.xml"
"$package/uninstall.sh"
grep -Fq '<name>us</name>' "$work/xkb/rules/evdev.xml"
[[ ! -e "$work/xkb/symbols/bgdv" ]]

# An existing collision must fail without changing unrelated data.
printf 'unmanaged\n' > "$work/xkb/symbols/bgdv"
if "$package/install.sh" >"$work/error.log" 2>&1; then exit 1; fi
grep -Fq 'not owned by this project' "$work/error.log"
grep -Fq '<name>us</name>' "$work/xkb/rules/evdev.xml"
rm "$work/xkb/symbols/bgdv"
ln -s "$work/nonexistent" "$work/xkb/symbols/bgdv"
if "$package/install.sh" >"$work/error.log" 2>&1; then
  printf 'Dangling symbols symlink was accepted.\n' >&2
  exit 1
fi
grep -Fq 'not a regular file' "$work/error.log"
rm "$work/xkb/symbols/bgdv"

cp "$work/xkb/rules/evdev.xml" "$work/valid-registry.xml"
printf '<broken>\n' > "$work/xkb/rules/evdev.xml"
if "$package/install.sh" >"$work/error.log" 2>&1; then exit 1; fi
grep -Fq 'existing XKB registry XML is invalid' "$work/error.log"
cp "$work/valid-registry.xml" "$work/xkb/rules/evdev.xml"
printf 'Disposable install, repeat install, removal, ownership, and invalid registry checks passed.\n'

# The remaining checks use the runner's disposable Ubuntu XKB root.
unset BGDV_TEST_OS_RELEASE BGDV_XKB_ROOT
grep -Eq '^ID="?ubuntu"?$' /etc/os-release || { printf 'Ubuntu runner required.\n' >&2; exit 1; }
"$package/install.sh"
"$package/install.sh"
python3 -c 'import xml.etree.ElementTree as E; r=E.parse("/usr/share/X11/xkb/rules/evdev.xml").getroot(); assert sum(e.findtext("configItem/name") == "bgdv" for e in r.findall(".//layout")) == 1'
gnome_cflags_text=$(pkg-config --cflags gnome-desktop-3.0)
gnome_libs_text=$(pkg-config --libs gnome-desktop-3.0)
read -r -a gnome_cflags <<< "$gnome_cflags_text"
read -r -a gnome_libs <<< "$gnome_libs_text"
cc "${gnome_cflags[@]}" -o "$work/check-gnome-layout" "$repo/scripts/check-gnome-layout.c" "${gnome_libs[@]}"
"$work/check-gnome-layout"
xkbcli compile-keymap --layout bgdv > "$work/wayland.xkb"
grep -Fq 'Cyrillic_a' "$work/wayland.xkb"
printf 'Wayland XKB compilation passed.\n'
# $1 belongs to the shell started by xvfb-run.
# shellcheck disable=SC2016
xvfb-run -a bash -o pipefail -c 'setxkbmap -layout bgdv -print | xkbcomp -xkb - "$1"' bash "$work/x11.xkb"
python3 "$repo/scripts/check-x11-map.py" "$work/x11.xkb"

cp /usr/share/X11/xkb/symbols/bgdv "$work/original-bgdv"
mutation_pending=1
sudo sed -i 's/Cyrillic_a, Cyrillic_A/Cyrillic_o, Cyrillic_A/' /usr/share/X11/xkb/symbols/bgdv
# $1 belongs to the shell started by xvfb-run.
# shellcheck disable=SC2016
xvfb-run -a bash -o pipefail -c 'setxkbmap -layout bgdv -print | xkbcomp -xkb - "$1"' bash "$work/mutated.xkb"
if python3 "$repo/scripts/check-x11-map.py" "$work/mutated.xkb"; then
  printf 'Mutated key was not detected.\n' >&2
  exit 1
fi
printf 'X11 wrong-key mutation was rejected.\n'
sudo cp "$work/original-bgdv" /usr/share/X11/xkb/symbols/bgdv
mutation_pending=0
"$package/uninstall.sh"
system_installed=0
[[ ! -e /usr/share/X11/xkb/symbols/bgdv ]]
printf 'Ubuntu archive and X11 checks passed.\n'
