"""Read-only prerequisites and source inventory shared by platform workflows."""

import hashlib
import importlib.metadata
import json
import plistlib
import re
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bg_dvorak_phonetic.diagnostics import Diagnostics
    from bg_dvorak_phonetic.models import PlatformContext, RunResult
    from bg_dvorak_phonetic.platforms.base import PlatformAdapter

from bg_dvorak_phonetic.diagnostics import InstallerError
from bg_dvorak_phonetic.models import Action, Health, LayoutAssets

LAYOUT_ID = "bg-dvorak-phonetic"
BUNDLE = f"mac-os/{LAYOUT_ID}.bundle"
ASSET_PATHS = (
    "linux/symbols-bg-dv",
    "linux/evdev.xml",
    f"{BUNDLE}/Contents/Info.plist",
    f"{BUNDLE}/Contents/version.plist",
    f"{BUNDLE}/Contents/Resources/{LAYOUT_ID}.keylayout",
    f"{BUNDLE}/Contents/Resources/{LAYOUT_ID}.icns",
    f"{BUNDLE}/Contents/Resources/en.lproj/InfoPlist.strings",
)
PREPARE = "Prepare with uv python install 3.14.7, then uv sync --locked --dev in the checkout."


def project_root() -> Path:
    """Resolve checkout distribution from the installed source, independently of cwd."""
    return Path(__file__).resolve().parents[2]


def safe_path(path: Path) -> None:
    """Reject any symlink component, including dangling symlinks."""
    for part in (path, *path.parents):
        if part.is_symlink():
            raise InstallerError(
                "Unsafe symlink", 4, path=part, remedy="Restore a regular owned path."
            )


def digest(path: Path) -> str | None:
    """Hash regular files or complete trees; reject symlinks and special files."""
    safe_path(path)
    if not path.exists():
        return None
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if not path.is_dir():
        raise InstallerError("Unsupported filesystem object", 4, path=path)
    items = []
    for item in sorted(path.rglob("*")):
        safe_path(item)
        if not item.is_file() and not item.is_dir():
            raise InstallerError("Unsupported bundle object", 4, path=item)
        items.append(
            (item.relative_to(path).as_posix(), digest(item) if item.is_file() else "directory")
        )
    return hashlib.sha256(json.dumps(items).encode("utf-8")).hexdigest()


def inventory(root: Path) -> LayoutAssets:
    """Validate the full authoritative source inventory before inspecting destinations."""
    manifest = []
    try:
        for relative in ASSET_PATHS:
            path = root / relative
            safe_path(path)
            if not path.is_file():
                raise ValueError(f"Missing asset: {relative}")
            manifest.append((relative, hashlib.sha256(path.read_bytes()).hexdigest()))
        variant = ET.fromstring((root / "linux/evdev.xml").read_bytes())
        if variant.findtext("configItem/name") != LAYOUT_ID:
            raise ValueError("Wrong Linux asset identity")
        info = plistlib.loads((root / BUNDLE / "Contents/Info.plist").read_bytes())
        plistlib.loads((root / BUNDLE / "Contents/version.plist").read_bytes())
        keylayout = parse_keylayout(
            (root / BUNDLE / f"Contents/Resources/{LAYOUT_ID}.keylayout").read_bytes()
        )
        if keylayout.tag != "keyboard":
            raise ValueError("Invalid keylayout asset")
        identifiers = (info["CFBundleIdentifier"], info[f"KLInfo_{LAYOUT_ID}"]["TISInputSourceID"])
        if identifiers != (
            "org.sil.ukelele.keyboardlayout.bg-dvorak-phonetic",
            "org.sil.ukelele.keyboardlayout.bg-dvorak-phonetic.bg-dvorak-phonetic",
        ):
            raise ValueError("Conflicting bundle asset identity")
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        raise InstallerError(
            f"Invalid source asset: {exc}",
            2,
            path=root,
            remedy="Obtain a complete trusted project checkout.",
        ) from exc
    revision = hashlib.sha256(repr(manifest).encode()).hexdigest()
    return LayoutAssets(LAYOUT_ID, revision, ASSET_PATHS, tuple(manifest), identifiers)


