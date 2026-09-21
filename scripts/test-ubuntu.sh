#!/bin/bash
set -euo pipefail

archive=${1:?pass the Ubuntu release ZIP}
repo=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
unzip -q "$archive" -d "$work"
package=$(find "$work" -mindepth 1 -maxdepth 1 -type d -name '*-ubuntu' -print -quit)
[[ -n "$package" ]] || { printf 'Ubuntu archive is empty.\n' >&2; exit 1; }

# A disposable registry first exercises ownership, repeat installs, and errors.
mkdir -p "$work/xkb/rules" "$work/xkb/symbols"
printf 'ID=ubuntu\n' > "$work/os-release"
printf '%s\n' '<?xml version="1.0"?>' '<xkbConfigRegistry>' '<layoutList>' '<layout><configItem><name>us</name></configItem></layout>' '</layoutList>' '</xkbConfigRegistry>' > "$work/xkb/rules/evdev.xml"
export BGDV_TEST_OS_RELEASE="$work/os-release" BGDV_XKB_ROOT="$work/xkb"
"$package/install.sh"
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

cp "$work/xkb/rules/evdev.xml" "$work/valid-registry.xml"
printf '<broken>\n' > "$work/xkb/rules/evdev.xml"
if "$package/install.sh" >"$work/error.log" 2>&1; then exit 1; fi
grep -Fq 'existing XKB registry XML is invalid' "$work/error.log"
cp "$work/valid-registry.xml" "$work/xkb/rules/evdev.xml"

# The remaining checks use the runner's disposable Ubuntu XKB root.
unset BGDV_TEST_OS_RELEASE BGDV_XKB_ROOT
[[ $(. /etc/os-release; printf '%s' "$ID") == ubuntu ]] || { printf 'Ubuntu runner required.\n' >&2; exit 1; }
"$package/install.sh"
"$package/install.sh"
python3 -c 'import xml.etree.ElementTree as E; r=E.parse("/usr/share/X11/xkb/rules/evdev.xml").getroot(); assert len(r.findall(".//layout[configItem/name=\"bgdv\"]")) == 1'
xkbcli compile-keymap --layout bgdv > "$work/wayland.xkb"
grep -Fq 'Cyrillic_a' "$work/wayland.xkb"
xvfb-run -a sh -c 'setxkbmap -layout bgdv -print | xkbcomp -xkb - "$1"' sh "$work/x11.xkb"
python3 "$repo/scripts/check-x11-map.py" "$work/x11.xkb"

cp /usr/share/X11/xkb/symbols/bgdv "$work/original-bgdv"
sudo sed -i 's/Cyrillic_a, Cyrillic_A/Cyrillic_o, Cyrillic_A/' /usr/share/X11/xkb/symbols/bgdv
xvfb-run -a sh -c 'setxkbmap -layout bgdv -print | xkbcomp -xkb - "$1"' sh "$work/mutated.xkb"
if python3 "$repo/scripts/check-x11-map.py" "$work/mutated.xkb"; then
  printf 'Mutated key was not detected.\n' >&2
  exit 1
fi
sudo cp "$work/original-bgdv" /usr/share/X11/xkb/symbols/bgdv
"$package/uninstall.sh"
[[ ! -e /usr/share/X11/xkb/symbols/bgdv ]]
printf 'Ubuntu archive and X11 checks passed.\n'
