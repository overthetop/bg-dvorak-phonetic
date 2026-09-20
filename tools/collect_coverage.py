"""Require complete successful same-commit native artifacts before coverage combination."""

import json
import shutil
import sys
from pathlib import Path

MATRIX = ("ubuntu-24.04", "macos-15-intel", "macos-15", "macos-26")


def collect(root: Path, commit: str, destination: Path) -> None:
    """Validate every artifact before copying any coverage input."""
    inputs: list[tuple[str, Path]] = []
    for label in MATRIX:
        folder = root / f"native-{label}-{commit}"
        metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
        if (
            metadata["commit"] != commit
            or metadata["runner"] != label
            or metadata["result"] != "passed"
            or metadata["runtime_version"] != "3.14.7"
        ):
            raise ValueError(f"Failed or stale native evidence: {label}")
        files = list(folder.glob(".coverage.*"))
        if not files or any(not file.is_file() or file.stat().st_size == 0 for file in files):
            raise ValueError(f"Missing coverage data: {label}")
        inputs.extend((label, file) for file in files)
    destination.mkdir(exist_ok=False)
    for label, file in inputs:
        shutil.copy2(
            file, destination / f".coverage.{label}.{file.name.removeprefix('.coverage.')}"
        )


def main() -> int:
    try:
        if len(sys.argv) != 4:
            raise ValueError("Expected artifact root, commit, and fresh output directory")
        collect(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Native aggregation refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
