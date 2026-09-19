import importlib.util
from pathlib import Path

from bg_dvorak_phonetic.workflow import execute


def test_third_adapter_uses_shared_workflow(asset_checkout, tmp_path):
    path = Path(__file__).parents[1] / "fixtures/fake_platform.py"
    spec = importlib.util.spec_from_file_location("fake_platform", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    adapter = module.FakeAdapter(asset_checkout, tmp_path / "fake")
    context = adapter.probe("user")
    assert execute(adapter, context, yes=True).action == "installed"
    assert execute(adapter, context, yes=True).action == "unchanged"
    adapter.source.write_bytes(b"updated")
    assert execute(adapter, context, yes=True).action == "updated"
    adapter.target.write_bytes(b"broken")
    assert execute(adapter, context, yes=True).action == "repaired"
