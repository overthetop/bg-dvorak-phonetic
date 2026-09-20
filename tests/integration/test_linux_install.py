import shutil
import sys

import pytest

from bg_dvorak_phonetic.models import Health
from bg_dvorak_phonetic.platforms.linux import LinuxAdapter, transform_registry, transform_symbols
from bg_dvorak_phonetic.transaction import Transaction
from bg_dvorak_phonetic.workflow import inventory

REGISTRY = (
    b"<xkbConfigRegistry><layoutList><layout><configItem><name>bg</name></configItem>"
    b"<variantList></variantList></layout>"
    b"</layoutList></xkbConfigRegistry>"
)
SYMBOLS = b'partial alphanumeric_keys\nxkb_symbols "other" { name[Group1]="unrelated }"; };\n'


def test_transform_preserves_unrelated_bytes(project_root):
    source = (project_root / "linux/symbols-bg-dv").read_bytes()
    output = transform_symbols(SYMBOLS, source)
    assert output.startswith(SYMBOLS)
    assert transform_symbols(output, source) == output
    entry = (project_root / "linux/evdev.xml").read_bytes()
    xml = transform_registry(REGISTRY, entry)
    assert xml.count(b"<name>bg-dvorak-phonetic</name>") == 1
    assert transform_registry(xml, entry) == xml


@pytest.mark.skipif(sys.platform != "linux", reason="Linux native validator")
def test_native_fresh_install(asset_checkout, isolated_roots):
    assert shutil.which("xkbcli"), "Required Linux validator xkbcli is missing"
    root = isolated_roots["xkb"]
    (root / "symbols").mkdir()
    (root / "rules").mkdir()
    (root / "symbols/bg").write_bytes(SYMBOLS)
    (root / "rules/evdev.xml").write_bytes(REGISTRY)
    (root / "rules/base.xml").symlink_to("evdev.xml")
    adapter = LinuxAdapter(
        root=asset_checkout, xkb_root=root, state_root=isolated_roots["state"], testing=True
    )
    context = adapter.probe("system")
    assets = inventory(asset_checkout)
    adapter.validate_assets(context, assets)
    state = adapter.inspect(context)
    assert state.health == Health.ABSENT
    plan = adapter.plan(state, assets)
    # Test scope uses user ownership in temporary state while native detection stays Linux.
    from dataclasses import replace

    context = replace(context, scope="user")
    plan = replace(plan, scope="user")
    isolated_roots["state"].chmod(0o700)
    Transaction().apply(context, plan, lambda: adapter.verify_installed(context, assets))
    for _ in range(3):
        assert adapter.inspect(context).health == Health.CURRENT
    assert (root / "rules/base.xml").is_symlink()


@pytest.mark.skipif(sys.platform != "linux", reason="Linux distro XKB data")
def test_real_distro_inputs_in_temporary_root(asset_checkout, isolated_roots):
    from dataclasses import replace
    from pathlib import Path

    distro = Path("/usr/share/X11/xkb")
    assert (distro / "symbols/bg").is_file(), "Native tests require xkb-data"
    root = isolated_roots["xkb"]
    (root / "symbols").mkdir()
    (root / "rules").mkdir()
    for relative in ("symbols/bg", "rules/evdev.xml", "rules/base.xml"):
        shutil.copy2(distro / relative, root / relative)
    adapter = LinuxAdapter(
        root=asset_checkout, xkb_root=root, state_root=isolated_roots["state"], testing=True
    )
    context = replace(adapter.probe("system"), scope="user")
    adapter.context = context
    context.state_root.chmod(0o700)
    assets = inventory(asset_checkout)
    adapter.validate_assets(context, assets)
    state = adapter.inspect(context)
    plan = adapter.plan(state, assets)
    Transaction().apply(context, plan, lambda: adapter.verify_installed(context, assets))
    for _ in range(3):
        assert adapter.inspect(context).health == Health.CURRENT
