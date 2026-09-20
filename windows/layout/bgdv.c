/* Generated from reviewed project mapping.
 * Scan/navigation/key-name tables adapted from Microsoft kbdus.c:
 * Copyright (c) 1985-2000, Microsoft Corporation. MS-PL; see LICENSE.Microsoft.
 * Changes: Dvorak VK positions, Bulgarian levels, AltGr/Caps and compose tables.
 */
#include <windows.h>
#include <kbd.h>
#define ALLOC_SECTION_LDATA
static ALLOC_SECTION_LDATA USHORT ausVK[] = {
    T00, T01, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36,
    0x37, 0x38, 0x39, 0x30, 0xDB, 0xDD, T0E, T0F,
    0xDE, 0xBC, 0xBE, 0x50, 0x59, 0x46, 0x47, 0x43,
    0x52, 0x4C, 0xBF, 0xBB, T1C, T1D, 0x41, 0x4F,
    0x45, 0x55, 0x49, 0x44, 0x48, 0x54, 0x4E, 0x53,
    0xBD, 0xC0, T2A, 0xDC, 0xBA, 0x51, 0x4A, 0x4B,
    0x58, 0x42, 0x4D, 0x57, 0x56, 0x5A,

    /*
     * Right-hand Shift key must have KBDEXT bit set.
     */
    T36 | KBDEXT,

    T37 | KBDMULTIVK,               // numpad_* + Shift/Alt -> SnapShot

    T38, T39, T3A, T3B, T3C, T3D, T3E,
    T3F, T40, T41, T42, T43, T44,

    /*
     * NumLock Key:
     *     KBDEXT     - VK_NUMLOCK is an Extended key
     *     KBDMULTIVK - VK_NUMLOCK or VK_PAUSE (without or with CTRL)
     */
    T45 | KBDEXT | KBDMULTIVK,

    T46 | KBDMULTIVK,

    /*
     * Number Pad keys:
     *     KBDNUMPAD  - digits 0-9 and decimal point.
     *     KBDSPECIAL - require special processing by Windows
     */
    T47 | KBDNUMPAD | KBDSPECIAL,   // Numpad 7 (Home)
    T48 | KBDNUMPAD | KBDSPECIAL,   // Numpad 8 (Up),
    T49 | KBDNUMPAD | KBDSPECIAL,   // Numpad 9 (PgUp),
    T4A,
    T4B | KBDNUMPAD | KBDSPECIAL,   // Numpad 4 (Left),
    T4C | KBDNUMPAD | KBDSPECIAL,   // Numpad 5 (Clear),
    T4D | KBDNUMPAD | KBDSPECIAL,   // Numpad 6 (Right),
    T4E,
    T4F | KBDNUMPAD | KBDSPECIAL,   // Numpad 1 (End),
    T50 | KBDNUMPAD | KBDSPECIAL,   // Numpad 2 (Down),
    T51 | KBDNUMPAD | KBDSPECIAL,   // Numpad 3 (PgDn),
    T52 | KBDNUMPAD | KBDSPECIAL,   // Numpad 0 (Ins),
    T53 | KBDNUMPAD | KBDSPECIAL,   // Numpad . (Del),

    T54, T55, T56, T57, T58, T59, T5A, T5B,
    T5C, T5D, T5E, T5F, T60, T61, T62, T63,
    T64, T65, T66, T67, T68, T69, T6A, T6B,
    T6C, T6D, T6E, T6F, T70, T71, T72, T73,
    T74, T75, T76, T77, T78, T79, T7A, T7B,
    T7C, T7D, T7E

};

