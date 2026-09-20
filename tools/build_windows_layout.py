"""Deterministic native layout generation and explicit, offline maintainer build.

Requires Python 3.14.7. Never imported by product installation workflows.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DISPLAY_NAME = "Bulgarian (Dvorak phonetic)"
POSITIONS = {"TLDE", "BKSL"} | {
    f"{prefix}{index:02d}"
    for prefix, count in [("AE", 12), ("AD", 12), ("AC", 11), ("AB", 10)]
    for index in range(1, count + 1)
}


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_mapping(mapping: dict[str, Any]) -> None:
    """Reject incomplete/ambiguous physical maps before generating native source."""
    keys = mapping.get("keys", [])
    if mapping.get("schema_version") != 1 or len(keys) != 47:
        raise ValueError("Expected mapping schema 1 and 47 keys")
    if {key["position"] for key in keys} != POSITIONS:
        raise ValueError("Missing or duplicate physical position")
    for field in ("scan_code", "virtual_key"):
        values = [key[field] for key in keys]
        if len(set(values)) != 47 or any(type(v) is not int or not 0 < v < 255 for v in values):
            raise ValueError(f"Invalid or duplicate {field}")
    dead_names = {item["name"] for item in mapping["dead_keys"]}
    if dead_names != {
        "dead_grave",
        "dead_tilde",
        "dead_circumflex",
        "dead_breve",
        "dead_ogonek",
        "dead_doubleacute",
    }:
        raise ValueError("Expected six named dead accents")
    for key in keys:
        for field in ("levels", "caps_levels"):
            if len(key[field]) != 4:
                raise ValueError("Expected four explicit modifier levels")
            for value in key[field]:
                if (
                    value is not None
                    and value not in dead_names
                    and (not isinstance(value, str) or len(value) != 1 or ord(value) > 0xFFFF)
                ):
                    raise ValueError("Invalid Unicode/dead state")


def generate_sources(mapping: dict[str, Any]) -> dict[str, str]:
    """Generate ASCII C/DEF/RC sources; all non-ASCII characters use code points."""
    validate_mapping(mapping)
    reference = (ROOT / "windows/layout/reference/kbdus.c").read_text(encoding="utf-8")
    scan_start = reference.index("static ALLOC_SECTION_LDATA USHORT ausVK")
    scan_end = reference.index(
        "/***************************************************************************", scan_start
    )
    scans = reference[scan_start:scan_end]
    for key in mapping["keys"]:
        scans = re.sub(rf"\bT{key['scan_code']:02X}\b", f"0x{key['virtual_key']:02X}", scans)
    name_start = reference.index("static ALLOC_SECTION_LDATA VSC_LPWSTR aKeyNames[]")
    name_end = reference.index("static ALLOC_SECTION_LDATA KBDTABLES", name_start)
    names = reference[name_start:name_end]
    dead = {item["name"]: item for item in mapping["dead_keys"]}

    def wchar(value: str | None) -> str:
        if value is None:
            return "WCH_NONE"
        return "WCH_DEAD" if value in dead else f"0x{ord(value):04X}"

    # Native base-layout ASCII control semantics, separate from Bulgarian output levels.
    native_ctrl = {
        0xDB: "\x1b",
        0xDD: "\x1d",
        0xDC: "\x1c",
        0xE2: "\x1c",
        0x08: "\x7f",
        0x0D: "\n",
        0x1B: "\x1b",
        0x20: " ",
        0x03: "\x03",
    }
    native_shift_ctrl = {0x32: "\x00", 0x36: "\x1e", 0xBD: "\x1f"}
    rows = []
    for key in mapping["keys"]:
        vk = key["virtual_key"]
        levels = key["levels"]
        caps = (1 if levels[:2] != key["caps_levels"][:2] else 0) | (
            4 if levels[2:] != key["caps_levels"][2:] else 0
        )
        control = chr(vk & 31) if 65 <= vk <= 90 else native_ctrl.get(vk)
        shift_control = chr(vk & 31) if 65 <= vk <= 90 else native_shift_ctrl.get(vk)
        values = [levels[0], levels[1], control, shift_control, levels[2], levels[3]]
        rows.append(f"{{0x{vk:02X}, {caps}, {{{', '.join(wchar(v) for v in values)}}}}},")
        if any(value in dead for value in values if value is not None):
            accents = [
                wchar(dead[value]["spacing"]) if value in dead else "WCH_NONE" for value in values
            ]
            rows.append("{0xFF, 0, {" + ", ".join(accents) + "}},")
    for vk, base, shift in [
        (0x03, "\x03", "\x03"),
        (0x20, " ", " "),
        (0x0D, "\r", "\r"),
        (0x09, "\t", "\t"),
        (0x08, "\b", "\b"),
        (0x1B, "\x1b", "\x1b"),
        (0xE2, "\\", "|"),
        *[(0x60 + i, str(i), str(i)) for i in range(10)],
        (0x6A, "*", "*"),
        (0x6B, "+", "+"),
        (0x6D, "-", "-"),
        (0x6E, ".", "."),
        (0x6F, "/", "/"),
    ]:
        values = [
            base,
            shift,
            native_ctrl.get(vk),
            native_shift_ctrl.get(vk),
            base,
            shift,
        ]
        rows.append(f"{{0x{vk:02X}, 0, {{{', '.join(wchar(v) for v in values)}}}}},")
    rows.append("{0, 0, {0}},")
    compositions = []
    for accent in mapping["dead_keys"]:
        spacing = ord(accent["spacing"])
        for case in accent["cases"]:
            next_input, output = case["next"], case["output"]
            if case["pending"] is None and len(output) == 1:
                char = accent["spacing"] if next_input == accent["name"] else next_input
                if len(char) == 1:
                    compositions.append(
                        f"{{MAKELONG(0x{ord(char):04X}, 0x{spacing:04X}), 0x{ord(output):04X}, 0}},"
                    )
    c = (
        """/* Generated from reviewed project mapping.
 * Scan/navigation/key-name tables adapted from Microsoft kbdus.c:
 * Copyright (c) 1985-2000, Microsoft Corporation. MS-PL; see LICENSE.Microsoft.
 * Changes: Dvorak VK positions, Bulgarian levels, AltGr/Caps and compose tables.
 */
