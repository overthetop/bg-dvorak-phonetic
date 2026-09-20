"""Read-only layout asset validation using Python 3.14.7; never load a DLL."""

import argparse
import hashlib
import json
import re
import stat
import struct
import sys
from pathlib import Path
from typing import Any

DISPLAY_NAME = "Bulgarian (Dvorak phonetic)"
SOURCE_PATHS = {
    "windows/mapping.json",
    "linux/symbols-bg-dv",
    "tools/build_windows_layout.py",
    "windows/layout/bgdv.vcxproj",
    "windows/layout/reference/kbdus.c",
}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_asset_path(root: Path, name: str) -> Path:
    """Require a regular, non-reparse, single-link asset directly inside its root."""
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
    }
    if (
        not isinstance(name, str)
        or not name
        or name in {".", ".."}
        or any(char in name for char in "/\\:\x00")
        or name.endswith((".", " "))
        or name.split(".")[0].upper() in reserved
    ):
        raise ValueError("Invalid asset filename")
    path = root / name
    for ancestor in (path, *path.absolute().parents):
        info = ancestor.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Reparse/symlink asset path")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("Asset must be a regular single-link file")
    return path


def validate_pe(data: bytes) -> None:
    """Check x64 PE export ordinal/name and RT_STRING ID 1 without executing code."""
    if not 256 <= len(data) <= 16 * 1024 * 1024 or data[:2] != b"MZ":
        raise ValueError("Invalid PE size/signature")

    def unpack(fmt: str, offset: int) -> tuple[Any, ...]:
        size = struct.calcsize(fmt)
        if offset < 0 or offset + size > len(data):
            raise ValueError("Truncated PE structure")
        return struct.unpack_from(fmt, data, offset)

    pe = unpack("<I", 0x3C)[0]
    if data[pe : pe + 4] != b"PE\0\0":
        raise ValueError("Missing PE signature")
    machine, count, _, _, _, optional_size, flags = unpack("<HHIIIHH", pe + 4)
    optional = pe + 24
    if machine != 0x8664 or not flags & 0x2000 or not 1 <= count <= 96:
        raise ValueError("Expected x64 DLL")
    if optional_size < 240 or unpack("<H", optional)[0] != 0x20B:
        raise ValueError("Expected PE32+ optional header")
    if unpack("<I", optional + 108)[0] < 3:
        raise ValueError("Missing PE directories")
    sections = []
    for index in range(count):
        size, address, raw_size, raw = unpack("<IIII", optional + optional_size + index * 40 + 8)
        if raw + raw_size > len(data):
            raise ValueError("Invalid section bounds")
        sections.append((address, size, raw, raw_size))

    def offset(rva: int, size: int = 1) -> int:
        matches = [
            raw + rva - address
            for address, _, raw, raw_size in sections
            if address <= rva and rva + size <= address + raw_size
        ]
        if len(matches) != 1:
            raise ValueError("Unmapped or ambiguous PE address")
        return int(matches[0])

    export_rva, export_size = unpack("<II", optional + 112)
    export = offset(export_rva, 40)
    base, functions, names, function_rva, name_rva, ordinal_rva = unpack("<IIIIII", export + 16)
    if not 1 <= names <= functions <= 4096:
        raise ValueError("Invalid export counts")
    found = False
    for index in range(names):
        rva = unpack("<I", offset(name_rva + index * 4, 4))[0]
        start = offset(rva)
        end = data.find(b"\0", start, start + 256)
        if end < 0:
            raise ValueError("Unterminated export name")
        if data[start:end] == b"KbdLayerDescriptor":
            ordinal = unpack("<H", offset(ordinal_rva + index * 2, 2))[0]
            if ordinal >= functions or base + ordinal != 1:
                raise ValueError("Invalid descriptor export ordinal")
            target = unpack("<I", offset(function_rva + ordinal * 4, 4))[0]
            offset(target)
            if export_rva <= target < export_rva + export_size:
                raise ValueError("Forwarded descriptor export is forbidden")
            found = True
    if not found:
        raise ValueError("Missing KbdLayerDescriptor export")
    resource_rva, resource_size = unpack("<II", optional + 128)
    resource = offset(resource_rva, resource_size)

    def entry(relative: int, identifier: int | None) -> int:
        if not 0 <= relative <= resource_size - 16:
            raise ValueError("Resource directory outside bounds")
        named, ids = unpack("<HH", resource + relative + 12)
        if named + ids > 4096 or relative + 16 + 8 * (named + ids) > resource_size:
            raise ValueError("Invalid resource directory")
        entries = [
            unpack("<II", resource + relative + 16 + index * 8) for index in range(named + ids)
        ]
        candidates = [value for key, value in entries if key == identifier or identifier is None]
        if len(candidates) != 1:
            raise ValueError("Missing or ambiguous display resource")
        return int(candidates[0])

    block = entry(0, 6)
    if not block & 0x80000000:
        raise ValueError("Invalid string resource tree")
    language = entry(block & 0x7FFFFFFF, 1)
    if not language & 0x80000000:
        raise ValueError("Invalid string block")
    record = entry(language & 0x7FFFFFFF, None)
    if record & 0x80000000 or record + 16 > resource_size:
        raise ValueError("Invalid resource leaf")
    string_rva, size, _, _ = unpack("<IIII", resource + record)
    cursor = offset(string_rva, size)
    end = cursor + size
    values = []
    for _ in range(16):
        if cursor + 2 > end:
            raise ValueError("Truncated string block")
        length = unpack("<H", cursor)[0]
        cursor += 2
        if cursor + length * 2 > end:
            raise ValueError("Truncated display string")
        values.append(data[cursor : cursor + length * 2].decode("utf-16-le"))
        cursor += length * 2
    if values[1] != DISPLAY_NAME:
        raise ValueError("Display resource mismatch")


