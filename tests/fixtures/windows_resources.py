"""Test-only destinations; never accept a caller-supplied filesystem or registry root.

Registry fixtures use a unique HKCU Software leaf, never keyboard registration paths.
This is test scaffolding, not the production path/ACL security boundary.
"""

import os
import stat
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4


@dataclass(frozen=True)
class FileSnapshot:
    content: bytes | None
    mode: int | None


@dataclass(frozen=True)
class WindowsResources:
    root: Path
    registry_subkey: str | None
    fault: Callable[[str], None]

    def checkpoint(self, event: str) -> None:
        self.fault(event)

    def file(self, name: str) -> Path:
        """Only a single ordinary filename under the freshly allocated directory."""
        if (
            not name
            or name in {".", ".."}
            or any(character in name for character in "/\\:\x00")
            or name.endswith((".", " "))
            or name.split(".")[0].upper()
            in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10)),
            }
        ):
            raise ValueError("Expected a single fixture filename")
        path = self.root / name
        if os.path.lexists(path):
            info = path.lstat()
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or getattr(info, "st_file_attributes", 0) & 0x400
            ):
                raise ValueError("Fixture file must be regular, unlinked and non-reparse")
        return path

    def capture_file(self, name: str) -> FileSnapshot:
        path = self.file(name)
        if not path.exists():
            return FileSnapshot(None, None)
        return FileSnapshot(path.read_bytes(), stat.S_IMODE(path.stat().st_mode))

    def restore_file(self, name: str, snapshot: FileSnapshot) -> None:
        path = self.file(name)
        if snapshot.content is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(snapshot.content)
            if snapshot.mode is not None:
                path.chmod(snapshot.mode)

    def open_registry(self):
        import winreg

        if self.registry_subkey is None:
            raise RuntimeError("Registry fixture was not requested")
        return winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, self.registry_subkey, 0, winreg.KEY_ALL_ACCESS
        )

    def capture_registry(self) -> dict[str, tuple[object, int]]:
        import winreg

        with self.open_registry() as key:
            children, values, _ = winreg.QueryInfoKey(key)
            if children:
                raise ValueError("Snapshot fixture values only; child keys are unsupported")
            result = {}
            for index in range(values):
                name, value, kind = winreg.EnumValue(key, index)
                result[name] = (value, kind)
            return result

    def restore_registry(self, snapshot: dict[str, tuple[object, int]]) -> None:
        import winreg

        current = self.capture_registry()
        with self.open_registry() as key:
            for name in current:
                winreg.DeleteValue(key, name)
            for name, (value, kind) in snapshot.items():
                winreg.SetValueEx(key, name, 0, kind, value)


def _remove_registry_tree(parent, name: str) -> None:
    """Delete only descendants of the freshly allocated fixture key."""
    import winreg

    with winreg.OpenKey(parent, name, 0, winreg.KEY_ALL_ACCESS) as key:
        while winreg.QueryInfoKey(key)[0]:
            _remove_registry_tree(key, winreg.EnumKey(key, 0))
    winreg.DeleteKey(parent, name)


@contextmanager
def windows_resources(
    *, registry: bool = False, fault: Callable[[str], None] = lambda event: None
) -> Iterator[WindowsResources]:
    """Yield injectable destinations and clean up on success or injected failure.

    Files work on every host; registry=True requires real Windows and never falls back
    to a mock. No product command or live layout path is used.
    """
    if registry and sys.platform != "win32":
        raise RuntimeError("Native registry fixtures require Windows")
    with TemporaryDirectory(prefix="bg-dvorak-windows-test-") as directory:
        subkey = None
        if registry:
            import winreg

            subkey = "Software\\bg-dvorak-phonetic-test-" + str(uuid4())
            # Refuse even an improbable UUID collision rather than reuse existing data.
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey):
                    raise FileExistsError(subkey)
            except FileNotFoundError:
                pass
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, subkey):
                pass
        try:
            yield WindowsResources(Path(directory), subkey, fault)
        finally:
            if subkey is not None:
                import winreg

                _remove_registry_tree(winreg.HKEY_CURRENT_USER, subkey)
