# Release desktop smoke test

Record the release version, machine or VM, OS version, session type, date, tester, and pass/fail result for each row. These desktop checks supplement GitHub Actions; headless jobs cannot prove that Settings lists or activates a layout.

| Platform | OS version | Session | Layout listed | Selection works | Typing works | Tester/date |
| --- | --- | --- | --- | --- | --- | --- |
| Ubuntu GNOME | 24.04 | Wayland |  |  |  |  |
| Ubuntu GNOME | 24.04 | X11 |  |  |  |  |
| macOS |  | logged-in desktop |  |  |  |  |

For each row, install from the release ZIP, add **Bulgarian (Dvorak phonetic)** in the system input-source UI, and type the physical keys corresponding to XKB `<AC01>`, `<AD01>`, and `<AB02>` (expected Cyrillic `а`, `ю`, `я`). Check the matching uppercase letters with Shift and a punctuation key. Install again and confirm there is one layout entry. Remove the layout and confirm the other input sources still work. On Ubuntu, repeat this in both the Wayland and X11 GNOME sessions.

Do not mark a desktop row passed from CI alone. Record any failed key or discovery step with its OS and session details.
