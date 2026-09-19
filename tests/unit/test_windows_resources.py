"""Containment and restoration guarantees for Windows test scaffolding."""

import sys

import pytest

from tests.fixtures.windows_resources import windows_resources


def test_files_restore_and_cleanup():
    with windows_resources() as resources:
        root = resources.root
        original = resources.file("existing.dll")
        original.write_bytes(b"original")
        snapshot = resources.capture_file("existing.dll")
        original.write_bytes(b"changed")
        resources.restore_file("existing.dll", snapshot)
        assert original.read_bytes() == b"original"
        absent = resources.capture_file("new.dll")
        resources.file("new.dll").write_bytes(b"new")
        resources.restore_file("new.dll", absent)
        assert not resources.file("new.dll").exists()
    assert not root.exists()


@pytest.mark.parametrize("name", ["../outside", "/absolute", "C:\\Windows", "a/b", "a:b", "..", ""])
def test_rejects_paths_outside_fixture(name):
    with windows_resources() as resources, pytest.raises(ValueError):
        resources.file(name)


def test_rejects_linked_resources(tmp_path):
    outside = tmp_path / "outside"
    outside.write_bytes(b"untouched")
    with windows_resources() as resources:
        try:
            resources.file("linked").symlink_to(outside)
        except OSError as error:
            if sys.platform == "win32" and getattr(error, "winerror", None) == 1314:
                pytest.skip("Windows symlink privilege unavailable")
            raise
        with pytest.raises(ValueError):
            resources.capture_file("linked")
    assert outside.read_bytes() == b"untouched"


def test_fault_hook_and_exception_cleanup():
    events = []

    def fault(event):
        events.append(event)
        raise RuntimeError("injected")

    with pytest.raises(RuntimeError, match="injected"), windows_resources(fault=fault) as resources:
        root = resources.root
        resources.checkpoint("before-write")
    assert events == ["before-write"]
    assert not root.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="requires native Windows registry")
def test_native_registry_restore_and_cleanup():
    import winreg

    with windows_resources(registry=True) as resources:
        subkey = resources.registry_subkey
        with resources.open_registry() as key:
            winreg.SetValueEx(key, "empty", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "binary", 0, winreg.REG_BINARY, b"\x00\xff")
        snapshot = resources.capture_registry()
        with resources.open_registry() as key:
            winreg.DeleteValue(key, "empty")
            winreg.SetValueEx(key, "extra", 0, winreg.REG_DWORD, 17)
        resources.restore_registry(snapshot)
        assert resources.capture_registry() == snapshot
    with pytest.raises(FileNotFoundError):
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey)


def test_rejects_hardlinked_resources(tmp_path):
    outside = tmp_path / "outside"
    outside.write_bytes(b"untouched")
    with windows_resources() as resources:
        resources.file("linked").hardlink_to(outside)
        with pytest.raises(ValueError):
            resources.restore_file("linked", resources.capture_file("absent"))
    assert outside.read_bytes() == b"untouched"


def test_registry_request_never_falls_back_to_mock():
    if sys.platform == "win32":
        pytest.skip("non-Windows refusal")
    with pytest.raises(RuntimeError, match="require Windows"), windows_resources(registry=True):
        pytest.fail("must not yield a portable registry substitute")
