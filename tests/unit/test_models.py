from dataclasses import FrozenInstanceError
from pathlib import Path
from uuid import UUID

import pytest

from bg_dvorak_phonetic.models import (
    Action,
    ChangePlan,
    FileOperation,
    Health,
    RecoveryRecord,
    RunResult,
)


def test_health_and_action_values():
    assert {item.value for item in Health} == {
        "absent",
        "current",
        "outdated",
        "repairable",
        "unsafe",
    }
    assert {item.value for item in Action} == {"install", "update", "repair", "noop"}


def test_plan_is_immutable_and_has_generated_identifier():
    plan = ChangePlan(platform="linux", scope="system", action=Action.NOOP)
    assert UUID(plan.run_id).version == 4
    assert plan.schema_version == 1
    with pytest.raises(FrozenInstanceError):
        plan.scope = "user"


def test_operation_rejects_relative_destination_and_arbitrary_command():
    with pytest.raises(ValueError):
        FileOperation(kind="create", destination=Path("../bad"))
    with pytest.raises(ValueError):
        FileOperation(kind="execute", destination=Path("/tmp/bad"))


def test_noop_rejects_mutation():
    operation = FileOperation(kind="create", destination=Path("/tmp/layout"))
    with pytest.raises(ValueError):
        ChangePlan(platform="linux", scope="system", action=Action.NOOP, operations=(operation,))


def test_journal_roundtrip_and_schema_refusal():
    record = RecoveryRecord(scope="user")
    encoded = record.to_json()
    assert RecoveryRecord.from_json(encoded) == record
    with pytest.raises(ValueError, match="schema"):
        RecoveryRecord.from_json(encoded.replace('"schema_version": 1', '"schema_version": 2'))
    with pytest.raises(ValueError):
        RecoveryRecord(run_id="../../escape", scope="user")


def test_success_does_not_claim_activation():
    assert RunResult(action="installed").activation_status == "pending"


@pytest.mark.parametrize("bad_id", [None, 123, "../escape", "A" * 36])
def test_invalid_journal_identifiers_refused(bad_id):
    import json

    record = json.loads(RecoveryRecord(scope="user").to_json())
    record["run_id"] = bad_id
    with pytest.raises(ValueError):
        RecoveryRecord.from_json(json.dumps(record))


def test_boolean_schema_is_not_version_one():
    with pytest.raises(ValueError):
        RecoveryRecord(scope="user", schema_version=True)
