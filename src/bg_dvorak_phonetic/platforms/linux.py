"""Ubuntu XKB adapter with bounded byte-preserving transformations."""

import os
import platform
import re
import shutil
import stat
import tempfile
import xml.etree.ElementTree as ET
from contextlib import AbstractContextManager
from pathlib import Path
from xml.parsers import expat

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
from bg_dvorak_phonetic.transaction import scope_lock
from bg_dvorak_phonetic.workflow import (
    LAYOUT_ID,
    digest,
    project_root,
    run_command,
    safe_path,
    select_action,
)

TOKEN = re.compile(rb'\s+|//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|[A-Za-z_][\w-]*|.', re.S)
FLAGS = {
    b"partial",
    b"default",
    b"hidden",
    b"alphanumeric_keys",
    b"modifier_keys",
    b"keypad_keys",
    b"function_keys",
    b"alternate_group",
}


def symbol_spans(data: bytes) -> list[tuple[int, int]]:
    """Locate only complete project blocks, ignoring braces in comments/strings."""
    tokens = [
        m
        for m in TOKEN.finditer(data)
        if not m.group().isspace() and not m.group().startswith((b"//", b"/*"))
    ]
    depth = 0
    spans = []
    start: int | None = None
    for index, token in enumerate(tokens):
        value = token.group()
        if value == b'"' or (value == b"/" and data[token.start() :].startswith(b"/*")):
            raise InstallerError("Unterminated XKB string or comment", 4)
        if value == b"xkb_symbols" and depth == 0:
            if index + 2 >= len(tokens) or tokens[index + 2].group() != b"{":
                raise InstallerError("Malformed XKB declaration", 4)
            if tokens[index + 1].group() == b'"bg-dvorak-phonetic"':
                first = index
                while first > 0 and tokens[first - 1].group() in FLAGS:
                    first -= 1
                start = tokens[first].start()
        if value == b"{":
            depth += 1
        elif value == b"}":
            depth -= 1
            if depth < 0:
                raise InstallerError("Unbalanced shared XKB file", 4)
            if depth == 0 and start is not None:
                if index + 1 >= len(tokens) or tokens[index + 1].group() != b";":
                    raise InstallerError("Unbounded project XKB block", 4)
                spans.append((start, tokens[index + 1].end()))
                start = None
    if depth or start is not None:
        raise InstallerError("Unbalanced shared XKB file", 4)
    return spans


def transform_symbols(data: bytes, source: bytes) -> bytes:
    """Insert/update/deduplicate complete project definitions, preserving other bytes."""
    source = source.strip()
    if len(symbol_spans(source)) != 1:
        raise InstallerError("Invalid supplied XKB definition", 2)
    spans = symbol_spans(data)
    if not spans:
        return data + (b"" if data.endswith(b"\n") else b"\n") + source + b"\n"
    for index in reversed(range(len(spans))):
        start, end = spans[index]
        data = data[:start] + (source if index == 0 else b"") + data[end:]
    return data


def transform_registry(data: bytes, entry: bytes) -> bytes:
    """Edit only exact variant spans under the unique Bulgarian registry layout."""
    if b"<!ENTITY" in data or b"<!ENTITY" in entry:
        raise InstallerError("XML entity declarations are unsafe", 4)
    try:
        root = ET.fromstring(data)
        source = ET.fromstring(entry)
        if source.tag != "variant" or source.findtext("configItem/name") != LAYOUT_ID:
            raise ValueError("Invalid supplied variant")
        layouts = [
            node
            for node in root.findall("./layoutList/layout")
            if node.findtext("configItem/name") == "bg"
        ]
        if len(layouts) != 1 or len(layouts[0].findall("variantList")) != 1:
            raise ValueError("Expected a unique Bulgarian layout and variant list")
        # Expat supplies byte offsets; pair its traversal with ElementTree's element order.
        elements = iter(root.iter())
        stack: list[tuple[ET.Element, int]] = []
        spans: dict[ET.Element, tuple[int, int, int]] = {}
        parser = expat.ParserCreate()

        def begin(name: str, attributes: dict[str, str]) -> None:
            stack.append((next(elements), parser.CurrentByteIndex))

        def end(name: str) -> None:
            node, start = stack.pop()
            closing = parser.CurrentByteIndex
            if data[closing : closing + 2] == b"</":
                finish = data.index(b">", closing) + 1
            else:
                finish = closing
            spans[node] = (start, closing, finish)

        parser.StartElementHandler = begin
        parser.EndElementHandler = end
        parser.ExternalEntityRefHandler = lambda *args: 0
        parser.Parse(data, True)
        variants = layouts[0].find("variantList")
        assert variants is not None
        matches = [
            node
            for node in variants.findall("variant")
            if node.findtext("configItem/name") == LAYOUT_ID
        ]
        if matches:
            for index in reversed(range(len(matches))):
                start, _, end_offset = spans[matches[index]]
                data = data[:start] + (entry.strip() if index == 0 else b"") + data[end_offset:]
        else:
            start, closing, finish = spans[variants]
            if data[start:finish].rstrip().endswith(b"/>"):
                data = (
                    data[:start]
                    + b"<variantList>"
                    + entry.strip()
                    + b"</variantList>"
                    + data[finish:]
                )
            else:
                data = data[:closing] + entry.strip() + data[closing:]
        return data
    except (ET.ParseError, expat.ExpatError, ValueError, StopIteration) as exc:
        raise InstallerError(
            "Malformed or ambiguous shared XML registry",
            4,
            remedy="Restore the distro registry, then retry.",
        ) from exc


