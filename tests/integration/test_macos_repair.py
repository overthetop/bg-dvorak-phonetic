import plistlib
import shutil

import pytest

from bg_dvorak_phonetic.diagnostics import InstallerError
from bg_dvorak_phonetic.models import Health, PlatformContext
from bg_dvorak_phonetic.platforms.macos import MacOSAdapter
from bg_dvorak_phonetic.transaction import Transaction
from bg_dvorak_phonetic.workflow import BUNDLE, inventory


@pytest.fixture
def mac_case(asset_checkout, isolated_roots):
    # Portable identity/transaction evidence only; this is not native macOS validation.
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
    return adapter, context, inventory(asset_checkout)


def test_partial_matching_identity_and_duplicates(mac_case):
    adapter, context, assets = mac_case
    source = context.project_root / BUNDLE
    shutil.copytree(source, adapter.target)
    (adapter.target / "Contents/Resources/bg-dvorak-phonetic.icns").unlink()
    duplicate = adapter.user_root / "old.bundle"
    shutil.copytree(source, duplicate)
    state = adapter.inspect(context)
    assert state.health == Health.REPAIRABLE
    plan = adapter.plan(state, assets)
    Transaction().apply(context, plan, lambda: adapter.verify_installed(context, assets))
    assert not duplicate.exists()
    for _ in range(3):
        assert adapter.inspect(context).health == Health.CURRENT


def test_conflicting_id_and_unknown_population_refused(mac_case):
    adapter, context, assets = mac_case
    shutil.copytree(context.project_root / BUNDLE, adapter.target)
    info = adapter.target / "Contents/Info.plist"
    value = plistlib.loads(info.read_bytes())
    value["CFBundleIdentifier"] = "someone.else"
    info.write_bytes(plistlib.dumps(value))
    with pytest.raises(InstallerError, match="Conflicting"):
        adapter.inspect(context)
    info.unlink()
    with pytest.raises(InstallerError, match="Ambiguous"):
        adapter.inspect(context)


def test_empty_destination_repairable_and_global_conflict(mac_case):
    adapter, context, assets = mac_case
    adapter.target.mkdir()
    assert adapter.inspect(context).health == Health.REPAIRABLE
    shutil.copytree(context.project_root / BUNDLE, adapter.system_root / "global.bundle")
    with pytest.raises(InstallerError, match="system-wide"):
        adapter.inspect(context)


def test_trusted_receipt_recognizes_missing_identity(mac_case):
    adapter, context, assets = mac_case
    state = adapter.inspect(context)
    Transaction().apply(
        context, adapter.plan(state, assets), lambda: adapter.verify_installed(context, assets)
    )
    (adapter.target / "Contents/Info.plist").unlink()
    assert adapter.inspect(context).health == Health.REPAIRABLE
    plan = adapter.plan(adapter.inspect(context), assets)
    Transaction().apply(context, plan, lambda: adapter.verify_installed(context, assets))
    assert adapter.inspect(context).health == Health.CURRENT


def test_partial_identity_conflict_in_another_user_bundle(mac_case):
    adapter, context, assets = mac_case
    duplicate = adapter.user_root / "conflict.bundle"
    shutil.copytree(context.project_root / BUNDLE, duplicate)
    info = duplicate / "Contents/Info.plist"
    value = plistlib.loads(info.read_bytes())
    value["CFBundleIdentifier"] = "someone.else"
    info.write_bytes(plistlib.dumps(value))
    with pytest.raises(InstallerError, match="Conflicting user"):
        adapter.inspect(context)
