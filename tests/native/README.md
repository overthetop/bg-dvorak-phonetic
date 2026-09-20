# Windows typing probe

`windows_typing_probe.c` builds as x64 and x86 using the locked maintainer toolchain.
It logs actual WM_CHAR/WM_DEADCHAR and key events as JSON lines, including UTF-16 units,
scan codes, Shift/Ctrl/Alt/right-Alt/Caps state, active layout name and process/native architecture.
It does not install or select a layout, synthesize input, intercept other applications, or
change keyboard preferences. The window intentionally records input instead of implementing
an editor that could obscure the underlying Windows events.

Run each executable from PowerShell with redirected output, manually select the verified layout,
focus the probe window and type the fixture cases. Close the window to finish:

```powershell
.\build\windows-layout\windows_typing_probe-x64.exe > probe-x64.jsonl
.\build\windows-layout\windows_typing_probe-x86.exe > probe-x86.jsonl
```

Repeat the required scenarios in a real editor/browser as specified in the feature quickstart.
A pending dead accent may produce WM_DEADCHAR; the next WM_CHAR events establish the actual
composition. Record Backspace cancellation and switching between different dead accents explicitly.
The probe does not assert a case passed; compare the captured events with the independent fixture.

`--self-test` opens/closes a hidden window without typing or changing the active layout. Passing
it proves executable startup and the window message loop only, not mapping or desktop acceptance.
