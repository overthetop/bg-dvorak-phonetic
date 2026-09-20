# Mapping review — T005/T007

2026-09-19, agent review of two independent data paths; no human review or native typing claimed.

The expected fixture was manually transcribed from the 47-row layout contract. A separate
source decoding pass used libxkbcommon to resolve every keysym in linux/symbols-bg-dv.
All 47 positions and 188 assigned/absent level slots agree. The production mapping was created
from the source-decoded data, not copied from the expected fixture or generated C tables.
Caps expectations toggle only cased characters. All six dead accents include every base/Shift
character, space, repeat, Backspace cancellation and transitions to each different accent.
Precompositions use pinned Python 3.14.7 Unicode NFC; fallback is spacing accent plus character.

Physical Set-1 scan assignments were separately compared with Ubuntu evdev keycodes minus 8
for these 47 positions. Dvorak virtual-key values were independently compared with the distro
US Dvorak symbol table. Ctrl+A/C/V/X/Z map to AC01/AD08/AB09/AB05/AB10 respectively.
Supplemental control, navigation, function, ISO and keypad expectations are separate fixture
fields. macOS key-code 50 and Shift AD02/AD03 differences were reviewed against its keylayout;
Option/Command QWERTY behavior remains an explicit difference.

Contract tests compare outputs, Caps levels, scan codes, virtual keys and composition cases
against the independently maintained oracle. Native C metadata and generated-table agreement
are additional checks, not desktop typing evidence. Backspace/dead-state transitions and the
32-bit input ABI especially remain subject to T011's mandatory empirical proof.