def run_command(args: list[str], *, timeout: int = 30) -> str:
    """Execute checked arguments with no shell and a bounded validator timeout."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True, timeout=timeout)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "Native validator returned an error").strip()[-8192:]
        raise InstallerError(
            f"Validator failed: {args[0]}: {detail}",
            operation="validate",
            remedy="Correct the reported native configuration error and retry.",
        ) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise InstallerError(
            f"Validator failed: {args[0]}",
            operation="validate",
            remedy="Check native validator prerequisites and source files.",
        ) from exc
    return result.stdout


def verify_environment(root: Path) -> None:
    """Check prepared environment metadata without downloads, synchronization or writes."""
    try:
        pin = (root / ".python-version").read_text(encoding="utf-8").strip()
        metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
        if pin != "3.14.7" or sys.version_info[:3] != (3, 14, 7):
            raise ValueError("Python pin or interpreter differs from 3.14.7")
        if Path(sys.prefix).resolve() != (root / ".venv").resolve():
            raise ValueError("Not running in the prepared project environment")
        project = metadata["project"]
        if {v.strip() for v in lock["requires-python"].split(",")} != {
            v.strip() for v in project["requires-python"].split(",")
        }:
            raise ValueError("Stale locked Python requirement")
        package = next(p for p in lock["package"] if p["name"] == project["name"])
        if package["version"] != project["version"]:
            raise ValueError("Stale project version")
        requirements = project.get("dependencies", [])
        if requirements or package.get("dependencies"):
            raise ValueError("Runtime dependency changes require a reviewed preflight update")
        distribution = importlib.metadata.distribution(project["name"])
        if distribution.version != project["version"]:
            raise ValueError("Stale installed project")
        direct = json.loads(distribution.read_text("direct_url.json") or "{}")
        if direct.get("url") != root.as_uri() or not direct.get("dir_info", {}).get("editable"):
            raise ValueError("Installed project points to another checkout")
    except (
        OSError,
        ValueError,
        KeyError,
        StopIteration,
        importlib.metadata.PackageNotFoundError,
    ) as exc:
        raise InstallerError(
            f"Project environment requires preparation: {exc}",
            2,
            path=root,
            remedy=PREPARE,
            operation="preflight",
        ) from exc


def parse_keylayout(data: bytes) -> ET.Element:
    """Structurally validate Apple's XML 1.1 without fetching external entities.

    Expat implements XML 1.0. Map XML 1.1 control character references to a safe
    placeholder only in the validation copy; installed bytes and hashes stay intact.
    """
    if b"<!ENTITY" in data:
        raise ValueError("Entity declarations are not allowed")

    def control(match: re.Match[bytes]) -> bytes:
        token = match.group(1)
        number = int(token[1:], 16) if token.startswith(b"x") else int(token)
        if number == 0 or number > 0x10FFFF or 0xD800 <= number <= 0xDFFF:
            raise ValueError("Invalid XML character reference")
        if number < 32 and number not in (9, 10, 13):
            return b"_"
        return match.group(0)

    structural = re.sub(rb"&#(x[0-9a-fA-F]+|[0-9]+);", control, data)
    try:
        return ET.fromstring(structural)
    except ET.ParseError as exc:
        raise ValueError("Malformed keylayout XML") from exc


def select_action(health: Health) -> Action:
    """Shared state-to-action policy; unsafe states never produce an apply plan."""
    if health == Health.UNSAFE:
        raise InstallerError(
            "Unsafe installation state",
            4,
            remedy="Resolve the reported ownership/configuration conflict first.",
        )
    return {
        Health.ABSENT: Action.INSTALL,
        Health.CURRENT: Action.NOOP,
        Health.OUTDATED: Action.UPDATE,
        Health.REPAIRABLE: Action.REPAIR,
    }[health]


def consent(message: str, *, yes: bool) -> None:
    """Explain the boundary and require explicit noninteractive consent."""
    if yes:
        return
    if not sys.stdin.isatty():
        raise InstallerError(
            "Confirmation unavailable in noninteractive input",
            3,
            remedy="Review a dry-run, then pass --yes to accept the plan.",
        )
    if input(f"{message} [y/N] ").strip().lower() not in ("y", "yes"):
        raise InstallerError(
            "Authorization declined", 3, remedy="No changes requested; retry when ready."
        )


def execute(
    adapter: PlatformAdapter,
    context: PlatformContext,
    *,
    command: str = "install",
    dry_run: bool = False,
    yes: bool = False,
    recovery_id: str | None = None,
    diagnostics: Diagnostics | None = None,
) -> RunResult:
    """Coordinate inspection, consent and recoverable native work using injected adapters."""
    from dataclasses import replace

    from bg_dvorak_phonetic.diagnostics import Diagnostics
    from bg_dvorak_phonetic.models import RunResult
    from bg_dvorak_phonetic.transaction import Transaction

    events = diagnostics or Diagnostics()
    events.emit("preflight", f"platform={context.os_id} scope={context.scope}")
    assets = inventory(context.project_root)
    adapter.validate_assets(context, assets)
    engine = Transaction(lock_factory=adapter.acquire_lock)
    events.emit("inspect", "Inspect installation and pending recovery")
    recovery = adapter.recovery_access(context, assets)
    if recovery.requires_authorization:
        events.emit("authorize", "Read-only authorization to inspect protected recovery journals")
        consent("Authorize read-only recovery inspection (no state writes)?", yes=yes)
    pending = recovery.pending()
    if command == "recover":
        if recovery_id is None:
            raise InstallerError("Recovery requires a run ID", 2)
        if not dry_run:
            events.emit("authorize", f"Restore transaction {recovery_id}")
            consent("Restore the recorded previous state?", yes=yes)
        events.emit("restore", f"{'Preview' if dry_run else 'Restore'} transaction {recovery_id}")
        recovery.restore(recovery_id, dry_run=dry_run)
        events.emit(
            "verify-restored",
            "Recovery preview validated" if dry_run else "Original state restored",
        )
        return RunResult(
            "unchanged" if dry_run else "restored",
            recovery_id=recovery_id,
            next_steps=("Review activation manually after restoration.",),
        )
    if pending and command == "install" and not dry_run:
        events.emit("authorize", f"Restore unfinished transactions: {', '.join(pending)}")
        consent("Restore unfinished transactions before installation?", yes=yes)
        for run_id in pending:
            events.emit("restore", run_id)
            recovery.restore(run_id)
            events.emit("verify-restored", run_id)
    state = adapter.inspect(context)
    events.emit("inspect", f"health={state.health.value} activation={state.activation}")
    if pending and (dry_run or command == "status"):
        return RunResult(
            "refused",
            installation_status=state.health.value,
            recovery_id=pending[0],
            warnings=("Recovery pending; preview did not restore anything.",),
            next_steps=(f"Recover {pending[0]} in scope {context.scope}.",),
            exit_code=5,
        )
    if command == "status":
        result = RunResult("unchanged", installation_status=state.health.value)
        return replace_result_guidance(adapter, context, result)
    expected_action = select_action(state.health)
    plan = replace(adapter.plan(state, assets), run_id=events.run_id)
    if plan.action != expected_action:
        raise InstallerError("Adapter plan violates shared state policy", 4)
    events.emit("plan", f"action={plan.action.value}; changes={len(plan.operations)}")
    if dry_run or not plan.operations:
        result = RunResult(
            "unchanged",
            run_id=plan.run_id,
            installation_status=state.health.value,
            next_steps=(f"Proposed action: {plan.action.value}",) if dry_run else (),
        )
        events.emit("complete", "Preview complete" if dry_run else "Already current")
        return replace_result_guidance(adapter, context, result)
    events.emit("authorize", f"Apply {plan.action.value} in {context.scope} scope")
    consent("Apply the displayed plan and retain recovery backups?", yes=yes)
    events.emit(
        "backup", f"Recoverable originals will be retained at {context.state_root / plan.run_id}"
    )
    events.emit(
        "validate-staged", "Validate supplied candidates before replacing installed content"
    )
    events.emit("apply", "Apply authorized scoped transaction")
    adapter.apply_authorized(context, plan, engine)
    events.emit("verify-installed", "Native validation and manifest checks passed")
    action = {"install": "installed", "update": "updated", "repair": "repaired"}[plan.action.value]
    result = RunResult(
        action,
        run_id=plan.run_id,
        installation_status="current",
        changed_paths=tuple(op.destination for op in plan.operations),
        recovery_id=plan.run_id,
    )
    events.emit("complete", f"action={action} activation=pending")
    return replace_result_guidance(adapter, context, result)


def replace_result_guidance(
    adapter: PlatformAdapter, context: PlatformContext, result: RunResult
) -> RunResult:
    """Attach native activation steps without claiming active typing."""
    from dataclasses import replace

    return replace(
        result, next_steps=(*result.next_steps, *adapter.activation_guidance(context, result))
    )
