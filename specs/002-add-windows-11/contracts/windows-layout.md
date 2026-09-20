# Windows Layout Asset Contract

## Identity and packaging

Logical ID: `bg-dvorak-phonetic`. Display name: `Bulgarian (Dvorak phonetic)`.
Language association: Bulgarian (`0402`). Proposed project KLID: `A0D00402`; Layout Id: `0D00`.
These are project design choices, not Microsoft-assigned global reservations. Check collisions
and native discovery during the first implementation proof; never replace another identity.
The validated identity is then stable across releases and repairs.

The release contains `windows/assets/manifest.json` and its prebuilt x64 DLL. Build provenance
records source revision, mapping digest, exact compiler/SDK/WDK versions, and artifact hashes.
The generated table source, resource definition, module export definition, and build project
are reviewable under `windows/layout/`. The DLL exports `KbdLayerDescriptor`, uses the selected
kit's table ABI, and contains the display-name string resource used by registration.
The build does not embed installation/update/repair logic. No runtime build tools are required.
Use versioned installed DLL names; retain the old version for rollback.

## Physical-key and modifier semantics

Use the explicit entries in `linux/symbols-bg-dv` as the Windows character authority. The table
below uses XKB physical positions, not the keycap labels from an already selected layout.
Map these positions to the standard Windows scan codes in `windows/mapping.json` and review
that translation separately. Do not derive physical positions from the currently active keyboard.

- Base/Shift use columns one/two. Caps Lock toggles case only for cased letters; Shift+Caps
  reverses that case. Caps does not turn digits or punctuation into their shifted symbols.
- AltGr (right Alt) and Shift+AltGr expose explicit Linux levels three/four. An absent level
  produces no character; it does not invent a new Latin layer. Caps toggles cased extended letters.
  Windows may represent AltGr as Ctrl+Alt; document/test this interaction with shortcuts.
- Ctrl shortcuts use US Dvorak virtual-key positions; test Ctrl+A/C/V/X/Z in native applications.
  No global interception or rewrite of application shortcuts. Left Alt/Win combinations retain
  OS behavior. macOS Command/QWERTY behavior is not copied to Windows.
- Preserve ordinary Space, Enter, Tab, Backspace, Escape, navigation/function keys and keypad
  behavior from the native base layout. NumLock controls keypad digits; keypad decimal is `.`.
  ISO extra key uses backslash/bar. These supplement positions absent from the Linux fragment.
- Dead accents have explicit deterministic compose tables: grave, tilde, circumflex, breve,
  ogonek, double acute. Space or repeating the same accent yields its spacing accent. For an
  available base/Shift character, emit its NFC precomposed form when Unicode defines one;
  otherwise emit the spacing accent followed by the character. Backspace cancels a pending accent;
  a different dead accent emits the previous spacing accent and starts the new pending accent.
  Record expected sequences in fixtures. This finite Windows composition behavior does not claim
  to replicate a user's configurable Linux Compose table.

## Required physical mapping

`—` means no explicitly assigned extended output. `dead_*` names identify the state above.

| Position | Base | Shift | AltGr | Shift+AltGr |
| --- | --- | --- | --- | --- |
| TLDE | ` | ~ | dead_grave | dead_tilde |
| AE01 | 1 | ! | — | — |
| AE02 | 2 | @ | — | — |
| AE03 | 3 | # | — | — |
| AE04 | 4 | $ | — | — |
| AE05 | 5 | % | — | — |
| AE06 | 6 | ^ | dead_circumflex | dead_circumflex |
| AE07 | 7 | & | — | — |
| AE08 | 8 | * | — | — |
| AE09 | 9 | ( | dead_grave | dead_breve |
| AE10 | 0 | ) | — | — |
| AE11 | [ | { | — | — |
| AE12 | ] | } | dead_tilde | — |
| AD01 | ю | Ю | — | — |
| AD02 | , | „ | — | — |
| AD03 | . | “ | — | — |
| AD04 | п | П | — | — |
| AD05 | у | У | — | — |
| AD06 | ф | Ф | — | — |
| AD07 | г | Г | — | — |
| AD08 | ц | Ц | © | © |
| AD09 | р | Р | ® | ® |
| AD10 | л | Л | — | — |
| AD11 | / | ? | — | — |
| AD12 | ш | Ш | — | — |
| AC01 | а | А | — | — |
| AC02 | о | О | — | — |
| AC03 | е | Е | э | Э |
| AC04 | ъ | Ъ | ѫ | Ѫ |
| AC05 | и | И | — | — |
| AC06 | д | Д | — | — |
| AC07 | х | Х | — | — |
| AC08 | т | Т | ™ | ™ |
| AC09 | н | Н | — | — |
| AC10 | с | С | © | © |
| AC11 | - | _ | — | — |
| AB01 | ; | : | dead_ogonek | dead_doubleacute |
| AB02 | я | Я | ѣ | Ѣ |
| AB03 | й | Й | ѭ | Ѭ |
| AB04 | к | К | — | — |
| AB05 | ч | Ч | — | — |
| AB06 | б | Б | — | — |
| AB07 | м | М | — | — |
| AB08 | ж | Ж | — | — |
| AB09 | в | В | — | — |
| AB10 | з | З | — | — |
| BKSL | щ | Щ | — | — |

## Known existing-platform differences

macOS ANSI key code 50 produces ч/Ч, whereas Linux TLDE produces grave/tilde. macOS Shift
at the physical AD02/AD03 positions produces quotation/equal characters; Windows follows Linux
„/“. macOS Option and Command maps include Latin QWERTY behavior; Windows follows the explicit
Linux extended levels and the US Dvorak shortcut policy above. Existing macOS/Linux files are
unchanged. List these differences in end-user mapping documentation before release.

## Build and native proof gates

1. Generate the mapping manifest and native tables deterministically; review all explicit source
   levels and compare fixtures independently, including Caps and dead-key sequences.
2. Build using locked VS/SDK/WDK inputs. Check machine type, export, resource ID, source/mapping
   provenance and hash before registration. A malicious or untrusted DLL is not made trustworthy
   by loading it to inspect the export; inspect metadata first and load only trusted build output
   in a disposable test process.
3. In a disposable 25H2 Home/Pro x64 desktop with normal security settings, prove registration,
   Settings discovery, selection, all expected mappings, shortcuts, and sign-in persistence.
4. Include a native x64 editor, x64 browser field, and compiled 32-bit text-input probe. The chosen
   deployment is one native x64 layout DLL; if the 32-bit probe fails, block dependent work and
   revise the ABI/artifact design from measured evidence. Do not assume a generic x86 DLL is a
   valid WOW64 layout and do not waive the acceptance case.
5. Test an update while the previous layout is loaded. Files/registration may be current while
   active applications still use the old version; report pending session refresh honestly.
6. Validate policy/signature compatibility without disabling Secure Boot or system protection.
   Any policy rejection is an implementation/release blocker; do not introduce a bypass.

Commands and evidence collection are in [quickstart.md](../quickstart.md). These are future
acceptance requirements, not claims that a native binary or mapping tests currently exist.