static ALLOC_SECTION_LDATA VSC_VK aE0VscToVk[] = {
        { 0x10, X10 | KBDEXT              },  // Speedracer: Previous Track
        { 0x19, X19 | KBDEXT              },  // Speedracer: Next Track
        { 0x1D, X1D | KBDEXT              },  // RControl
        { 0x20, X20 | KBDEXT              },  // Speedracer: Volume Mute
        { 0x21, X21 | KBDEXT              },  // Speedracer: Launch App 2
        { 0x22, X22 | KBDEXT              },  // Speedracer: Media Play/Pause
        { 0x24, X24 | KBDEXT              },  // Speedracer: Media Stop
        { 0x2E, X2E | KBDEXT              },  // Speedracer: Volume Down
        { 0x30, X30 | KBDEXT              },  // Speedracer: Volume Up
        { 0x32, X32 | KBDEXT              },  // Speedracer: Browser Home
        { 0x35, X35 | KBDEXT              },  // Numpad Divide
        { 0x37, X37 | KBDEXT              },  // Snapshot
        { 0x38, X38 | KBDEXT              },  // RMenu
        { 0x47, X47 | KBDEXT              },  // Home
        { 0x48, X48 | KBDEXT              },  // Up
        { 0x49, X49 | KBDEXT              },  // Prior
        { 0x4B, X4B | KBDEXT              },  // Left
        { 0x4D, X4D | KBDEXT              },  // Right
        { 0x4F, X4F | KBDEXT              },  // End
        { 0x50, X50 | KBDEXT              },  // Down
        { 0x51, X51 | KBDEXT              },  // Next
        { 0x52, X52 | KBDEXT              },  // Insert
        { 0x53, X53 | KBDEXT              },  // Delete
        { 0x5B, X5B | KBDEXT              },  // Left Win
        { 0x5C, X5C | KBDEXT              },  // Right Win
        { 0x5D, X5D | KBDEXT              },  // Application
        { 0x5F, X5F | KBDEXT              },  // Speedracer: Sleep
        { 0x65, X65 | KBDEXT              },  // Speedracer: Browser Search
        { 0x66, X66 | KBDEXT              },  // Speedracer: Browser Favorites
        { 0x67, X67 | KBDEXT              },  // Speedracer: Browser Refresh
        { 0x68, X68 | KBDEXT              },  // Speedracer: Browser Stop
        { 0x69, X69 | KBDEXT              },  // Speedracer: Browser Forward
        { 0x6A, X6A | KBDEXT              },  // Speedracer: Browser Back
        { 0x6B, X6B | KBDEXT              },  // Speedracer: Launch App 1
        { 0x6C, X6C | KBDEXT              },  // Speedracer: Launch Mail
        { 0x6D, X6D | KBDEXT              },  // Speedracer: Launch Media Selector
        { 0x1C, X1C | KBDEXT              },  // Numpad Enter
        { 0x46, X46 | KBDEXT              },  // Break (Ctrl + Pause)
        { 0,      0                       }
};

static ALLOC_SECTION_LDATA VSC_VK aE1VscToVk[] = {
        { 0x1D, Y1D                       },  // Pause
        { 0   ,   0                       }
};


