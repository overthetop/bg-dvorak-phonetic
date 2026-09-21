#!/usr/bin/env python3
"""Check representative installed keylayout data without a GUI login session."""
import sys
import re
import xml.etree.ElementTree as ET

source = open(sys.argv[1], encoding="utf-8").read()
# ElementTree rejects XML 1.1 control-character references used by this layout.
source = re.sub(r"&#x([0-9a-fA-F]+);", lambda match:
    "" if int(match.group(1), 16) < 32 and int(match.group(1), 16) not in (9, 10, 13)
    else match.group(0), source)
root = ET.fromstring(source)
maps = {}
for keymap in root.findall("./keyMapSet/keyMap"):
    maps[keymap.get("index")] = {
        key.get("code"): key.get("output") for key in keymap.findall("key")
    }
for index, code, expected in [
    ("0", "1", "о"), ("0", "7", "я"), ("0", "13", ","),
    ("1", "7", "Я"),
]:
    actual = maps[index].get(code)
    if actual != expected:
        raise SystemExit(f"keymap {index}, key {code}: expected {expected!r}, got {actual!r}")
print("Installed macOS keylayout contains the expected base and Shift mappings.")
