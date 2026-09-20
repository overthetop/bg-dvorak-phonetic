"""Scoped, durable, recoverable changes; multiple replacements are not globally atomic."""

import os
import shutil
import stat
import tempfile
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import replace
from pathlib import Path

from bg_dvorak_phonetic.diagnostics import InstallerError
from bg_dvorak_phonetic.models import (
    ChangePlan,
    FileOperation,
    PlatformContext,
    RecoveryRecord,
    validate_id,
)
from bg_dvorak_phonetic.platforms.base import FileSystem
from bg_dvorak_phonetic.resources import PosixResourceBackend
from bg_dvorak_phonetic.workflow import digest, safe_path


def sync_directory(path: Path) -> None:
    """Persist directory entries after rename/create operations."""
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def protected_root(context: PlatformContext, *, create: bool = False) -> None:
    """Validate scope ownership and private permissions; inspection never creates."""
    root = context.state_root
    safe_path(root)
    if not root.exists():
        if not create:
            return
        root.mkdir(parents=True, mode=0o700)
    info = root.stat()
    expected = 0 if context.scope == "system" else os.getuid()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != expected
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise InstallerError(
            "Unsafe recovery state ownership or permissions",
            4,
            path=root,
            remedy="Restore scope ownership and directory mode 0700.",
        )


