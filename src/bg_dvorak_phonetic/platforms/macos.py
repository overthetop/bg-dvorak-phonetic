"""User-local macOS bundle adapter; no preference edits or automatic session changes."""

import platform
import plistlib
import shutil
import tempfile
from contextlib import AbstractContextManager
from pathlib import Path

from bg_dvorak_phonetic.diagnostics import InstallerError
from bg_dvorak_phonetic.models import (
    ChangePlan,
    FileOperation,
    Health,
    InstallationState,
    LayoutAssets,
    PlatformContext,
    RunResult,
)
from bg_dvorak_phonetic.platforms.base import CommandRunner, RecoveryAccess, TransactionEngine
from bg_dvorak_phonetic.transaction import Transaction, scope_lock
from bg_dvorak_phonetic.workflow import (
    BUNDLE,
    LAYOUT_ID,
    digest,
    inventory,
    parse_keylayout,
    project_root,
    run_command,
    select_action,
)

IDENTITY = "org.sil.ukelele.keyboardlayout.bg-dvorak-phonetic"
INPUT_ID = f"{IDENTITY}.bg-dvorak-phonetic"


def bundle_identity(path: Path) -> tuple[str | None, str | None]:
    """Read remaining native identities; conflicting identities are never owned."""
    digest(path)
    try:
        data = plistlib.loads((path / "Contents/Info.plist").read_bytes())
        if not isinstance(data, dict):
            return (None, None)
        layout = data.get(f"KLInfo_{LAYOUT_ID}", {})
        input_id = layout.get("TISInputSourceID") if isinstance(layout, dict) else None
        return (data.get("CFBundleIdentifier"), input_id)
    except OSError, ValueError:
        return (None, None)