static VK_TO_BIT bits[] = {{VK_SHIFT, KBDSHIFT}, {VK_CONTROL, KBDCTRL}, {VK_MENU, KBDALT}, {0,0}};
static MODIFIERS modifiers = {bits, 7, {0,1,2,3,SHFT_INVALID,SHFT_INVALID,4,5}};
static VK_TO_WCHARS6 characters[] = {
{0xC0, 0, {0x0060, 0x007E, WCH_NONE, WCH_NONE, WCH_DEAD, WCH_DEAD}},
{0xFF, 0, {WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE, 0x0060, 0x007E}},
{0x31, 0, {0x0031, 0x0021, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0x32, 0, {0x0032, 0x0040, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0x33, 0, {0x0033, 0x0023, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0x34, 0, {0x0034, 0x0024, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0x35, 0, {0x0035, 0x0025, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0x36, 0, {0x0036, 0x005E, WCH_NONE, WCH_NONE, WCH_DEAD, WCH_DEAD}},
{0xFF, 0, {WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE, 0x005E, 0x005E}},
{0x37, 0, {0x0037, 0x0026, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0x38, 0, {0x0038, 0x002A, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0x39, 0, {0x0039, 0x0028, WCH_NONE, WCH_NONE, WCH_DEAD, WCH_DEAD}},
{0xFF, 0, {WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE, 0x0060, 0x02D8}},
{0x30, 0, {0x0030, 0x0029, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0xDB, 0, {0x005B, 0x007B, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0xDD, 0, {0x005D, 0x007D, WCH_NONE, WCH_NONE, WCH_DEAD, WCH_NONE}},
{0xFF, 0, {WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE, 0x007E, WCH_NONE}},
{0xDE, 1, {0x044E, 0x042E, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0xBC, 0, {0x002C, 0x201E, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0xBE, 0, {0x002E, 0x201C, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0x50, 1, {0x043F, 0x041F, 0x0010, 0x0010, WCH_NONE, WCH_NONE}},
{0x59, 1, {0x0443, 0x0423, 0x0019, 0x0019, WCH_NONE, WCH_NONE}},
{0x46, 1, {0x0444, 0x0424, 0x0006, 0x0006, WCH_NONE, WCH_NONE}},
{0x47, 1, {0x0433, 0x0413, 0x0007, 0x0007, WCH_NONE, WCH_NONE}},
{0x43, 1, {0x0446, 0x0426, 0x0003, 0x0003, 0x00A9, 0x00A9}},
{0x52, 1, {0x0440, 0x0420, 0x0012, 0x0012, 0x00AE, 0x00AE}},
{0x4C, 1, {0x043B, 0x041B, 0x000C, 0x000C, WCH_NONE, WCH_NONE}},
{0xBF, 0, {0x002F, 0x003F, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0xBB, 1, {0x0448, 0x0428, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0x41, 1, {0x0430, 0x0410, 0x0001, 0x0001, WCH_NONE, WCH_NONE}},
{0x4F, 1, {0x043E, 0x041E, 0x000F, 0x000F, WCH_NONE, WCH_NONE}},
{0x45, 5, {0x0435, 0x0415, 0x0005, 0x0005, 0x044D, 0x042D}},
{0x55, 5, {0x044A, 0x042A, 0x0015, 0x0015, 0x046B, 0x046A}},
{0x49, 1, {0x0438, 0x0418, 0x0009, 0x0009, WCH_NONE, WCH_NONE}},
{0x44, 1, {0x0434, 0x0414, 0x0004, 0x0004, WCH_NONE, WCH_NONE}},
{0x48, 1, {0x0445, 0x0425, 0x0008, 0x0008, WCH_NONE, WCH_NONE}},
{0x54, 1, {0x0442, 0x0422, 0x0014, 0x0014, 0x2122, 0x2122}},
{0x4E, 1, {0x043D, 0x041D, 0x000E, 0x000E, WCH_NONE, WCH_NONE}},
{0x53, 1, {0x0441, 0x0421, 0x0013, 0x0013, 0x00A9, 0x00A9}},
{0xBD, 0, {0x002D, 0x005F, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0xBA, 0, {0x003B, 0x003A, WCH_NONE, WCH_NONE, WCH_DEAD, WCH_DEAD}},
{0xFF, 0, {WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE, 0x02DB, 0x02DD}},
{0x51, 5, {0x044F, 0x042F, 0x0011, 0x0011, 0x0463, 0x0462}},
{0x4A, 5, {0x0439, 0x0419, 0x000A, 0x000A, 0x046D, 0x046C}},
{0x4B, 1, {0x043A, 0x041A, 0x000B, 0x000B, WCH_NONE, WCH_NONE}},
{0x58, 1, {0x0447, 0x0427, 0x0018, 0x0018, WCH_NONE, WCH_NONE}},
{0x42, 1, {0x0431, 0x0411, 0x0002, 0x0002, WCH_NONE, WCH_NONE}},
{0x4D, 1, {0x043C, 0x041C, 0x000D, 0x000D, WCH_NONE, WCH_NONE}},
{0x57, 1, {0x0436, 0x0416, 0x0017, 0x0017, WCH_NONE, WCH_NONE}},
{0x56, 1, {0x0432, 0x0412, 0x0016, 0x0016, WCH_NONE, WCH_NONE}},
{0x5A, 1, {0x0437, 0x0417, 0x001A, 0x001A, WCH_NONE, WCH_NONE}},
{0xDC, 1, {0x0449, 0x0429, WCH_NONE, WCH_NONE, WCH_NONE, WCH_NONE}},
{0x20, 0, {0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020}},
{0x0D, 0, {0x000D, 0x000D, 0x000D, 0x000D, 0x000D, 0x000D}},
{0x09, 0, {0x0009, 0x0009, 0x0009, 0x0009, 0x0009, 0x0009}},
{0x08, 0, {0x0008, 0x0008, 0x0008, 0x0008, 0x0008, 0x0008}},
{0x1B, 0, {0x001B, 0x001B, 0x001B, 0x001B, 0x001B, 0x001B}},
{0xE2, 0, {0x005C, 0x007C, WCH_NONE, WCH_NONE, 0x005C, 0x007C}},
{0x60, 0, {0x0030, 0x0030, WCH_NONE, WCH_NONE, 0x0030, 0x0030}},
{0x61, 0, {0x0031, 0x0031, WCH_NONE, WCH_NONE, 0x0031, 0x0031}},
{0x62, 0, {0x0032, 0x0032, WCH_NONE, WCH_NONE, 0x0032, 0x0032}},
{0x63, 0, {0x0033, 0x0033, WCH_NONE, WCH_NONE, 0x0033, 0x0033}},
{0x64, 0, {0x0034, 0x0034, WCH_NONE, WCH_NONE, 0x0034, 0x0034}},
{0x65, 0, {0x0035, 0x0035, WCH_NONE, WCH_NONE, 0x0035, 0x0035}},
{0x66, 0, {0x0036, 0x0036, WCH_NONE, WCH_NONE, 0x0036, 0x0036}},
{0x67, 0, {0x0037, 0x0037, WCH_NONE, WCH_NONE, 0x0037, 0x0037}},
{0x68, 0, {0x0038, 0x0038, WCH_NONE, WCH_NONE, 0x0038, 0x0038}},
{0x69, 0, {0x0039, 0x0039, WCH_NONE, WCH_NONE, 0x0039, 0x0039}},
{0x6A, 0, {0x002A, 0x002A, WCH_NONE, WCH_NONE, 0x002A, 0x002A}},
{0x6B, 0, {0x002B, 0x002B, WCH_NONE, WCH_NONE, 0x002B, 0x002B}},
{0x6D, 0, {0x002D, 0x002D, WCH_NONE, WCH_NONE, 0x002D, 0x002D}},
{0x6E, 0, {0x002E, 0x002E, WCH_NONE, WCH_NONE, 0x002E, 0x002E}},
{0x6F, 0, {0x002F, 0x002F, WCH_NONE, WCH_NONE, 0x002F, 0x002F}},
{0, 0, {0}},
};
static VK_TO_WCHAR_TABLE character_tables[] = {
    {(PVK_TO_WCHARS1)characters, 6, sizeof(characters[0])}, {NULL,0,0}
};
static DEADKEY dead_keys[] = {
{MAKELONG(0x0415, 0x0060), 0x0400, 0},
{MAKELONG(0x0418, 0x0060), 0x040D, 0},
{MAKELONG(0x0435, 0x0060), 0x0450, 0},
{MAKELONG(0x0438, 0x0060), 0x045D, 0},
{MAKELONG(0x0020, 0x0060), 0x0060, 0},
{MAKELONG(0x0060, 0x0060), 0x0060, 0},
{MAKELONG(0x0020, 0x007E), 0x007E, 0},
{MAKELONG(0x007E, 0x007E), 0x007E, 0},
{MAKELONG(0x0020, 0x005E), 0x005E, 0},
{MAKELONG(0x005E, 0x005E), 0x005E, 0},
{MAKELONG(0x0410, 0x02D8), 0x04D0, 0},
{MAKELONG(0x0415, 0x02D8), 0x04D6, 0},
{MAKELONG(0x0416, 0x02D8), 0x04C1, 0},
{MAKELONG(0x0418, 0x02D8), 0x0419, 0},
{MAKELONG(0x0423, 0x02D8), 0x040E, 0},
{MAKELONG(0x0430, 0x02D8), 0x04D1, 0},
{MAKELONG(0x0435, 0x02D8), 0x04D7, 0},
{MAKELONG(0x0436, 0x02D8), 0x04C2, 0},
{MAKELONG(0x0438, 0x02D8), 0x0439, 0},
{MAKELONG(0x0443, 0x02D8), 0x045E, 0},
{MAKELONG(0x0020, 0x02D8), 0x02D8, 0},
{MAKELONG(0x02D8, 0x02D8), 0x02D8, 0},
{MAKELONG(0x0020, 0x02DB), 0x02DB, 0},
{MAKELONG(0x02DB, 0x02DB), 0x02DB, 0},
{MAKELONG(0x0423, 0x02DD), 0x04F2, 0},
{MAKELONG(0x0443, 0x02DD), 0x04F3, 0},
{MAKELONG(0x0020, 0x02DD), 0x02DD, 0},
{MAKELONG(0x02DD, 0x02DD), 0x02DD, 0},
{0,0,0}
};
static ALLOC_SECTION_LDATA VSC_LPWSTR aKeyNames[] = {
    0x01,    L"Esc",
    0x0e,    L"Backspace",
    0x0f,    L"Tab",
    0x1c,    L"Enter",
    0x1d,    L"Ctrl",
    0x2a,    L"Shift",
    0x36,    L"Right Shift",
    0x37,    L"Num *",
    0x38,    L"Alt",
    0x39,    L"Space",
    0x3a,    L"Caps Lock",
    0x3b,    L"F1",
    0x3c,    L"F2",
    0x3d,    L"F3",
    0x3e,    L"F4",
    0x3f,    L"F5",
    0x40,    L"F6",
    0x41,    L"F7",
    0x42,    L"F8",
    0x43,    L"F9",
    0x44,    L"F10",
    0x45,    L"Pause",
    0x46,    L"Scroll Lock",
    0x47,    L"Num 7",
    0x48,    L"Num 8",
    0x49,    L"Num 9",
    0x4a,    L"Num -",
    0x4b,    L"Num 4",
    0x4c,    L"Num 5",
    0x4d,    L"Num 6",
    0x4e,    L"Num +",
    0x4f,    L"Num 1",
    0x50,    L"Num 2",
    0x51,    L"Num 3",
    0x52,    L"Num 0",
    0x53,    L"Num Del",
    0x54,    L"Sys Req",
    0x57,    L"F11",
    0x58,    L"F12",
    0x7c,    L"F13",
    0x7d,    L"F14",
    0x7e,    L"F15",
    0x7f,    L"F16",
    0x80,    L"F17",
    0x81,    L"F18",
    0x82,    L"F19",
    0x83,    L"F20",
    0x84,    L"F21",
    0x85,    L"F22",
    0x86,    L"F23",
    0x87,    L"F24",
    0   ,    NULL
};

static ALLOC_SECTION_LDATA VSC_LPWSTR aKeyNamesExt[] = {
    0x1c,    L"Num Enter",
    0x1d,    L"Right Ctrl",
    0x35,    L"Num /",
    0x37,    L"Prnt Scrn",
    0x38,    L"Right Alt",
    0x45,    L"Num Lock",
    0x46,    L"Break",
    0x47,    L"Home",
    0x48,    L"Up",
    0x49,    L"Page Up",
    0x4b,    L"Left",
    0x4d,    L"Right",
    0x4f,    L"End",
    0x50,    L"Down",
    0x51,    L"Page Down",
    0x52,    L"Insert",
    0x53,    L"Delete",
    0x54,    L"<00>",
    0x56,    L"Help",
    0x5b,    L"Left Windows",
    0x5c,    L"Right Windows",
    0x5d,    L"Application",
    0   ,    NULL
};


static KBDTABLES tables = {
    &modifiers, character_tables, dead_keys, aKeyNames, aKeyNamesExt, NULL,
    ausVK, sizeof(ausVK)/sizeof(ausVK[0]), aE0VscToVk, aE1VscToVk,
    MAKELONG(KLLF_ALTGR, KBD_VERSION), 0, 0, NULL, 0, 0
};
PKBDTABLES KbdLayerDescriptor(VOID) { return &tables; }
