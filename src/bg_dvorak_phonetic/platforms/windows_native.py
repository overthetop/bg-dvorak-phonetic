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


def _validate_handle_identity(path: Path, root: Path) -> None:
    """Validate the final native handle path, type, and link count."""
    _require_windows()
    windows = cast(Any, ctypes)
    kernel32 = windows.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = ctypes.c_void_p

    class FileTime(ctypes.Structure):
        _fields_ = [("low", ctypes.c_ulong), ("high", ctypes.c_ulong)]

    class FileInformation(ctypes.Structure):
        _fields_ = [
            ("attributes", ctypes.c_ulong),
            ("created", FileTime),
            ("accessed", FileTime),
            ("written", FileTime),
            ("volume_serial", ctypes.c_ulong),
            ("size_high", ctypes.c_ulong),
            ("size_low", ctypes.c_ulong),
            ("links", ctypes.c_ulong),
            ("index_high", ctypes.c_ulong),
            ("index_low", ctypes.c_ulong),
        ]

    handle = kernel32.CreateFileW(
        str(path),
        0x80,
        0x1 | 0x2 | 0x4,
        None,
        3,
        0x00200000,
        None,
    )
    if handle == ctypes.c_void_p(-1).value:
        raise windows.WinError(windows.get_last_error())
    try:
        information = FileInformation()
        if not kernel32.GetFileInformationByHandle(handle, ctypes.byref(information)):
            raise windows.WinError(windows.get_last_error())
        if information.attributes & 0x400 or information.links != 1:
            raise ValueError("Handle identifies a reparse point or multiply linked file")
        size = kernel32.GetFinalPathNameByHandleW(handle, None, 0, 0)
        if not size:
            raise windows.WinError(windows.get_last_error())
        buffer = ctypes.create_unicode_buffer(size + 1)
        if not kernel32.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0):
            raise windows.WinError(windows.get_last_error())
        final = buffer.value
        if final.startswith("\\\\?\\"):
            final = final[4:]
        final_path = Path(os.path.normcase(final))
        expected = Path(os.path.normcase(path.resolve(strict=True)))
        resolved_root = Path(os.path.normcase(root.resolve(strict=True)))
        if final_path != expected or (
            final_path.parent != resolved_root and resolved_root not in final_path.parents
        ):
            raise ValueError("Final handle identity escapes the fixed root")
    finally:
        kernel32.CloseHandle(handle)


def _security_sddl(path: Path) -> str:
    _require_windows()
    windows = cast(Any, ctypes)
    advapi32 = windows.WinDLL("advapi32", use_last_error=True)
    kernel32 = windows.WinDLL("kernel32", use_last_error=True)
    descriptor = bytes.fromhex(_security_descriptor(path))
    buffer = ctypes.create_string_buffer(descriptor)
    output = ctypes.c_wchar_p()
    length = ctypes.c_ulong()
    flags = 0x00000001 | 0x00000004
    if not advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW(
        buffer, 1, flags, ctypes.byref(output), ctypes.byref(length)
    ):
        raise windows.WinError(windows.get_last_error())
    try:
        if output.value is None:
            raise RuntimeError("Security descriptor conversion returned no value")
        return output.value
    finally:
        kernel32.LocalFree(output)


def _validate_protected_sddl(sddl: str) -> None:
    owner = re.search(r"(?:^|O:)(BA|SY)(?=G:|D:|S:|$)", sddl)
    if owner is None:
        raise PermissionError("Protected state owner must be Administrators or SYSTEM")
    aces = re.findall(r"\(([^)]*)\)", sddl)
    if not aces:
        raise PermissionError("Protected state requires an explicit DACL")
    for ace in aces:
        fields = ace.split(";")
        if len(fields) < 6 or fields[0] != "A" or fields[-1] not in {"BA", "SY"}:
            raise PermissionError("Protected state DACL grants an unexpected principal")


def _set_protected_security(path: Path) -> None:
    _require_windows()
    windows = cast(Any, ctypes)
    advapi32 = windows.WinDLL("advapi32", use_last_error=True)
    kernel32 = windows.WinDLL("kernel32", use_last_error=True)
    descriptor = ctypes.c_void_p()
    size = ctypes.c_ulong()
    sddl = "O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)"
    if not advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        sddl, 1, ctypes.byref(descriptor), ctypes.byref(size)
    ):
        raise windows.WinError(windows.get_last_error())
    try:
        flags = 0x00000001 | 0x00000004
        if not advapi32.SetFileSecurityW(str(path), flags, descriptor):
            raise windows.WinError(windows.get_last_error())
    finally:
        kernel32.LocalFree(descriptor)


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
    if sys.platform == "win32" and path.exists():
        _validate_handle_identity(path, root)
    return path


def resolve_known_folder(folder_id: str) -> Path:
    """Resolve a Windows known folder without trusting environment variables."""
    _require_windows()
    import uuid

    windows = cast(Any, ctypes)
    shell32 = windows.WinDLL("shell32", use_last_error=True)
    ole32 = windows.WinDLL("ole32", use_last_error=True)
    raw = (ctypes.c_ubyte * 16).from_buffer_copy(uuid.UUID(folder_id).bytes_le)
    output = ctypes.c_wchar_p()
    result = shell32.SHGetKnownFolderPath(ctypes.byref(raw), 0, None, ctypes.byref(output))
    if result:
        raise OSError(f"SHGetKnownFolderPath failed: 0x{result & 0xFFFFFFFF:08x}")
    try:
        if output.value is None:
            raise RuntimeError("Known-folder API returned no path")
        return Path(output.value)
    finally:
        ole32.CoTaskMemFree(output)


