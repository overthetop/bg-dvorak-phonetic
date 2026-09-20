"""Lazy Windows-native resource primitives with fixed-root containment."""

import ctypes
import hashlib
import importlib
import os
import re
import stat
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

from bg_dvorak_phonetic.models import RegistrySnapshot, RegistryValue
from bg_dvorak_phonetic.resources import Observation, Reconciliation

_LAYOUT_ROOT = r"SYSTEM\CurrentControlSet\Control\Keyboard Layouts"
_DEVICE_PREFIXES = ("\\\\?\\", "\\\\.\\", "\\??\\")
_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_TYPE_NAMES = {
    1: "REG_SZ",
    2: "REG_EXPAND_SZ",
    3: "REG_BINARY",
    4: "REG_DWORD",
    7: "REG_MULTI_SZ",
    11: "REG_QWORD",
}


def _require_windows() -> None:
    if sys.platform != "win32":
        raise RuntimeError("Windows native resources require Windows")


def _security_descriptor(path: Path) -> str:
    _require_windows()
    windows = cast(Any, ctypes)
    advapi32 = windows.WinDLL("advapi32", use_last_error=True)
    needed = ctypes.c_ulong()
    flags = 0x00000001 | 0x00000004
    advapi32.GetFileSecurityW(str(path), flags, None, 0, ctypes.byref(needed))
    if not needed.value:
        raise windows.WinError(windows.get_last_error())
    buffer = ctypes.create_string_buffer(needed.value)
    if not advapi32.GetFileSecurityW(str(path), flags, buffer, needed.value, ctypes.byref(needed)):
        raise windows.WinError(windows.get_last_error())
    return buffer.raw[: needed.value].hex()


def guard_file_path(path: Path, root: Path, *, allow_absent: bool = True) -> Path:
    """Return a contained ordinary Windows path or reject ambiguous identities."""
    if not path.is_absolute() or not root.is_absolute() or ".." in path.parts:
        raise ValueError("Path must be absolute and canonical")
    raw = str(path)
    if raw.startswith(_DEVICE_PREFIXES) or "\x00" in raw:
        raise ValueError("Device paths are forbidden")
    relative = path.relative_to(root)
    if not relative.parts:
        raise ValueError("Resource must be below its fixed root")
    for part in relative.parts:
        stem = part.rstrip(" .").split(".")[0].upper()
        if not part or part.endswith((" ", ".")) or ":" in part or stem in _RESERVED:
            raise ValueError("Ambiguous Windows path component")
    current = root
    for part in relative.parts:
        current /= part
        if not os.path.lexists(current):
            if allow_absent:
                continue
            raise FileNotFoundError(current)
        info = current.lstat()
        attributes = getattr(info, "st_file_attributes", 0)
        if stat.S_ISLNK(info.st_mode) or attributes & 0x400:
            raise ValueError("Reparse points and junctions are forbidden")
        if current == path and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
            raise ValueError("Resource must be a singly linked regular file")
    resolved_root = Path(os.path.normcase(root.resolve(strict=True)))
    resolved_parent = Path(os.path.normcase(path.parent.resolve(strict=True)))
    if resolved_parent != resolved_root and resolved_root not in resolved_parent.parents:
        raise ValueError("Resolved path escapes the fixed root")
    return path


def snapshot_registry(hive: Any, view: int, subkey: str) -> RegistrySnapshot:
    """Capture raw registry value types/content in canonical name order."""
    _require_windows()
    winreg = cast(Any, importlib.import_module("winreg"))

    try:
        key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ | view)
    except FileNotFoundError:
        return RegistrySnapshot(exists=False)
    with key:
        children, count, _ = winreg.QueryInfoKey(key)
        if children:
            raise ValueError("Registry snapshot contains unexpected child keys")
        values = []
        seen: set[str] = set()
        for index in range(count):
            name, value, kind = winreg.EnumValue(key, index)
            folded = name.casefold()
            if folded in seen:
                raise ValueError("Case-insensitive duplicate registry value")
            seen.add(folded)
            type_name = _TYPE_NAMES.get(kind)
            if type_name is None:
                raise ValueError(f"Unsupported registry value type: {kind}")
            if kind == winreg.REG_BINARY:
                value = bytes(value).hex()
            elif kind == winreg.REG_MULTI_SZ:
                value = tuple(value)
            values.append(RegistryValue(name, type_name, value))
        values.sort(key=lambda item: (item.name.casefold(), item.name))
        return RegistrySnapshot(
            exists=True,
            values=tuple(values),
            security_descriptor=None,
        )


