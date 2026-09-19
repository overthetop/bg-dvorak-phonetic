"""Small injected native boundary; shared code owns workflow and recovery policy."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol

from bg_dvorak_phonetic.models import (
    ChangePlan,
    InstallationState,
    LayoutAssets,
    PlatformContext,
    RunResult,
)


class FileSystem(Protocol):
    """Replaceable filesystem mutation boundary for fault injection."""

    def read_bytes(self, path: Path) -> bytes: ...
    def replace(self, source: Path, target: Path) -> None: ...
    def unlink(self, path: Path) -> None: ...


class CommandRunner(Protocol):
    """Run a bounded argument-list native validator."""

    def __call__(self, args: list[str], *, timeout: int = 30) -> str: ...


class TransactionEngine(Protocol):
    def apply(
        self, context: PlatformContext, plan: ChangePlan, verify: Callable[[], None]
    ) -> None: ...


class RecoveryAccess(Protocol):
    """Native transport for read-only journal access and authorized restoration."""

    requires_authorization: bool

    def pending(self) -> tuple[str, ...]: ...
    def restore(self, run_id: str, *, dry_run: bool = False) -> None: ...


class PlatformAdapter(Protocol):
    """Nine operations; inspection and planning never mutate installation/state."""

    def recovery_access(self, context: PlatformContext, assets: LayoutAssets) -> RecoveryAccess: ...
    def probe(self, requested_scope: str | None) -> PlatformContext: ...
    def validate_assets(
        self, context: PlatformContext, assets: LayoutAssets
    ) -> tuple[str, ...]: ...
    def inspect(self, context: PlatformContext) -> InstallationState: ...
    def plan(self, state: InstallationState, assets: LayoutAssets) -> ChangePlan: ...
    def validate_staged(self, context: PlatformContext, staged: Path) -> tuple[str, ...]: ...
    def acquire_lock(self, context: PlatformContext) -> AbstractContextManager[None]: ...
    def apply_authorized(
        self, context: PlatformContext, plan: ChangePlan, engine: TransactionEngine
    ) -> None: ...
    def verify_installed(self, context: PlatformContext, assets: LayoutAssets) -> None: ...
    def activation_guidance(
        self, context: PlatformContext, result: RunResult
    ) -> tuple[str, ...]: ...
