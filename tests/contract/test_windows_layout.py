"""Independent mapping oracle and fail-closed native build contracts."""

import copy
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load_tool("build_windows_layout")
validator = load_tool("validate_windows_layout")
generate_sources = builder.generate_sources
validate_mapping = builder.validate_mapping
verify_toolchain = builder.verify_toolchain
validate_asset_path = validator.validate_asset_path
validate_manifest = validator.validate_manifest
validate_pe = validator.validate_pe


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_all_mapping_outputs_match_independent_oracle():
    mapping = read("windows/mapping.json")
    expected = read("tests/fixtures/windows_mapping_expected.json")
    validate_mapping(mapping)
    assert len(mapping["keys"]) == 47
    assert {k["position"]: k["levels"] for k in mapping["keys"]} == {
        k["position"]: k["levels"] for k in expected["keys"]
    }
    assert mapping["dead_keys"] == expected["dead_keys"]
    for key in mapping["keys"]:
        oracle = next(k for k in expected["keys"] if k["position"] == key["position"])
        assert key["caps_levels"] == oracle["caps_levels"]
        assert key["scan_code"] == oracle["scan_code"]
        assert key["virtual_key"] == oracle["virtual_key"]
    for shortcut in expected["shortcuts"]:
        key = next(k for k in mapping["keys"] if k["position"] == shortcut["position"])
        assert key["virtual_key"] == ord(shortcut["control_vk"])


def test_generation_is_deterministic_and_has_required_export():
    mapping = read("windows/mapping.json")
    first = generate_sources(mapping)
    assert first == generate_sources(copy.deepcopy(mapping))
    assert set(first) == {"bgdv.c", "bgdv.def", "bgdv.rc"}
    assert "KbdLayerDescriptor" in first["bgdv.c"]
    assert "KbdLayerDescriptor @1" in first["bgdv.def"]
    assert "Bulgarian (Dvorak phonetic)" in first["bgdv.rc"]
    assert "CreateProcess" not in first["bgdv.c"]


@pytest.mark.parametrize("mutation", ["duplicate_scan", "duplicate_vk", "missing_key", "bad_level"])
def test_invalid_mapping_is_rejected(mutation):
    mapping = read("windows/mapping.json")
    if mutation == "duplicate_scan":
        mapping["keys"][1]["scan_code"] = mapping["keys"][0]["scan_code"]
    elif mutation == "duplicate_vk":
        mapping["keys"][1]["virtual_key"] = mapping["keys"][0]["virtual_key"]
    elif mutation == "missing_key":
        mapping["keys"].pop()
    else:
        mapping["keys"][0]["levels"] = ["invalid"]
    with pytest.raises(ValueError):
        validate_mapping(mapping)


def test_missing_or_pending_toolchain_fails_without_provisioning(tmp_path):
    lock = read("windows/toolchain.lock.json")
    with pytest.raises((ValueError, FileNotFoundError)):
        verify_toolchain(lock, tmp_path, tmp_path)
    lock["build_ready"] = False
    with pytest.raises(ValueError, match="lock"):
        verify_toolchain(lock, tmp_path, tmp_path)


@pytest.mark.parametrize(
    "name",
    ["../evil.dll", "C:/evil.dll", "a:b.dll", "CON.dll", "a\\b.dll", "/a.dll", "x.dll.", "x.dll "],
)
def test_asset_paths_cannot_escape_root(tmp_path, name):
    with pytest.raises(ValueError):
        validate_asset_path(tmp_path, name)


def test_asset_symlink_is_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.write_bytes(b"not a DLL")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "linked.dll").symlink_to(outside)
    with pytest.raises(ValueError):
        validate_asset_path(assets, "linked.dll")


@pytest.mark.parametrize("data", [b"", b"MZ", b"MZ" + bytes(510)])
def test_malformed_pe_is_rejected_without_loading(data):
    with pytest.raises(ValueError):
        validate_pe(data)