def _registry_security_descriptor(key: Any) -> str:
    advapi32 = cast(Any, ctypes).WinDLL("advapi32", use_last_error=True)
    flags = 0x00000001 | 0x00000004
    needed = ctypes.c_ulong()
    status = advapi32.RegGetKeySecurity(int(key.handle), flags, None, ctypes.byref(needed))
    if status not in (0, 122):
        raise OSError(status, "RegGetKeySecurity size query failed")
    buffer = ctypes.create_string_buffer(needed.value)
    status = advapi32.RegGetKeySecurity(int(key.handle), flags, buffer, ctypes.byref(needed))
    if status:
        raise OSError(status, "RegGetKeySecurity failed")
    return buffer.raw[: needed.value].hex()


def _registry_native_value(value: RegistryValue) -> tuple[object, int]:
    winreg = cast(Any, importlib.import_module("winreg"))
    kinds = {
        "REG_SZ": winreg.REG_SZ,
        "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
        "REG_MULTI_SZ": winreg.REG_MULTI_SZ,
        "REG_BINARY": winreg.REG_BINARY,
        "REG_DWORD": winreg.REG_DWORD,
        "REG_QWORD": winreg.REG_QWORD,
    }
    content: object = value.value
    if value.value_type == "REG_BINARY":
        if not isinstance(content, str):
            raise ValueError("REG_BINARY snapshots use hexadecimal text")
        content = bytes.fromhex(content)
    elif value.value_type == "REG_MULTI_SZ":
        if not isinstance(content, tuple):
            raise ValueError("REG_MULTI_SZ snapshots use string tuples")
        content = list(content)
    return content, kinds[value.value_type]


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
            security_descriptor=_registry_security_descriptor(key),
        )


class WindowsResourceBackend:
    """Bounded file, registry, lock, and durable-record operations."""

    def __init__(self, system_root: Path, state_root: Path) -> None:
        _require_windows()
        self.system_root = system_root.absolute()
        self.state_root = state_root
        if not self.system_root.is_absolute() or not state_root.is_absolute():
            raise ValueError("Windows roots must be absolute")

    def prepare_state_root(self) -> None:
        self.state_root.mkdir(parents=True, exist_ok=True)
        _set_protected_security(self.state_root)
        self.validate_state_root()

    def validate_state_root(self) -> None:
        if not self.state_root.is_dir():
            raise FileNotFoundError("Protected state root is unavailable")
        _validate_protected_sddl(_security_sddl(self.state_root))

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
        with destination.open("rb+") as handle:
            os.fsync(handle.fileno())

    def verify_file(self, path: Path, expected: Observation) -> bool:
        return self.snapshot_file(path) == expected

    def registry_snapshot(self, subkey: str) -> RegistrySnapshot:
        winreg = cast(Any, importlib.import_module("winreg"))

        self._guard_subkey(subkey)
        return snapshot_registry(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY, subkey)

    def apply_registry(self, subkey: str, expected: RegistrySnapshot) -> None:
        winreg = cast(Any, importlib.import_module("winreg"))
        self._guard_subkey(subkey)
        access = winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY
        if not expected.exists:
            try:
                winreg.DeleteKeyEx(
                    winreg.HKEY_LOCAL_MACHINE,
                    subkey,
                    access=winreg.KEY_WOW64_64KEY,
                )
            except FileNotFoundError:
                return
            return
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, subkey, 0, access) as key:
            children, count, _ = winreg.QueryInfoKey(key)
            if children:
                raise ValueError("Refusing to replace a key with child keys")
            current = [winreg.EnumValue(key, index)[0] for index in range(count)]
            expected_names = {value.name.casefold() for value in expected.values}
            for name in current:
                if name.casefold() not in expected_names:
                    winreg.DeleteValue(key, name)
            for value in expected.values:
                content, kind = _registry_native_value(value)
                winreg.SetValueEx(key, value.name, 0, kind, content)
            winreg.FlushKey(key)
        if self.registry_snapshot(subkey).values != expected.values:
            raise RuntimeError("Registry postcondition verification failed")

    @staticmethod
    def _guard_subkey(subkey: str) -> None:
        normalized = re.sub(r"\\+", r"\\", subkey).rstrip("\\")
        prefix = _LAYOUT_ROOT + "\\"
        if not normalized.startswith(prefix) or normalized.count("\\") != prefix.count("\\"):
            raise ValueError("Registry key is outside the fixed layout root")

    @contextmanager
    def acquire_lock(self) -> Iterator[None]:
        msvcrt = cast(Any, importlib.import_module("msvcrt"))

        self.validate_state_root()
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
        self.validate_state_root()
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
        self.validate_state_root()
        return (self.state_root / name).read_bytes()

    def reconcile_file(self, path: Path, before: Observation, after: Observation) -> Reconciliation:
        result = Reconciliation.classify(self.snapshot_file(path), before, after)
        if result is Reconciliation.THIRD:
            raise ValueError("Refusing to overwrite a third state")
        return result