class MacOSAdapter:
    def __init__(
        self,
        *,
        root: Path | None = None,
        user_root: Path | None = None,
        system_root: Path | None = None,
        state_root: Path | None = None,
        testing: bool = False,
        runner: CommandRunner = run_command,
    ) -> None:
        if not testing and any(p is not None for p in (user_root, system_root, state_root)):
            raise ValueError("Destination overrides are test-only")
        self.root = root or project_root()
        self.user_root = user_root or Path.home() / "Library/Keyboard Layouts"
        self.system_root = system_root or Path("/Library/Keyboard Layouts")
        self.state_root = (
            state_root or Path.home() / "Library/Application Support/bg-dvorak-phonetic"
        )
        self.target = self.user_root / f"{LAYOUT_ID}.bundle"
        self.runner = runner
        self.context: PlatformContext | None = None
        self.duplicates: tuple[Path, ...] = ()
        self.staging: tempfile.TemporaryDirectory[str] | None = None

    def recovery_access(self, context: PlatformContext, assets: LayoutAssets) -> RecoveryAccess:
        from bg_dvorak_phonetic.transaction import LocalRecoveryAccess

        return LocalRecoveryAccess(context)

    def probe(self, requested_scope: str | None) -> PlatformContext:
        version = platform.mac_ver()[0]
        arch = platform.machine()
        if platform.system() != "Darwin" or not (
            (version.split(".")[0] == "15" and arch in ("x86_64", "arm64"))
            or (version.split(".")[0] == "26" and arch == "arm64")
        ):
            raise InstallerError("Supported macOS: 15 Intel/ARM64 or 26 ARM64", 2)
        if requested_scope not in (None, "user"):
            raise InstallerError("macOS supports user scope only", 2)
        self.context = PlatformContext(
            "macos", version, arch, "aqua", "user", self.root, (self.user_root,), self.state_root
        )
        return self.context

    def validate_assets(self, context: PlatformContext, assets: LayoutAssets) -> tuple[str, ...]:
        if not shutil.which("plutil"):
            raise InstallerError("Missing native plutil", 2, remedy="Restore macOS system tools.")
        return self.validate_staged(context, self.root / BUNDLE)

    def inspect(self, context: PlatformContext) -> InstallationState:
        for bundle in self.system_root.glob("*.bundle"):
            identity = bundle_identity(bundle)
            if identity[0] == IDENTITY or identity[1] == INPUT_ID:
                raise InstallerError(
                    "Conflicting system-wide layout",
                    4,
                    path=bundle,
                    remedy="Resolve the global copy manually before user installation.",
                )
        duplicates = []
        for bundle in self.user_root.glob("*.bundle"):
            if bundle == self.target:
                continue
            identity = bundle_identity(bundle)
            if identity == (IDENTITY, INPUT_ID):
                duplicates.append(bundle)
            elif identity[0] == IDENTITY or identity[1] == INPUT_ID:
                raise InstallerError(
                    "Conflicting user bundle identity",
                    4,
                    path=bundle,
                    remedy="Reconcile the conflicting copy before installation.",
                )
        self.duplicates = tuple(duplicates)
        current = digest(self.target)
        expected = digest(self.root / BUNDLE)
        if current is None:
            health = Health.ABSENT
        elif not self.target.is_dir():
            raise InstallerError("Canonical bundle path is not a directory", 4, path=self.target)
        elif not any(self.target.iterdir()):
            health = Health.REPAIRABLE
        else:
            identity = bundle_identity(self.target)
            if any(
                value is not None and value != expected_id
                for value, expected_id in zip(identity, (IDENTITY, INPUT_ID), strict=True)
            ):
                raise InstallerError(
                    "Conflicting bundle identifier blocks overwrite", 4, path=self.target
                )
            receipt = any(
                record.phase == "committed"
                and any(
                    op.destination == self.target and op.after_hash_or_absent is not None
                    for op in record.ordered_operations
                )
                for record in Transaction().records(context)
            )
            if identity == (None, None) and not receipt:
                raise InstallerError(
                    "Ambiguous populated bundle ownership",
                    4,
                    path=self.target,
                    remedy="Restore a matching identity or reconcile this bundle manually.",
                )
            health = Health.CURRENT if current == expected else Health.OUTDATED
            if any(
                not (self.target / path.relative_to(self.root / BUNDLE)).is_file()
                for path in (self.root / BUNDLE).rglob("*")
                if path.is_file()
            ):
                health = Health.REPAIRABLE
        if duplicates:
            health = Health.REPAIRABLE
        return InstallationState(
            health,
            ((str(self.target), current or ""),),
            (IDENTITY,) if current else (),
            (self.target, *self.duplicates),
        )

    def plan(self, state: InstallationState, assets: LayoutAssets) -> ChangePlan:
        assert self.context is not None
        if state.health == Health.UNSAFE:
            raise InstallerError("Unsafe bundle ownership", 4)
        source = self.root / BUNDLE
        operations = []
        if digest(self.target) != digest(source):
            operations.append(
                FileOperation(
                    "replace" if self.target.exists() else "create",
                    self.target,
                    digest(self.target),
                    digest(source),
                    source,
                )
            )
        for duplicate in self.duplicates:
            operations.append(FileOperation("remove-owned-duplicate", duplicate, digest(duplicate)))
        action = select_action(state.health)
        return ChangePlan(
            "macos",
            "user",
            action,
            tuple(operations),
            tuple((str(p), digest(p)) for p in (self.target, *self.duplicates)),
            assets.manifest,
        )

    def validate_staged(self, context: PlatformContext, staged: Path) -> tuple[str, ...]:
        if bundle_identity(staged) != (IDENTITY, INPUT_ID):
            raise InstallerError("Bundle native identifiers do not match", 2, path=staged)
        for plist in ("Info.plist", "version.plist"):
            self.runner(["plutil", "-lint", str(staged / "Contents" / plist)], timeout=30)
        layout = staged / f"Contents/Resources/{LAYOUT_ID}.keylayout"
        try:
            root = parse_keylayout(layout.read_bytes())
            if root.tag != "keyboard":
                raise ValueError("Not a keyboard document")
        except (OSError, ValueError) as exc:
            raise InstallerError("Invalid keylayout reference", 2, path=layout) from exc
        if digest(staged) != digest(self.root / BUNDLE):
            raise InstallerError("Bundle resources differ from supplied manifest", 1, path=staged)
        return ("native-plutil", "keylayout-structure", "complete-resource-manifest")

    def acquire_lock(self, context: PlatformContext) -> AbstractContextManager[None]:
        return scope_lock(context)

    def apply_authorized(
        self, context: PlatformContext, plan: ChangePlan, engine: TransactionEngine
    ) -> None:
        engine.apply(context, plan, lambda: self.verify_installed(context, inventory(self.root)))

    def verify_installed(self, context: PlatformContext, assets: LayoutAssets) -> None:
        self.validate_staged(context, self.target)
        if self.inspect(context).health != Health.CURRENT:
            raise InstallerError("Bundle verification failed", path=self.target)

    def activation_guidance(self, context: PlatformContext, result: RunResult) -> tuple[str, ...]:
        return (
            "System Settings > Keyboard > Text Input > Edit: add Bulgarian Dvorak phonetic.",
            "Selection and typing remain pending. If discovery needs refresh, "
            "save work and log out/in manually.",
        )