#include <windows.h>
#include <kbd.h>
#define ALLOC_SECTION_LDATA
"""
        + scans
        + """
static VK_TO_BIT bits[] = {{VK_SHIFT, KBDSHIFT}, {VK_CONTROL, KBDCTRL}, {VK_MENU, KBDALT}, {0,0}};
static MODIFIERS modifiers = {bits, 7, {0,1,2,3,SHFT_INVALID,SHFT_INVALID,4,5}};
static VK_TO_WCHARS6 characters[] = {
"""
        + "\n".join(rows)
        + """
};
static VK_TO_WCHAR_TABLE character_tables[] = {
    {(PVK_TO_WCHARS1)characters, 6, sizeof(characters[0])}, {NULL,0,0}
};
static DEADKEY dead_keys[] = {
"""
        + "\n".join(compositions)
        + """
{0,0,0}
};
"""
        + names
        + """
static KBDTABLES tables = {
    &modifiers, character_tables, dead_keys, aKeyNames, aKeyNamesExt, NULL,
    ausVK, sizeof(ausVK)/sizeof(ausVK[0]), aE0VscToVk, aE1VscToVk,
    MAKELONG(KLLF_ALTGR, KBD_VERSION), 0, 0, NULL, 0, 0
};
PKBDTABLES KbdLayerDescriptor(VOID) { return &tables; }
"""
    )
    return {
        "bgdv.c": c,
        "bgdv.def": "LIBRARY bgdv\nEXPORTS\n    KbdLayerDescriptor @1\n",
        "bgdv.rc": '#include <windows.h>\nLANGUAGE 2, 1\nSTRINGTABLE\nBEGIN\n    1 "'
        + DISPLAY_NAME
        + '"\nEND\n',
    }


def verify_toolchain(lock: dict[str, Any], compiler_root: Path, kits: Path) -> None:
    """Verify pinned compiler files, archives and extracted SDK/WDK contents offline."""
    if lock.get("schema_version") != 1 or lock.get("build_ready") is not True:
        raise ValueError("Native toolchain lock is pending or invalid")
    for item in lock["compiler_inputs"]:
        path = compiler_root / item["name"]
        if sha256(path) != item["sha256"]:
            raise ValueError(f"Compiler input mismatch: {item['name']}")
    header_root = compiler_root.parents[2] / "include"
    for item in lock["compiler_headers"]:
        if sha256(header_root / item["name"]) != item["sha256"]:
            raise ValueError(f"Compiler header mismatch: {item['name']}")
    for package in lock["acquired_inputs"]:
        archive_path = kits / (package["package"] + ".zip")
        if sha256(archive_path) != package["sha256"]:
            raise ValueError(f"Kit package mismatch: {package['package']}")
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                target = kits / package["package"] / info.filename
                if sha256(target) != hashlib.sha256(archive.read(info)).hexdigest():
                    raise ValueError(f"Extracted kit mismatch: {info.filename}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--compiler-root", type=Path)
    parser.add_argument("--msbuild", type=Path)
    parser.add_argument("--kits", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "windows/assets")
    args = parser.parse_args(argv)
    try:
        mapping = json.loads((ROOT / "windows/mapping.json").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "windows/toolchain.lock.json").read_text(encoding="utf-8"))
        generated = generate_sources(mapping)
        if args.generate_only:
            for name, content in generated.items():
                (ROOT / "windows/layout" / name).write_text(content, encoding="ascii")
            return 0
        if sys.platform != "win32" or not all((args.compiler_root, args.msbuild, args.kits)):
            raise ValueError("Build requires native Windows, --compiler-root, --msbuild and --kits")
        verify_toolchain(lock, args.compiler_root, args.kits)
        if sha256(args.msbuild) != lock["native_tools"][2]["sha256"]:
            raise ValueError("MSBuild input mismatch")
        build = ROOT / "build/windows-layout"
        build.mkdir(parents=True, exist_ok=True)
        for name, content in generated.items():
            (build / name).write_text(content, encoding="ascii")
        sdk = args.kits / "microsoft.windows.sdk.cpp/c"
        include = sdk / "Include/10.0.26100.0"
        # SDK headers plus the compiler's standard intrinsic headers; no ambient INCLUDE.
        vc_include = args.compiler_root.parents[2] / "include"
        include_paths = [include / "um", include / "shared", include / "ucrt", vc_include]
        include_args = " ".join(f'/I"{p}"' for p in include_paths)
        (build / "compile.rsp").write_text(
            f"/nologo /c /X /GS- /Zl /O2 /Brepro /D_AMD64_ {include_args} "
            f'/Fo"{build / "bgdv.obj"}" "{build / "bgdv.c"}"',
            encoding="utf-16",
        )
        # RC does not accept CL's UTF-16 response-file format. Pass Unicode argv
        # directly instead of converting paths through an ANSI response file or shell.
        subprocess.run(
            [
                str(sdk / "bin/10.0.26100.0/x64/rc.exe"),
                "/nologo",
                *[argument for path in include_paths for argument in ("/I", str(path))],
                "/fo",
                str(build / "bgdv.res"),
                str(build / "bgdv.rc"),
            ],
            check=True,
            timeout=120,
        )
        (build / "link.rsp").write_text(
            "/NOLOGO /DLL /NOENTRY /NODEFAULTLIB /MACHINE:X64 /Brepro /DYNAMICBASE /NXCOMPAT "
            f'/DEF:"{build / "bgdv.def"}" /OUT:"{build / "bgdv.dll"}" '
            f'"{build / "bgdv.obj"}" "{build / "bgdv.res"}"',
            encoding="utf-16",
        )
        subprocess.run(
            [
                str(args.msbuild),
                str(ROOT / "windows/layout/bgdv.vcxproj"),
                "/nologo",
                f"/p:CompilerRoot={args.compiler_root}",
                f"/p:BuildDirectory={build}",
            ],
            check=True,
            timeout=120,
        )
        args.output.mkdir(parents=True, exist_ok=True)
        digest = sha256(build / "bgdv.dll")
        name = f"bgdv_{digest}.dll"
        (args.output / name).write_bytes((build / "bgdv.dll").read_bytes())
        sources = [
            "windows/mapping.json",
            "linux/symbols-bg-dv",
            "tools/build_windows_layout.py",
            "windows/layout/bgdv.vcxproj",
            "windows/layout/reference/kbdus.c",
        ]
        revision = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        manifest = {
            "source_revision": revision,
            "logical_id": "bg-dvorak-phonetic",
            "target": {"build_family": 26200, "editions": ["Home", "Pro"], "architecture": "x64"},
            "mapping_sha256": sha256(ROOT / "windows/mapping.json"),
            "schema_version": 1,
            "architecture": "x64",
            "display_name": DISPLAY_NAME,
            "klid": "A0D00402",
            "layout_id": "0D00",
            "resource_id": 1,
            "dll": {"path": name, "sha256": digest},
            "sources": {path: sha256(ROOT / path) for path in sources},
            "toolchain_sha256": sha256(ROOT / "windows/toolchain.lock.json"),
            "toolchain": lock["observed"],
        }
        (args.output / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Native build failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