def validate_manifest(
    manifest: dict[str, Any], asset_root: Path, source_root: Path, lock_path: Path
) -> None:
    """Bind a native asset to its already trusted checkout and locked inputs.

    Hashes provide consistency, not publisher authentication. Callers must first trust
    the acquired checkout/release. No registration, library loading or downloads occur.
    """
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")
    revision = manifest.get("source_revision")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Invalid source revision provenance")
    expected = {
        "schema_version": 1,
        "architecture": "x64",
        "display_name": DISPLAY_NAME,
        "klid": "A0D00402",
        "layout_id": "0D00",
        "resource_id": 1,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("Manifest schema/identity/architecture mismatch")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("build_ready") is not True or manifest.get("toolchain_sha256") != digest(lock_path):
        raise ValueError("Untrusted or mismatched toolchain provenance")
    if manifest.get("toolchain") != lock.get("observed"):
        raise ValueError("Tool version provenance mismatch")
    sources = manifest.get("sources")
    if not isinstance(sources, dict) or set(sources) != SOURCE_PATHS:
        raise ValueError("Missing/unknown/case-duplicate source input")
    for name, expected_hash in sources.items():
        path = source_root / name
        validate_asset_path(path.parent, path.name)
        if digest(path) != expected_hash:
            raise ValueError(f"Source hash mismatch: {name}")
    names = [path.name.casefold() for path in asset_root.iterdir()]
    if len(names) != len(set(names)):
        raise ValueError("Case-insensitive duplicate asset names")
    artifact = manifest["dll"]
    expected_hash = artifact["sha256"]
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise ValueError("Invalid DLL hash")
    if artifact["path"] != f"bgdv_{expected_hash}.dll":
        raise ValueError("DLL must have its immutable content-addressed name")
    path = validate_asset_path(asset_root, artifact["path"])
    if digest(path) != expected_hash:
        raise ValueError("DLL hash mismatch")
    validate_pe(path.read_bytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--assets", type=Path, default=root / "windows/assets")
    args = parser.parse_args(argv)
    try:
        manifest_path = validate_asset_path(args.assets, "manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_manifest(manifest, args.assets, root, root / "windows/toolchain.lock.json")
        print(
            "Native asset metadata, hashes and locked provenance passed; typing proof is separate."
        )
        return 0
    except (OSError, ValueError, KeyError, TypeError, struct.error) as error:
        print(f"Asset validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
