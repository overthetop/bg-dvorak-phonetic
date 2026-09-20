"""Isolated fixtures: native tests must explicitly inject these destination roots."""

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest


@dataclass
class CommandRecorder:
    """Record argument-list commands and supply an injected process result."""

    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(tuple(args))
        if kwargs.get("check") and self.returncode:
            raise subprocess.CalledProcessError(self.returncode, args, self.stdout, self.stderr)
        return subprocess.CompletedProcess(args, self.returncode, self.stdout, self.stderr)


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def asset_checkout(tmp_path: Path, project_root: Path) -> Path:
    """Copy authoritative assets, retaining spaces and Cyrillic in the checkout path."""
    checkout = tmp_path / "layout проект"
    checkout.mkdir()
    for name in ("linux", "mac-os"):
        shutil.copytree(project_root / name, checkout / name)
    return checkout


@pytest.fixture
def isolated_roots(tmp_path: Path) -> dict[str, Path]:
    roots = {name: tmp_path / name for name in ("xkb", "user", "system", "state")}
    for root in roots.values():
        root.mkdir()
    return roots


@pytest.fixture
def command_recorder() -> CommandRecorder:
    return CommandRecorder()


@pytest.fixture
def prepared_adapter(asset_checkout, isolated_roots, monkeypatch):
    """Portable workflow fixture; native tool validation is covered separately."""
    from bg_dvorak_phonetic.models import PlatformContext
    from bg_dvorak_phonetic.platforms.macos import MacOSAdapter

    original_which = shutil.which
    monkeypatch.setattr(
        shutil,
        "which",
        lambda command: "/fixture/plutil" if command == "plutil" else original_which(command),
    )

    adapter = MacOSAdapter(
        root=asset_checkout,
        user_root=isolated_roots["user"],
        system_root=isolated_roots["system"],
        state_root=isolated_roots["state"],
        testing=True,
        runner=lambda args, timeout=30: "",
    )
    context = PlatformContext(
        "macos",
        "15",
        "arm64",
        "aqua",
        "user",
        asset_checkout,
        (isolated_roots["user"],),
        isolated_roots["state"],
    )
    adapter.context = context
    context.state_root.chmod(0o700)
    return adapter, context
