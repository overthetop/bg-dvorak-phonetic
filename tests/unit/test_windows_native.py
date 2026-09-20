import sys

import pytest

from bg_dvorak_phonetic.platforms.windows_native import (
    WindowsResourceBackend,
    guard_file_path,
    snapshot_registry,
)
from tests.fixtures.windows_resources import windows_resources


@pytest.mark.parametrize("name", ["bad:name", "NUL.txt", "trailing.", "trailing "])
def test_guard_rejects_ambiguous_components(tmp_path, name):
    with pytest.raises(ValueError):
        guard_file_path(tmp_path / name, tmp_path)


def test_guard_rejects_escape_links_and_hardlinks(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    with pytest.raises(ValueError):
        guard_file_path(root / ".." / "outside", root)

    link = root / "link"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="Reparse"):
        guard_file_path(link, root)

    hardlink = root / "hardlink"
    hardlink.hardlink_to(outside)
    with pytest.raises(ValueError, match="singly linked"):
        guard_file_path(hardlink, root)


def test_guard_accepts_absent_contained_file(tmp_path):
    assert guard_file_path(tmp_path / "new.dll", tmp_path) == tmp_path / "new.dll"


def test_non_windows_native_backend_fails_lazily(tmp_path):
    if sys.platform == "win32":
        pytest.skip("portable lazy-import assertion")
    with pytest.raises(RuntimeError, match="require Windows"):
        WindowsResourceBackend(tmp_path, tmp_path)


@pytest.mark.skipif(sys.platform != "win32", reason="requires native Windows")
def test_native_registry_snapshot_preserves_types_and_order():
    import winreg

    with windows_resources(registry=True) as resources:
        with resources.open_registry() as key:
            winreg.SetValueEx(key, "z", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "Empty", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "binary", 0, winreg.REG_BINARY, b"\x00\xff")
        snapshot = snapshot_registry(winreg.HKEY_CURRENT_USER, 0, resources.registry_subkey)
        assert snapshot.exists
        assert [value.name for value in snapshot.values] == ["binary", "Empty", "z"]
        assert [(value.value_type, value.value) for value in snapshot.values] == [
            ("REG_BINARY", "00ff"),
            ("REG_SZ", ""),
            ("REG_DWORD", 0),
        ]


@pytest.mark.skipif(sys.platform != "win32", reason="requires native Windows")
def test_windows_backend_file_roundtrip_and_read_only_inspection():
    with windows_resources() as resources:
        state = resources.root / "state"
        state.mkdir()
        system = resources.root / "system"
        system.mkdir()
        source = resources.root / "source"
        source.write_bytes(b"layout")
        destination = system / "bgdv.dll"
        backend = WindowsResourceBackend(system, state)

        before_names = set(state.iterdir())
        assert not backend.snapshot_file(destination).exists
        assert set(state.iterdir()) == before_names

        staged = backend.stage_file(source, destination)
        backend.apply_file(staged, destination)
        observed = backend.snapshot_file(destination)
        assert observed.exists
        assert backend.verify_file(destination, observed)
