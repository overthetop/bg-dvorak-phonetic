import pytest

from bg_dvorak_phonetic.models import ValidationRecord


def test_record_roundtrip_and_missing_evidence():
    record = ValidationRecord(
        commit="a" * 40,
        os_version="Ubuntu 24.04",
        runtime_version="3.14.7",
        architecture="x86_64",
        scenario="native",
        result="passed",
        diagnostics="pytest.log",
        coverage_artifact="coverage-ubuntu-24.04",
    )
    assert ValidationRecord.from_json(record.to_json()) == record
    with pytest.raises(ValueError):
        ValidationRecord(
            commit="a" * 40,
            os_version="macOS 15",
            runtime_version="3.14.7",
            architecture="arm64",
            scenario="native",
            result="passed",
        )
