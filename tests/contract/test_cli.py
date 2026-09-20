import subprocess
import sys


def cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "bg_dvorak_phonetic", *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_help_and_version():
    assert cli("--help").returncode == 0
    assert cli("--version").stdout.strip() == "0.1.0"


def test_install_requires_explicit_linux_scope():
    if sys.platform == "linux":
        result = cli("install")
        assert result.returncode == 2
        assert "--scope system" in result.stderr


def test_public_cli_rejects_arbitrary_destinations():
    assert cli("install", "--root", "/tmp").returncode == 2


def test_invalid_scope():
    assert cli("install", "--scope", "everywhere").returncode == 2
