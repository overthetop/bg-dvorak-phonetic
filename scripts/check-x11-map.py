#!/usr/bin/env python3
"""Check representative keys in a compiled XKB keymap."""

import re
import sys

keymap = open(sys.argv[1], encoding="utf-8").read()
expected = {
    "AC01": "Cyrillic_a",
    "AD01": "Cyrillic_yu",
    "AB02": "Cyrillic_ya",
    "AD02": "comma",
}
for key, symbol in expected.items():
    match = re.search(rf"key <{key}>\s*\{{(.*?)\}};", keymap, re.S)
    if not match or not re.search(rf"\b{symbol}\b", match.group(1)):
        sys.exit(f"{key} does not map to {symbol}")
print("X11 representative mappings passed")
