import json
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "covered,total,expected", [(0, 0, 1), (79, 100, 1), (80, 100, 1), (81, 100, 0), (801, 1000, 0)]
)
def test_exact_line_gate(project_root, tmp_path, covered, total, expected):
    report = tmp_path / "coverage.json"
    report.write_text(
        json.dumps(
            {
                "totals": {
                    "covered_lines": covered,
                    "num_statements": total,
                    "percent_covered": 100,
                    "covered_branches": 0,
                }
            }
        )
    )
    result = subprocess.run(
        [sys.executable, str(project_root / "tools/check_coverage.py"), str(report)],
        capture_output=True,
    )
    assert result.returncode == expected


@pytest.mark.parametrize(
    "data",
    [
        "{}",
        "bad",
        '{"totals":{"covered_lines":true,"num_statements":1}}',
        '{"totals":{"covered_lines":2,"num_statements":1}}',
    ],
)
def test_invalid_report_fails(project_root, tmp_path, data):
    report = tmp_path / "report"
    report.write_text(data)
    assert (
        subprocess.run(
            [sys.executable, str(project_root / "tools/check_coverage.py"), str(report)],
            capture_output=True,
        ).returncode
        == 1
    )
