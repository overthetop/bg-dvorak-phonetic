import io

from bg_dvorak_phonetic.diagnostics import Diagnostics, InstallerError


def test_ordered_plain_stderr_and_remedy():
    stream = io.StringIO()
    events = Diagnostics(stream=stream)
    events.emit("preflight", "Checking platform")
    events.error(InstallerError("failed", 2, remedy="Prepare environment", operation="inspect"))
    lines = stream.getvalue().splitlines()
    assert "preflight" in lines[0]
    assert events.run_id in lines[0]
    assert "ERROR" in lines[1] and "Prepare environment" in lines[1]
    assert "\x1b" not in stream.getvalue()


def test_credentials_redacted():
    stream = io.StringIO()
    Diagnostics(stream=stream).emit(
        "preflight", "token=secret password=secret https://user:secret@host"
    )
    assert "secret" not in stream.getvalue()
