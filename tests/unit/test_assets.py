import pytest

from bg_dvorak_phonetic.diagnostics import InstallerError
from bg_dvorak_phonetic.workflow import inventory, project_root, run_command, verify_environment


def test_root_does_not_depend_on_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert (project_root() / "pyproject.toml").is_file()


def test_complete_assets_and_hash_changes(asset_checkout):
    first = inventory(asset_checkout)
    assert len(first.manifest) == 7
    path = asset_checkout / "linux/symbols-bg-dv"
    path.write_bytes(path.read_bytes() + b"\n")
    assert first.manifest != inventory(asset_checkout).manifest
    path.unlink()
    with pytest.raises(InstallerError, match="asset"):
        inventory(asset_checkout)


def test_symlink_asset_refused(asset_checkout, tmp_path):
    path = asset_checkout / "linux/evdev.xml"
    path.unlink()
    path.symlink_to(tmp_path / "missing")
    with pytest.raises(InstallerError):
        inventory(asset_checkout)


def test_command_failure_and_timeout():
    import sys

    with pytest.raises(InstallerError):
        run_command([sys.executable, "-c", "raise SystemExit(1)"])
    with pytest.raises(InstallerError):
        run_command([sys.executable, "-c", "import time; time.sleep(3)"], timeout=1)


def test_prepared_environment_and_changed_pin(tmp_path):
    verify_environment(project_root())
    (tmp_path / ".python-version").write_text("3.13.0")
    with pytest.raises(InstallerError, match="prepar|Python|environment"):
        verify_environment(tmp_path)


def test_malformed_keylayout_is_actionable(asset_checkout):
    from bg_dvorak_phonetic.workflow import BUNDLE

    path = asset_checkout / BUNDLE / "Contents/Resources/bg-dvorak-phonetic.keylayout"
    path.write_bytes(b"<keyboard><broken>")
    with pytest.raises(InstallerError, match="Invalid source asset") as error:
        inventory(asset_checkout)
    assert error.value.code == 2


@pytest.mark.parametrize("change", ["pin", "dependency", "version", "lock"])
def test_stale_environment_refused_without_changes(project_root, tmp_path, monkeypatch, change):
    import json
    import shutil
    import sys

    from bg_dvorak_phonetic import workflow

    for name in (".python-version", "pyproject.toml", "uv.lock"):
        shutil.copy2(project_root / name, tmp_path / name)
    (tmp_path / ".venv").mkdir()
    monkeypatch.setattr(sys, "prefix", str(tmp_path / ".venv"))

    class Distribution:
        version = "0.1.0"

        def read_text(self, name):
            return json.dumps({"url": tmp_path.as_uri(), "dir_info": {"editable": True}})

    monkeypatch.setattr(workflow.importlib.metadata, "distribution", lambda name: Distribution())
    if change == "pin":
        (tmp_path / ".python-version").write_text("3.15.0")
    elif change == "dependency":
        path = tmp_path / "pyproject.toml"
        path.write_text(path.read_text().replace("dependencies = []", 'dependencies = ["missing"]'))
    elif change == "version":
        path = tmp_path / "pyproject.toml"
        path.write_text(path.read_text().replace('version = "0.1.0"', 'version = "0.2.0"'))
    else:
        (tmp_path / "uv.lock").unlink()
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    with pytest.raises(InstallerError) as error:
        verify_environment(tmp_path)
    assert error.value.code == 2
    assert before == {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