class LinuxAdapter:
    """Native Linux paths are fixed; alternate roots are only injected by in-process tests."""

    def __init__(
        self,
        *,
        root: Path | None = None,
        xkb_root: Path | None = None,
        state_root: Path | None = None,
        testing: bool = False,
        runner: CommandRunner = run_command,
    ) -> None:
        if not testing and (xkb_root is not None or state_root is not None):
            raise ValueError("Destination overrides are test-only")
        self.root = root or project_root()
        self.xkb = xkb_root or Path("/usr/share/X11/xkb")
        self.state = state_root or Path("/var/lib/bg-dvorak-phonetic")
        self.runner = runner
        self.testing = testing
        self.context: PlatformContext | None = None
        self.staging: tempfile.TemporaryDirectory[str] | None = None
        self.candidates: dict[Path, bytes] = {}

    def recovery_access(self, context: PlatformContext, assets: LayoutAssets) -> RecoveryAccess:
        from bg_dvorak_phonetic.transaction import LocalRecoveryAccess

        if not self.testing and os.geteuid() != 0 and context.state_root.exists():
            from bg_dvorak_phonetic.privileged import LinuxRecoveryAccess

            return LinuxRecoveryAccess(assets.manifest)
        return LocalRecoveryAccess(context)

    def probe(self, requested_scope: str | None) -> PlatformContext:
        facts = platform.freedesktop_os_release() if platform.system() == "Linux" else {}
        if (
            facts.get("ID") != "ubuntu"
            or facts.get("VERSION_ID") != "24.04"
            or platform.machine() != "x86_64"
        ):
            raise InstallerError("Supported Linux: Ubuntu 24.04 x86_64", 2)
        if requested_scope != "system":
            raise InstallerError(
                "Linux installation requires --scope system",
                2,
                remedy="Run install --scope system to select system-wide changes.",
            )
        self.context = PlatformContext(
            "linux",
            "24.04",
            platform.machine(),
            os.environ.get("XDG_SESSION_TYPE", "headless"),
            "system",
            self.root,
            (self.xkb,),
            self.state,
        )
        return self.context

    def validate_assets(self, context: PlatformContext, assets: LayoutAssets) -> tuple[str, ...]:
        if not shutil.which("xkbcli"):
            raise InstallerError(
                "Missing xkbcli validator",
                2,
                remedy="Install xkb-data and libxkbcommon-tools with apt.",
            )
        symbol_spans((self.root / "linux/symbols-bg-dv").read_bytes())
        return ("source-identities",)

    def _targets(self) -> tuple[Path, ...]:
        targets = [self.xkb / "symbols/bg", self.xkb / "rules/evdev.xml"]
        base = self.xkb / "rules/base.xml"
        if base.is_symlink():
            safe_path(base.parent)
            if base.resolve() != targets[1] or not targets[1].is_file():
                raise InstallerError("Unverified distro registry alias", 4, path=base)
        elif base.exists():
            targets.append(base)
        for target in targets:
            if not self.testing:
                for location in (target, *target.parents):
                    info = location.stat(follow_symlinks=False)
                    if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o022:
                        raise InstallerError(
                            "XKB path must be root-owned and not writable by others",
                            4,
                            path=location,
                        )
            safe_path(target)
            if not target.is_file():
                raise InstallerError(
                    "Missing distro XKB file",
                    2,
                    path=target,
                    remedy="Restore the xkb-data package first.",
                )
        return tuple(targets)

    def inspect(self, context: PlatformContext) -> InstallationState:
        self.candidates = {}
        registrations: list[str] = []
        owned = []
        for target in self._targets():
            old = target.read_bytes()
            if target.name == "bg":
                transformed = transform_symbols(
                    old, (self.root / "linux/symbols-bg-dv").read_bytes()
                )
                registrations.extend(str(target) for _ in symbol_spans(old))
            else:
                transformed = transform_registry(old, (self.root / "linux/evdev.xml").read_bytes())
                document = ET.fromstring(old)
                for layout in document.findall("./layoutList/layout"):
                    if layout.findtext("configItem/name") == "bg":
                        registrations.extend(
                            str(target)
                            for node in layout.findall("./variantList/variant")
                            if node.findtext("configItem/name") == LAYOUT_ID
                        )
            self.candidates[target] = transformed
            if transformed != old:
                owned.append(target)
        if not owned:
            health = Health.CURRENT
        elif not registrations:
            health = Health.ABSENT
        elif any(registrations.count(str(p)) != 1 for p in self.candidates):
            health = Health.REPAIRABLE
        else:
            health = Health.OUTDATED
        return InstallationState(
            health,
            tuple((str(p), digest(p) or "") for p in self.candidates),
            tuple(registrations),
            tuple(self.candidates),
        )

    def plan(self, state: InstallationState, assets: LayoutAssets) -> ChangePlan:
        assert self.context is not None
        if state.health == Health.UNSAFE:
            raise InstallerError("Unsafe XKB ownership", 4)
        if self.staging is not None:
            self.staging.cleanup()
        self.staging = tempfile.TemporaryDirectory(prefix="bg-dvorak-xkb-")
        stage = Path(self.staging.name).resolve()
        operations = []
        for target, content in self.candidates.items():
            staged = stage / target.relative_to(self.xkb)
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(content)
            if content != target.read_bytes():
                operations.append(
                    FileOperation("replace", target, digest(target), digest(staged), staged)
                )
        self.validate_staged(self.context, stage)
        action = select_action(state.health)
        return ChangePlan(
            "linux",
            self.context.scope,
            action,
            tuple(operations),
            tuple((str(p), digest(p)) for p in self.candidates),
            assets.manifest,
        )

    def validate_staged(self, context: PlatformContext, staged: Path) -> tuple[str, ...]:
        self.runner(
            [
                "xkbcli",
                "compile-keymap",
                "--include",
                str(staged),
                "--include-defaults",
                "--layout",
                "bg",
                "--variant",
                LAYOUT_ID,
            ],
            timeout=30,
        )
        return ("xkbcli-compile-keymap",)

    def acquire_lock(self, context: PlatformContext) -> AbstractContextManager[None]:
        return scope_lock(context)

    def apply_authorized(
        self, context: PlatformContext, plan: ChangePlan, engine: TransactionEngine
    ) -> None:
        if self.testing or os.geteuid() == 0:
            from bg_dvorak_phonetic.workflow import inventory

            engine.apply(
                context, plan, lambda: self.verify_installed(context, inventory(self.root))
            )
        else:
            import sys

            from bg_dvorak_phonetic.privileged import invoke

            invoke(
                {
                    "schema_version": 1,
                    "action": "apply",
                    "source_hashes": dict(plan.source_hashes),
                    "observed_hashes": dict(plan.observed_hashes),
                    "run_id": plan.run_id,
                },
                interactive=sys.stdin.isatty(),
            )

    def verify_installed(self, context: PlatformContext, assets: LayoutAssets) -> None:
        if self.inspect(context).health != Health.CURRENT:
            raise InstallerError("Installed XKB manifest does not match plan", path=self.xkb)
        self.validate_staged(context, self.xkb)

    def activation_guidance(self, context: PlatformContext, result: RunResult) -> tuple[str, ...]:
        return (
            "GNOME Settings > Keyboard > Input Sources: add Bulgarian (Dvorak phonetic).",
            "Identity: layout bg, variant bg-dvorak-phonetic. Selection and typing remain pending.",
            "On Wayland use GNOME Input Sources; setxkbmap does not configure Wayland.",
            "If discovery needs a new session, save work and log out/in manually.",
        )