@contextmanager
def scope_lock(context: PlatformContext) -> Iterator[None]:
    """Acquire a nonblocking native lock; the lock file remains stable across runs."""
    import fcntl

    protected_root(context, create=True)
    path = context.state_root / "lock"
    safe_path(path)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise InstallerError("Unsafe lock ownership or mode", 4, path=path)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InstallerError(
                "Another installer holds the scope lock",
                4,
                remedy="Wait for the other run to finish, then retry.",
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def bounded(context: PlatformContext, path: Path) -> None:
    """Only adapter-approved children may be mutated; no symlink traversal."""
    safe_path(path)
    if (
        not path.is_absolute()
        or ".." in path.parts
        or not any(path != root and path.is_relative_to(root) for root in context.destination_roots)
    ):
        raise InstallerError("Destination outside approved scope", 4, path=path)


def copy_object(source: Path, destination: Path) -> None:
    """Copy a validated object, retaining modes and ownership for restoration."""
    digest(source)
    if source.is_dir():
        shutil.copytree(source, destination, copy_function=shutil.copy2)
        pairs = [(source, destination)] + [
            (item, destination / item.relative_to(source)) for item in source.rglob("*")
        ]
    else:
        shutil.copy2(source, destination)
        pairs = [(source, destination)]
    for original, copied in pairs:
        info = original.stat()
        if os.geteuid() == 0:
            os.chown(copied, info.st_uid, info.st_gid)
        if copied.is_file():
            with copied.open("rb") as handle:
                os.fsync(handle.fileno())
    for _, copied in reversed(pairs):
        if copied.is_dir():
            sync_directory(copied)
    sync_directory(destination.parent)


def remove_object(path: Path) -> None:
    safe_path(path)
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


class LocalFileSystem(PosixResourceBackend):
    """Compatibility name for the default POSIX resource backend."""


class Transaction:
    """Apply bounded operations under a scope lock and retain recoverable originals."""

    def __init__(
        self,
        *,
        fault: Callable[[str, int], None] | None = None,
        lock_factory: Callable[[PlatformContext], AbstractContextManager[None]] = scope_lock,
        filesystem: FileSystem | None = None,
        resource_backend: FileSystem | None = None,
    ) -> None:
        if filesystem is not None and resource_backend is not None:
            raise ValueError("Choose one injected resource backend")
        self.fault = fault or (lambda stage, index: None)
        self.lock_factory = lock_factory
        self.filesystem = resource_backend or filesystem or LocalFileSystem()

    def _save(self, root: Path, record: RecoveryRecord) -> None:
        path = root / "journal.json"
        descriptor, name = tempfile.mkstemp(prefix=".journal-", dir=root)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(record.to_json())
                handle.flush()
                os.fsync(handle.fileno())
            self.filesystem.replace(temporary, path)
            sync_directory(root)
        finally:
            temporary.unlink(missing_ok=True)

    def _load(self, context: PlatformContext, run_id: str) -> RecoveryRecord:
        validate_id(run_id)
        protected_root(context)
        directory = context.state_root / run_id
        path = directory / "journal.json"
        safe_path(path)
        expected = 0 if context.scope == "system" else os.getuid()
        if directory.is_dir() and not path.exists():
            info = directory.stat()
            if info.st_uid != expected or stat.S_IMODE(info.st_mode) != 0o700:
                raise InstallerError("Unsafe unfinished preparation directory", 4, path=directory)
            # No backup or mutation can precede publication of the first journal.
            # Retain abandoned initial staging files, but do not block a fresh run.
            for item in directory.iterdir():
                safe_path(item)
                info = item.stat()
                if (
                    not item.name.startswith(".journal-")
                    or not item.is_file()
                    or info.st_uid != expected
                    or stat.S_IMODE(info.st_mode) != 0o600
                ):
                    raise InstallerError(
                        "Missing journal with unexplained retained files",
                        5,
                        path=directory,
                        remedy="Preserve these files and inspect manually.",
                    )
            return RecoveryRecord(scope=context.scope, run_id=run_id, phase="restored")
        for item, mode in ((directory, 0o700), (path, 0o600)):
            info = item.stat()
            if info.st_uid != expected or stat.S_IMODE(info.st_mode) != mode:
                raise InstallerError("Unsafe journal ownership or permissions", 4, path=item)
        try:
            record = RecoveryRecord.from_json(path.read_text(encoding="utf-8"))
        except (ValueError, KeyError, TypeError) as exc:
            raise InstallerError("Invalid recovery journal", 4, path=path) from exc
        if record.run_id != run_id or record.scope != context.scope:
            raise InstallerError("Recovery scope or ID mismatch", 4, path=path)
        for index, operation in enumerate(record.ordered_operations):
            bounded(context, operation.destination)
            if operation.backup_path != directory / f"original-{index}":
                raise InstallerError("Invalid backup location", 4, path=path)
            safe_path(operation.backup_path)
        return record

    def pending(self, context: PlatformContext) -> tuple[str, ...]:
        """Read-only discovery; inaccessible/invalid state never means clean state."""
        protected_root(context)
        if not context.state_root.exists():
            return ()
        result = []
        for item in sorted(context.state_root.iterdir()):
            if item.name == "lock":
                continue
            record = self._load(context, item.name)
            if record.phase not in ("committed", "restored"):
                result.append(record.run_id)
        return tuple(result)

    def records(self, context: PlatformContext) -> tuple[RecoveryRecord, ...]:
        """Read trusted receipts without creating state or treating denied access as empty."""
        protected_root(context)
        if not context.state_root.exists():
            return ()
        return tuple(
            self._load(context, p.name)
            for p in sorted(context.state_root.iterdir())
            if p.name != "lock"
        )

    def _check(self, context: PlatformContext, plan: ChangePlan) -> None:
        if plan.scope != context.scope or plan.platform != context.os_id:
            raise InstallerError("Plan does not match selected scope/platform", 4)
        for relative, expected in plan.source_hashes:
            source = context.project_root / relative
            if not source.is_relative_to(context.project_root) or ".." in source.parts:
                raise InstallerError("Invalid source path", 4, path=source)
            if digest(source) != expected:
                raise InstallerError("Source changed after authorization", 4, path=source)
        for raw_path, observed_expected in plan.observed_hashes:
            path = Path(raw_path)
            bounded(context, path)
            if digest(path) != observed_expected:
                raise InstallerError("Inspected snapshot changed before apply", 4, path=path)
        for operation in plan.operations:
            bounded(context, operation.destination)
            if context.scope == "user" and operation.destination.exists():
                objects = [operation.destination]
                if operation.destination.is_dir():
                    objects.extend(operation.destination.rglob("*"))
                if any(path.stat().st_uid != os.getuid() for path in objects):
                    raise InstallerError(
                        "User-scope originals have another owner",
                        4,
                        path=operation.destination,
                        remedy="Resolve ownership before installing; originals were retained.",
                    )
            if digest(operation.destination) != operation.before_hash_or_absent:
                raise InstallerError(
                    "Destination changed after inspection",
                    4,
                    path=operation.destination,
                    remedy="Inspect again before retrying.",
                )
            if operation.staged_path is not None:
                if digest(operation.staged_path) != operation.after_hash_or_absent:
                    raise InstallerError("Staged content changed", 4, path=operation.staged_path)
            elif operation.after_hash_or_absent is not None:
                raise InstallerError("Missing staged content", 4)

    def apply(self, context: PlatformContext, plan: ChangePlan, verify: Callable[[], None]) -> None:
        """Lock, recheck, back up, write and verify; any failure invokes restoration."""
        if not plan.operations:
            return
        with self.lock_factory(context):
            self._check(context, plan)
            if self.pending(context):
                raise InstallerError(
                    "Unfinished transaction requires recovery",
                    5,
                    path=context.state_root,
                    remedy="Recover the reported run first.",
                )
            directory = context.state_root / plan.run_id
            directory.mkdir(mode=0o700)
            operations = tuple(
                replace(op, backup_path=directory / f"original-{i}")
                for i, op in enumerate(plan.operations)
            )
            record = RecoveryRecord(
                scope=context.scope, run_id=plan.run_id, ordered_operations=operations
            )
            self._save(directory, record)
            try:
                for index, operation in enumerate(operations):
                    self.fault("before-backup", index)
                    if operation.before_hash_or_absent is not None:
                        assert operation.backup_path is not None
                        copy_object(operation.destination, operation.backup_path)
                        if digest(operation.backup_path) != operation.before_hash_or_absent:
                            raise InstallerError(
                                "Source changed while backing up", 4, path=operation.destination
                            )
                    self.fault("after-backup", index)
                record = replace(
                    record,
                    retained_originals=tuple(str(op.backup_path) for op in operations),
                    phase="applying",
                )
                self._save(directory, record)
                for index, operation in enumerate(operations):
                    # Intent is durable before mutation, so a crash can inspect both hashes.
                    record = replace(record, completed_steps=(*record.completed_steps, index))
                    self._save(directory, record)
                    self.fault("before-apply", index)
                    self._replace(context, operation, plan.run_id, index)
                    self.fault("after-apply", index)
                verify()
                self._save(directory, replace(record, phase="verified"))
                self.fault("before-commit", len(operations))
                self._save(directory, replace(record, phase="committed"))
            except BaseException:
                try:
                    self._restore_locked(context, record)
                except BaseException as recovery_error:
                    raise self._recovery_required(context, record) from recovery_error
                raise

    def _replace(
        self, context: PlatformContext, operation: FileOperation, run_id: str, index: int
    ) -> None:
        target = operation.destination
        bounded(context, target)
        if digest(target) != operation.before_hash_or_absent:
            raise InstallerError("Target changed before replacement", 4, path=target)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Staging and displaced-directory names are deterministic journal-derived siblings.
        staged = target.parent / f".bg-dvorak-{run_id}-{index}-stage"
        displaced = target.parent / f".bg-dvorak-{run_id}-{index}-old"
        for sibling in (staged, displaced):
            safe_path(sibling)
            if sibling.exists():
                raise InstallerError("Unexpected transaction staging path", 4, path=sibling)
        if operation.staged_path is not None:
            copy_object(operation.staged_path, staged)
            if digest(staged) != operation.after_hash_or_absent:
                raise InstallerError("Staging hash mismatch", 4, path=staged)
            if target.exists() and target.is_file():
                info = target.stat()
                os.chmod(staged, stat.S_IMODE(info.st_mode))
                if os.geteuid() == 0:
                    os.chown(staged, info.st_uid, info.st_gid)
        if target.is_dir():
            self.filesystem.replace(target, displaced)
            sync_directory(target.parent)
            self.fault("after-displace", index)
        if operation.staged_path is None:
            remove_object(target)
        else:
            self.filesystem.replace(staged, target)
        sync_directory(target.parent)
        if digest(target) != operation.after_hash_or_absent:
            raise InstallerError("Post-write hash mismatch", path=target)
        remove_object(displaced)

    def restore(self, context: PlatformContext, run_id: str, *, dry_run: bool = False) -> None:
        """Restore a known journal, refusing changed destinations and invalid backup paths."""
        record = self._load(context, run_id)
        self._validate_restore(context, record)
        if dry_run or record.phase == "restored":
            return
        with self.lock_factory(context):
            record = self._load(context, run_id)
            try:
                self._restore_locked(context, record)
            except BaseException as recovery_error:
                raise self._recovery_required(context, record) from recovery_error

    def _recovery_required(
        self, context: PlatformContext, record: RecoveryRecord
    ) -> InstallerError:
        directory = context.state_root / record.run_id
        message = "Restoration could not safely finish"
        try:
            self._save(directory, replace(record, phase="recovery_required"))
        except (OSError, KeyboardInterrupt) as journal_error:
            message += f"; journal update also failed: {journal_error}"
        return InstallerError(
            message, 5, path=directory, remedy=f"Recover run {record.run_id}; retain all originals."
        )

    def _validate_restore(self, context: PlatformContext, record: RecoveryRecord) -> None:
        for index in record.completed_steps:
            operation = record.ordered_operations[index]
            bounded(context, operation.destination)
            current = digest(operation.destination)
            displaced = operation.destination.parent / f".bg-dvorak-{record.run_id}-{index}-old"
            valid = current in (operation.before_hash_or_absent, operation.after_hash_or_absent)
            if current is None and digest(displaced) == operation.before_hash_or_absent:
                valid = True
            restored = operation.destination.parent / f".bg-dvorak-{record.run_id}-{index}-restore"
            rollback = operation.destination.parent / f".bg-dvorak-{record.run_id}-{index}-rollback"
            if (
                record.phase in ("rolling_back", "recovery_required")
                and current is None
                and digest(rollback) == operation.after_hash_or_absent
            ):
                valid = True
            if (
                record.phase in ("rolling_back", "recovery_required")
                and current is None
                and digest(restored) == operation.before_hash_or_absent
            ):
                valid = True
            if not valid:
                raise InstallerError(
                    "External edit prevents restoration",
                    5,
                    path=operation.destination,
                    remedy="Preserve edits and retained originals; reconcile manually.",
                )
            if operation.before_hash_or_absent is not None:
                assert operation.backup_path is not None
                if digest(operation.backup_path) != operation.before_hash_or_absent:
                    raise InstallerError(
                        "Original backup is missing or changed", 5, path=operation.backup_path
                    )

    def _restore_locked(self, context: PlatformContext, record: RecoveryRecord) -> None:
        directory = context.state_root / record.run_id
        self._validate_restore(context, record)
        self._save(directory, replace(record, phase="rolling_back"))
        for index in reversed(record.completed_steps):
            operation = record.ordered_operations[index]
            self.fault("before-restore", index)
            target = operation.destination
            if digest(target) != operation.before_hash_or_absent:
                restored = target.parent / f".bg-dvorak-{record.run_id}-{index}-restore"
                safe_path(restored)
                if restored.exists():
                    if digest(restored) != operation.before_hash_or_absent:
                        raise InstallerError("Changed restoration staging object", 5, path=restored)
                    remove_object(restored)
                if operation.before_hash_or_absent is not None:
                    assert operation.backup_path is not None
                    copy_object(operation.backup_path, restored)
                rollback = target.parent / f".bg-dvorak-{record.run_id}-{index}-rollback"
                safe_path(rollback)
                if target.exists():
                    if rollback.exists():
                        raise InstallerError("Unexpected rollback displacement", 5, path=rollback)
                    self.filesystem.replace(target, rollback)
                    sync_directory(target.parent)
                self.fault("after-remove-restore", index)
                if operation.before_hash_or_absent is not None:
                    self.filesystem.replace(restored, target)
                sync_directory(target.parent)
            for suffix, expected in (
                ("stage", operation.after_hash_or_absent),
                ("old", operation.before_hash_or_absent),
                ("rollback", operation.after_hash_or_absent),
            ):
                sibling = target.parent / f".bg-dvorak-{record.run_id}-{index}-{suffix}"
                if sibling.exists():
                    if digest(sibling) != expected:
                        raise InstallerError("Changed transaction staging object", 5, path=sibling)
                    remove_object(sibling)
            if digest(target) != operation.before_hash_or_absent:
                raise InstallerError("Restoration verification failed", 5, path=target)
        self._save(directory, replace(record, phase="restored"))


class LocalRecoveryAccess:
    """Unprivileged scoped journal operations, used by user-scope adapters."""

    requires_authorization = False

    def __init__(self, context: PlatformContext) -> None:
        self.context = context
        self.engine = Transaction()

    def pending(self) -> tuple[str, ...]:
        return self.engine.pending(self.context)

    def restore(self, run_id: str, *, dry_run: bool = False) -> None:
        self.engine.restore(self.context, run_id, dry_run=dry_run)