class WindowsResourceBackend:
    """Bounded file, registry, lock, and durable-record operations."""

    def __init__(self, system_root: Path, state_root: Path) -> None:
        _require_windows()
        self.system_root = system_root.resolve(strict=True)
        self.state_root = state_root
        if not self.system_root.is_absolute() or not state_root.is_absolute():
            raise ValueError("Windows roots must be absolute")

    def snapshot_file(self, path: Path) -> Observation:
        guarded = guard_file_path(path, self.system_root)
        if not guarded.exists():
            return Observation(False, None, None)
        content = hashlib.sha256(guarded.read_bytes()).hexdigest()
        security = hashlib.sha256(bytes.fromhex(_security_descriptor(guarded))).hexdigest()
        return Observation(True, content, security)

    def stage_file(self, source: Path, destination: Path) -> Path:
        guard_file_path(destination, self.system_root)
        descriptor, name = tempfile.mkstemp(prefix=".bgdv-stage-", dir=destination.parent)
        staged = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(source.read_bytes())
                handle.flush()
                os.fsync(handle.fileno())
            return staged
        except BaseException:
            staged.unlink(missing_ok=True)
            raise

    def apply_file(self, staged: Path, destination: Path) -> None:
        guard_file_path(destination, self.system_root)
        os.replace(staged, destination)
        with destination.open("rb") as handle:
            os.fsync(handle.fileno())

    def verify_file(self, path: Path, expected: Observation) -> bool:
        return self.snapshot_file(path) == expected

    def registry_snapshot(self, subkey: str) -> RegistrySnapshot:
        winreg = cast(Any, importlib.import_module("winreg"))

        self._guard_subkey(subkey)
        return snapshot_registry(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY, subkey)

    @staticmethod
    def _guard_subkey(subkey: str) -> None:
        normalized = re.sub(r"\\+", r"\\", subkey).rstrip("\\")
        prefix = _LAYOUT_ROOT + "\\"
        if not normalized.startswith(prefix) or normalized.count("\\") != prefix.count("\\"):
            raise ValueError("Registry key is outside the fixed layout root")

    @contextmanager
    def acquire_lock(self) -> Iterator[None]:
        msvcrt = cast(Any, importlib.import_module("msvcrt"))

        if not self.state_root.exists():
            raise FileNotFoundError("Protected state root must be prepared before locking")
        path = self.state_root / "lock"
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0), 0o600)
        try:
            try:
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise BlockingIOError("Windows resource lock is held") from error
            yield
        finally:
            try:
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            finally:
                os.close(descriptor)

    def store_record(self, name: str, content: bytes) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError("Invalid record name")
        if not self.state_root.is_dir():
            raise FileNotFoundError("Protected state root is unavailable")
        descriptor, temporary_name = tempfile.mkstemp(prefix=".journal-", dir=self.state_root)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.state_root / name)
            directory = os.open(self.state_root, os.O_RDONLY)
            try:
                os.fsync(directory)
            except OSError as error:
                raise RuntimeError("Windows directory durability is unavailable") from error
            finally:
                os.close(directory)
        finally:
            temporary.unlink(missing_ok=True)

    def load_record(self, name: str) -> bytes:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError("Invalid record name")
        return (self.state_root / name).read_bytes()

    def reconcile_file(self, path: Path, before: Observation, after: Observation) -> Reconciliation:
        result = Reconciliation.classify(self.snapshot_file(path), before, after)
        if result is Reconciliation.THIRD:
            raise ValueError("Refusing to overwrite a third state")
        return result
