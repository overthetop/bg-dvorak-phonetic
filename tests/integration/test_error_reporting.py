import pytest

from bg_dvorak_phonetic import cli
from bg_dvorak_phonetic.diagnostics import InstallerError
from bg_dvorak_phonetic.workflow import execute


def test_noninteractive_consent_refused(prepared_adapter, monkeypatch):
    import sys

    adapter, context = prepared_adapter
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    with pytest.raises(InstallerError) as error:
        execute(adapter, context)
    assert error.value.code == 3
    assert "--yes" in error.value.remedy
    assert not adapter.target.exists()


@pytest.mark.parametrize("code", [1, 2, 3, 4, 5, 130])
def test_cli_preserves_classified_failure(code, monkeypatch, capsys):
    def fail(root):
        raise InstallerError("failure token=hidden", code, remedy="Recover recorded originals")

    monkeypatch.setattr(cli, "verify_environment", fail)
    assert cli.main(["install", "--verbose"]) == code
    output = capsys.readouterr()
    assert output.out == ""
    assert "Recover recorded originals" in output.err
    assert "hidden" not in output.err


def test_keyboard_interrupt_code(monkeypatch, capsys):
    def interrupt(root):
        raise KeyboardInterrupt()

    monkeypatch.setattr(cli, "verify_environment", interrupt)
    assert cli.main(["install"]) == 130
    assert "Interrupted" in capsys.readouterr().err
