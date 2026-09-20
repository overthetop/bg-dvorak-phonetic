/* Native input evidence probe; no layout installation, activation or remapping.
 * Build x64 and x86 with the locked SDK. Run from a terminal with stdout redirected
 * to a log, manually select the test layout, focus this window, and type cases.
 * --self-test creates and closes a hidden window without synthesizing text input.
 */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0A00
#include <windows.h>

static HWND probe_window;
static USHORT native_machine;
static USHORT process_machine;

static void record(const char *event, UINT message, WPARAM value, LPARAM detail)
{
    char line[768];
    WCHAR wide_layout[KL_NAMELENGTH];
    char layout[KL_NAMELENGTH];
    DWORD written;
    int length;
    unsigned int i;
    if (!GetKeyboardLayoutNameW(wide_layout)) {
        ExitProcess(2);
    }
    for (i = 0; i < KL_NAMELENGTH; ++i) {
        layout[i] = (char)wide_layout[i];
    }
    length = wsprintfA(line,
        "{\"event\":\"%s\",\"message\":%u,\"value\":%u,\"scan_code\":%u,"
        "\"extended\":%u,\"shift\":%u,\"ctrl\":%u,\"alt\":%u,\"right_alt\":%u,"
        "\"caps\":%u,\"layout\":\"%s\",\"process_bits\":%u,"
        "\"process_machine\":%u,\"native_machine\":%u}\n",
        event, message, (unsigned int)value, (unsigned int)((detail >> 16) & 0xff),
        (unsigned int)((detail >> 24) & 1),
        (GetKeyState(VK_SHIFT) & 0x8000) != 0,
        (GetKeyState(VK_CONTROL) & 0x8000) != 0,
        (GetKeyState(VK_MENU) & 0x8000) != 0,
        (GetKeyState(VK_RMENU) & 0x8000) != 0,
        (GetKeyState(VK_CAPITAL) & 1) != 0,
        layout, (unsigned int)(sizeof(void *) * 8), process_machine, native_machine);
    if (length <= 0 || !WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), line,
                                (DWORD)length, &written, NULL) || written != (DWORD)length) {
        ExitProcess(3);
    }
}

static LRESULT CALLBACK window_proc(HWND window, UINT message, WPARAM value, LPARAM detail)
{
    switch (message) {
    case WM_KEYDOWN:
    case WM_SYSKEYDOWN:
        record("key_down", message, value, detail);
        break;
    case WM_CHAR:
    case WM_SYSCHAR:
        /* Each value is the actual UTF-16 unit delivered by TranslateMessage. */
        record("char", message, value, detail);
        break;
    case WM_DEADCHAR:
    case WM_SYSDEADCHAR:
        record("dead_char", message, value, detail);
        break;
    case WM_INPUTLANGCHANGE:
        record("language", message, value, 0);
        break;
    case WM_DESTROY:
        record("finish", message, 0, 0);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(window, message, value, detail);
}

/* A fixed flag parser avoids importing a C runtime merely to parse one option. */
static BOOL self_test_requested(void)
{
    const WCHAR *command = GetCommandLineW();
    const WCHAR option[] = L"--self-test";
    unsigned int i;
    for (; *command; ++command) {
        if (command != GetCommandLineW() && command[-1] != L' ') {
            continue;
        }
        for (i = 0; option[i] && command[i] == option[i]; ++i) {}
        if (!option[i] && (!command[i] || command[i] == L' ')) {
            return TRUE;
        }
    }
    return FALSE;
}

void __cdecl probe_entry(void)
{
    WNDCLASSW window_class = {0};
    MSG message;
    BOOL result;
    BOOL self_test = self_test_requested();
    HINSTANCE instance = GetModuleHandleW(NULL);
    if (!IsWow64Process2(GetCurrentProcess(), &process_machine, &native_machine)) {
        ExitProcess(4);
    }
    window_class.lpfnWndProc = window_proc;
    window_class.hInstance = instance;
    window_class.lpszClassName = L"BgDvorakInputEvidenceProbe";
    window_class.hCursor = LoadCursorW(NULL, IDC_IBEAM);
    if (!RegisterClassW(&window_class)) {
        ExitProcess(5);
    }
    probe_window = CreateWindowExW(0, window_class.lpszClassName,
        L"Bulgarian Dvorak probe - select the layout manually, focus here, type; close to finish",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 900, 250,
        NULL, NULL, instance, NULL);
    if (!probe_window) {
        ExitProcess(6);
    }
    record("start", 0, 0, 0);
    if (self_test) {
        if (!PostMessageW(probe_window, WM_CLOSE, 0, 0)) {
            ExitProcess(7);
        }
    } else {
        ShowWindow(probe_window, SW_SHOW);
        SetFocus(probe_window);
    }
    while ((result = GetMessageW(&message, NULL, 0, 0)) > 0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    ExitProcess(result == -1 ? 8 : 0);
}
