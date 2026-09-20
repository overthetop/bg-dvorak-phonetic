"""Resource mutation boundary shared by platform transaction engines."""

import hashlib
import importlib
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, NoReturn, cast


@dataclass(frozen=True)
class Observation:
    exists: bool
    fingerprint: str | None
    security_fingerprint: str | None


class Reconciliation(StrEnum):
    BEFORE = "before"
    AFTER = "after"
    THIRD = "third"

    @classmethod
    def classify(
        cls, current: Observation, before: Observation, after: Observation
    ) -> Reconciliation:
        if current == before:
            return cls.BEFORE
        if current == after:
            return cls.AFTER
        return cls.THIRD


class PosixResourceBackend:
    """Default native file/storage backend retained for Linux and macOS."""

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def replace(self, source: Path, target: Path) -> None:
        os.replace(source, target)

    def unlink(self, path: Path) -> None:
        path.unlink(missing_ok=True)

    def snapshot_file(self, path: Path) -> Observation:
        if not path.exists():
            return Observation(False, None, None)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        mode = path.stat().st_mode & 0o7777
        security = hashlib.sha256(str(mode).encode()).hexdigest()
        return Observation(True, digest, security)

    def stage_file(self, source: Path, work_root: Path) -> Path:
        work_root.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(prefix=".staged-", dir=work_root)
        staged = Path(name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(source.read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        return staged

    def apply_file(self, staged: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged, destination)

    def verify_file(self, path: Path, expected: Observation) -> bool:
        return self.snapshot_file(path) == expected

    def restore_file(self, path: Path, original: Observation) -> None:
        if not original.exists:
            path.unlink(missing_ok=True)
            return
        current = self.snapshot_file(path)
        if current.fingerprint != original.fingerprint:
            raise ValueError("Original bytes are required to restore an existing file")

    def reconcile_file(self, path: Path, before: Observation, after: Observation) -> Reconciliation:
        result = Reconciliation.classify(self.snapshot_file(path), before, after)
        if result is Reconciliation.THIRD:
            raise ValueError("Refusing to overwrite a third state")
        return result

    def snapshot_registry(self, resource: object) -> NoReturn:
        raise TypeError("POSIX backend does not support registry resources")

    @contextmanager
    def acquire_lock(self, state_root: Path) -> Iterator[None]:
        if os.name == "nt":
            raise RuntimeError("POSIX resource locking is unavailable on Windows")
        fcntl = cast(Any, importlib.import_module("fcntl"))
        path = state_root / ".resource.lock"
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def store_record(self, state_root: Path, name: str, content: bytes) -> None:
        if not name or "/" in name or name in {".", ".."}:
            raise ValueError("Invalid record name")
        path = state_root / name
        path.write_bytes(content)

    def load_record(self, state_root: Path, name: str) -> bytes:
        if not name or "/" in name or name in {".", ".."}:
            raise ValueError("Invalid record name")
        return (state_root / name).read_bytes()