def minimal_pe():
    """Hand-constructed PE fixture, independent of the production generator/compiler."""
    data = bytearray(2048)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 0x84, 0x8664, 1, 0, 0, 0, 240, 0x2022)
    struct.pack_into("<H", data, 0x98, 0x20B)
    struct.pack_into("<I", data, 0x98 + 108, 16)
    struct.pack_into("<II", data, 0x98 + 112, 0x1000, 0x100)
    struct.pack_into("<II", data, 0x98 + 128, 0x1200, 0x200)
    section = 0x98 + 240
    data[section : section + 8] = b".rdata\0\0"
    struct.pack_into("<IIII", data, section + 8, 0x600, 0x1000, 0x600, 0x200)
    # Export name and ordinal 1, one function/name.
    struct.pack_into("<IIIIII", data, 0x210, 1, 1, 1, 0x1040, 0x1044, 0x1048)
    struct.pack_into("<I", data, 0x240, 0x1500)
    struct.pack_into("<I", data, 0x244, 0x1060)
    struct.pack_into("<H", data, 0x248, 0)
    data[0x260:0x273] = b"KbdLayerDescriptor\0"
    # RT_STRING(6), block 1, language 0x402, string ID 1.
    for offset, ident, child in [
        (0x400, 6, 0x80000020),
        (0x420, 1, 0x80000040),
        (0x440, 0x402, 0x60),
    ]:
        struct.pack_into("<H", data, offset + 14, 1)
        struct.pack_into("<II", data, offset + 16, ident, child)
    title = "Bulgarian (Dvorak phonetic)".encode("utf-16-le")
    strings = b"\0\0" + struct.pack("<H", len(title) // 2) + title + bytes(28)
    struct.pack_into("<IIII", data, 0x460, 0x1280, len(strings), 1200, 0)
    data[0x480 : 0x480 + len(strings)] = strings
    return bytes(data)


def test_pe_export_architecture_and_display_resource():
    validate_pe(minimal_pe())
    for offset in [0x84, 0x260, 0x484]:
        data = bytearray(minimal_pe())
        data[offset] ^= 1
        with pytest.raises(ValueError):
            validate_pe(bytes(data))


def asset_fixture(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    data = minimal_pe()
    digest = hashlib.sha256(data).hexdigest()
    name = "bgdv_" + digest + ".dll"
    (assets / name).write_bytes(data)
    source = tmp_path / "source"
    source.mkdir()
    for source_name in validator.SOURCE_PATHS:
        path = source / source_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"mapping")
    lock = {"build_ready": True, "observed": {"compiler_version": "fixture"}}
    (source / "toolchain.lock.json").write_text(json.dumps(lock))
    manifest = {
        "source_revision": "1" * 40,
        "schema_version": 1,
        "architecture": "x64",
        "display_name": "Bulgarian (Dvorak phonetic)",
        "klid": "A0D00402",
        "layout_id": "0D00",
        "resource_id": 1,
        "dll": {"path": name, "sha256": digest},
        "sources": {
            name: hashlib.sha256(b"mapping").hexdigest() for name in validator.SOURCE_PATHS
        },
        "toolchain_sha256": hashlib.sha256(
            (source / "toolchain.lock.json").read_bytes()
        ).hexdigest(),
        "toolchain": lock["observed"],
    }
    return assets, source, manifest


def test_manifest_accepts_only_matching_trusted_checkout(tmp_path):
    assets, source, manifest = asset_fixture(tmp_path)
    validate_manifest(manifest, assets, source, source / "toolchain.lock.json")
    (source / "windows/mapping.json").write_bytes(b"changed")
    with pytest.raises(ValueError):
        validate_manifest(manifest, assets, source, source / "toolchain.lock.json")


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", 99),
        ("architecture", "arm64"),
        ("klid", "00000402"),
        ("toolchain_sha256", "0" * 64),
        ("toolchain", {}),
        ("sources", {"A": "0" * 64, "a": "0" * 64}),
    ],
)
def test_manifest_rejects_schema_architecture_and_provenance(tmp_path, field, value):
    assets, source, manifest = asset_fixture(tmp_path)
    manifest[field] = value
    with pytest.raises(ValueError):
        validate_manifest(manifest, assets, source, source / "toolchain.lock.json")


def test_changed_tool_input_is_rejected(tmp_path):
    (tmp_path / "cl.exe").write_bytes(b"changed")
    lock = {
        "schema_version": 1,
        "build_ready": True,
        "compiler_inputs": [{"name": "cl.exe", "sha256": "0" * 64}],
    }
    with pytest.raises(ValueError, match="Compiler input mismatch"):
        verify_toolchain(lock, tmp_path, tmp_path)


def test_corrupted_dll_is_rejected_before_pe_parse(tmp_path):
    assets, source, manifest = asset_fixture(tmp_path)
    (assets / manifest["dll"]["path"]).write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="DLL hash mismatch"):
        validate_manifest(manifest, assets, source, source / "toolchain.lock.json")


def test_case_duplicate_assets_are_rejected(tmp_path):
    assets, source, manifest = asset_fixture(tmp_path)
    name = manifest["dll"]["path"]
    upper = assets / name.upper()
    if upper.exists():
        pytest.skip("case-insensitive filesystem prevents distinct aliases")
    upper.write_bytes((assets / name).read_bytes())
    with pytest.raises(ValueError, match="Case-insensitive duplicate"):
        validate_manifest(manifest, assets, source, source / "toolchain.lock.json")


def test_generation_and_validation_never_execute_native_code(tmp_path, monkeypatch):
    import ctypes
    import subprocess
    import urllib.request

    def forbidden(*args, **kwargs):
        pytest.fail("Read-only generation/metadata validation executed or downloaded code")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(ctypes, "CDLL", forbidden)
    generate_sources(read("windows/mapping.json"))
    assets, source, manifest = asset_fixture(tmp_path)
    validate_manifest(manifest, assets, source, source / "toolchain.lock.json")


def test_generated_control_characters_preserve_native_base_layout():
    import re

    generated = generate_sources(read("windows/mapping.json"))["bgdv.c"]
    rows = {
        int(vk, 16): values.split(", ")
        for vk, values in re.findall(r"\{0x([0-9A-F]{2}), \d+, \{([^}]+)\}\}", generated)
        if vk != "FF"
    }
    # Native kbdus.c: Enter/Backspace and punctuation have distinct Ctrl outputs.
    for vk, control, shifted_control in [
        (0x0D, "0x000A", "WCH_NONE"),
        (0x08, "0x007F", "WCH_NONE"),
        (0xDB, "0x001B", "WCH_NONE"),
        (0xDD, "0x001D", "WCH_NONE"),
        (0xDC, "0x001C", "WCH_NONE"),
        (0xE2, "0x001C", "WCH_NONE"),
        (0x32, "WCH_NONE", "0x0000"),
        (0x36, "WCH_NONE", "0x001E"),
        (0xBD, "WCH_NONE", "0x001F"),
        (0x09, "WCH_NONE", "WCH_NONE"),
    ]:
        assert rows[vk][2:4] == [control, shifted_control]
