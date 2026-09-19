import pytest

from bg_dvorak_phonetic.platforms import get_adapter


def test_unsupported_adapter():
    with pytest.raises(ValueError):
        get_adapter("windows")


def test_nine_operations_present():
    for name in ("linux", "macos"):
        adapter = get_adapter(name)
        for operation in (
            "probe",
            "validate_assets",
            "inspect",
            "plan",
            "validate_staged",
            "acquire_lock",
            "apply_authorized",
            "verify_installed",
            "activation_guidance",
        ):
            assert callable(getattr(adapter, operation))


@pytest.mark.parametrize(
    "os_id,version,architecture,supported",
    [
        ("linux", "24.04", "x86_64", True),
        ("linux", "22.04", "x86_64", False),
        ("linux", "24.04", "aarch64", False),
        ("macos", "15.5", "x86_64", True),
        ("macos", "15.5", "arm64", True),
        ("macos", "26.0", "arm64", True),
        ("macos", "26.0", "x86_64", False),
        ("macos", "14.0", "arm64", False),
    ],
)
def test_support_matrix_probe_is_read_only(monkeypatch, os_id, version, architecture, supported):
    import platform

    from bg_dvorak_phonetic.diagnostics import InstallerError

    monkeypatch.setattr(platform, "system", lambda: "Linux" if os_id == "linux" else "Darwin")
    monkeypatch.setattr(platform, "machine", lambda: architecture)
    monkeypatch.setattr(
        platform, "freedesktop_os_release", lambda: {"ID": "ubuntu", "VERSION_ID": version}
    )
    monkeypatch.setattr(platform, "mac_ver", lambda: (version, ("", "", ""), architecture))
    adapter = get_adapter(os_id)
    if supported:
        context = adapter.probe("system" if os_id == "linux" else "user")
        assert context.os_id == os_id
        assert context.architecture == architecture
    else:
        with pytest.raises(InstallerError) as error:
            adapter.probe("system" if os_id == "linux" else "user")
        assert error.value.code == 2


def test_shared_import_does_not_load_native_adapters():
    import subprocess
    import sys

    script = (
        "import sys; import bg_dvorak_phonetic.workflow; "
        'assert "bg_dvorak_phonetic.platforms.linux" not in sys.modules; '
        'assert "bg_dvorak_phonetic.platforms.macos" not in sys.modules'
    )
    assert subprocess.run([sys.executable, "-c", script], capture_output=True).returncode == 0
