import shutil
import sys

import pytest

from bg_dvorak_phonetic.models import Health
from bg_dvorak_phonetic.platforms.macos import MacOSAdapter
from bg_dvorak_phonetic.transaction import Transaction
from bg_dvorak_phonetic.workflow import inventory


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS native validator")
def test_native_fresh_bundle(asset_checkout, isolated_roots):
    assert shutil.which("plutil"), "Required macOS validator is missing"
    adapter = MacOSAdapter(
        root=asset_checkout,
        user_root=isolated_roots["user"],
        system_root=isolated_roots["system"],
        state_root=isolated_roots["state"],
        testing=True,
    )
    context = adapter.probe(None)
    isolated_roots["state"].chmod(0o700)
    assets = inventory(asset_checkout)
    adapter.validate_assets(context, assets)
    state = adapter.inspect(context)
    assert state.health == Health.ABSENT
    plan = adapter.plan(state, assets)
    Transaction().apply(context, plan, lambda: adapter.verify_installed(context, assets))
    for _ in range(3):
        assert adapter.inspect(context).health == Health.CURRENT
