"""Ordered plain-text diagnostics with actionable error categories."""

import re
import sys
from pathlib import Path
from typing import TextIO

from bg_dvorak_phonetic.models import DiagnosticEvent, new_id


class InstallerError(Exception):
    """A classified failure with recovery guidance safe to show to users."""

    def __init__(
        self,
        message: str,
        code: int = 1,
        *,
        remedy: str = "Inspect the reported location and retry.",
        operation: str = "installation",
        path: Path | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.remedy = remedy
        self.operation = operation
        self.path = path


def redact(text: str) -> str:
    """Remove common credential forms without dumping process environments."""
    text = re.sub(
        r"(?i)(password|token|secret|authorization)(\s*[=:]\s*)\S+", r"\1\2[redacted]", text
    )
    return re.sub(r"(https?://)[^\s/@]+:[^\s/@]+@", r"\1[redacted]@", text)


class Diagnostics:
    """Emit timestamped events to stderr (or an explicitly injected stream)."""

    def __init__(self, *, stream: TextIO | None = None, run_id: str | None = None) -> None:
        self.stream = stream if stream is not None else sys.stderr
        self.run_id = run_id or new_id()

    def emit(
        self,
        stage: str,
        message: str,
        *,
        level: str = "INFO",
        operation: str | None = None,
        path: Path | None = None,
        cause: str | None = None,
        remedy: str | None = None,
    ) -> None:
        event = DiagnosticEvent(
            self.run_id,
            level,
            stage,
            message,
            operation=operation,
            path=path,
            cause=cause,
            remedy=remedy,
        )
        parts = [event.timestamp_utc, event.run_id, event.level, event.stage, event.message]
        for label, value in (
            ("operation", operation),
            ("path", path),
            ("cause", cause),
            ("next", remedy),
        ):
            if value is not None:
                parts.append(f"{label}={value}")
        print(redact(" | ".join(parts)).replace("\n", " "), file=self.stream, flush=True)

    def error(self, error: InstallerError) -> None:
        self.emit(
            "failed",
            str(error),
            level="ERROR",
            operation=error.operation,
            path=error.path,
            cause=str(error.__cause__) if error.__cause__ else None,
            remedy=error.remedy,
        )
