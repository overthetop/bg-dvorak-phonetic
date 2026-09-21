#!/usr/bin/env python3
"""Check representative installed keylayout data without a GUI login session."""
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
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
