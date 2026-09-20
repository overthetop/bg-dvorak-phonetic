import json
import subprocess
import sys

import pytest

MATRIX = ("ubuntu-24.04", "macos-15-intel", "macos-15", "macos-26")


@pytest.mark.parametrize("fault", [None, "missing", "failed", "stale", "no-data"])
def test_aggregate_requires_all_same_commit_jobs(project_root, tmp_path, fault):
    commit = "a" * 40
    root = tmp_path / "artifacts"
    root.mkdir()
    for index, runner in enumerate(MATRIX):
        if index == 3 and fault == "missing":
            continue
        directory = root / f"native-{runner}-{commit}"
        directory.mkdir()
        metadata = {
            "commit": commit,
            "runner": runner,
            "runtime_version": "3.14.7",
            "result": "passed",
        }
        if index == 3:
            if fault == "stale":
                metadata["commit"] = "b" * 40
            if fault == "failed":
                metadata["result"] = "failed"
        (directory / "metadata.json").write_text(json.dumps(metadata))
        if not (index == 3 and fault == "no-data"):
            (directory / ".coverage.fixture").write_bytes(b"fixture-only")
    output = tmp_path / "input"
    result = subprocess.run(
        [
            sys.executable,
            str(project_root / "tools/collect_coverage.py"),
            str(root),
            commit,
            str(output),
        ],
        capture_output=True,
    )
    assert result.returncode == (0 if fault is None else 1)
    assert output.exists() is (fault is None)
