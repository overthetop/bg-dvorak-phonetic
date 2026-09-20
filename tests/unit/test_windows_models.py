import json
from pathlib import Path
from uuid import UUID

import pytest

from bg_dvorak_phonetic.models import (
    Action,
    ChangePlan,
    FileOperation,
    RecoveryRecord,
    RegistryOperation,
    RegistrySnapshot,
    RegistryValue,
    WindowsFileOperation,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "windows_v1_journals.json"


def test_registry_snapshot_preserves_absent_empty_and_types():
    absent = RegistrySnapshot(exists=False)
    empty = RegistrySnapshot(exists=True, values=())
    assert absent.fingerprint != empty.fingerprint
    values = (
        RegistryValue("Layout File", "REG_SZ", "bgdv.dll"),
        RegistryValue("Binary", "REG_BINARY", "00ff"),
        RegistryValue("Number", "REG_DWORD", 0),
    )
    snapshot = RegistrySnapshot(exists=True, values=values, security_descriptor="D:P")
    assert snapshot.values == values
    assert snapshot.fingerprint == snapshot.fingerprint


def test_registry_names_are_canonicalized_case_insensitively():
    with pytest.raises(ValueError, match="duplicate"):
        RegistrySnapshot(
            exists=True,
            values=(
                RegistryValue("Layout File", "REG_SZ", "one.dll"),
                RegistryValue("layout file", "REG_SZ", "two.dll"),
            ),
        )


def test_v2_plan_has_tagged_operations_and_canonical_digest(tmp_path):
    file_op = WindowsFileOperation(
        resource_id="layout-dll",
        kind="create",
        before_fingerprint=None,
        after_fingerprint="a" * 64,
        security_fingerprint=None,
        ownership_evidence="manifest",
        destination=tmp_path / "bgdv.dll",
        staged_digest="a" * 64,
    )
    registry_op = RegistryOperation(
        resource_id="layout-registration",
        kind="replace",
        before_fingerprint=None,
        after_fingerprint="b" * 64,
        security_fingerprint=None,
        ownership_evidence="manifest",
        hive="HKLM",
        view="64",
        subkey=r"SYSTEM\\CurrentControlSet\\Control\\Keyboard Layouts\\A0D00402",
        before=RegistrySnapshot(exists=False),
        after=RegistrySnapshot(
            exists=True,
            values=(RegistryValue("Layout File", "REG_SZ", "bgdv.dll"),),
        ),
        key_created=True,
    )
    plan = ChangePlan(
        platform="windows",
        scope="system",
        action=Action.INSTALL,
        operations=(file_op, registry_op),
        schema_version=2,
    )
    assert UUID(plan.run_id).version == 4
    assert plan.plan_digest
    assert [operation.resource_type for operation in plan.operations] == ["file", "registry"]


def test_v2_noop_has_no_operations_or_digest():
    plan = ChangePlan(platform="windows", scope="system", action=Action.NOOP, schema_version=2)
    assert plan.operations == ()
    assert plan.plan_digest == ""


@pytest.mark.parametrize("schema", [0, 3, True, "2"])
def test_unknown_plan_versions_fail_safely(schema):
    with pytest.raises(ValueError, match="schema"):
        ChangePlan(
            platform="windows",
            scope="system",
            action=Action.NOOP,
            schema_version=schema,
        )


def test_registry_operation_rejects_path_and_unbounded_resources(tmp_path):
    with pytest.raises((TypeError, ValueError)):
        RegistryOperation(
            resource_id="bad",
            kind="replace",
            before_fingerprint=None,
            after_fingerprint=None,
            security_fingerprint=None,
            ownership_evidence="none",
            hive=tmp_path,
            view="64",
            subkey="elsewhere",
            before=RegistrySnapshot(exists=False),
            after=RegistrySnapshot(exists=False),
            key_created=False,
        )


def test_immutable_v1_journals_roundtrip_without_rewriting():
    fixtures = json.loads(FIXTURES.read_text())
    for fixture in fixtures:
        raw = fixture["journal"]
        record = RecoveryRecord.from_json(json.dumps(raw, ensure_ascii=False))
        assert record.schema_version == 1
        decoded = json.loads(record.to_json())
        assert decoded == raw
        assert isinstance(record.ordered_operations[0], FileOperation)


def test_v2_recovery_roundtrip_preserves_registry_types(tmp_path):
    operation = RegistryOperation(
        resource_id="layout-registration",
        kind="replace",
        before_fingerprint=None,
        after_fingerprint="c" * 64,
        security_fingerprint="d" * 64,
        ownership_evidence="receipt",
        hive="HKLM",
        view="64",
        subkey=r"SYSTEM\\CurrentControlSet\\Control\\Keyboard Layouts\\A0D00402",
        before=RegistrySnapshot(exists=False),
        after=RegistrySnapshot(
            exists=True,
            values=(RegistryValue("Layout Id", "REG_SZ", ""),),
        ),
        key_created=True,
    )
    record = RecoveryRecord(
        platform="windows",
        scope="system",
        schema_version=2,
        ordered_operations=(operation,),
        request_digest="e" * 64,
        source_revision="f" * 40,
    )
    assert RecoveryRecord.from_json(record.to_json()) == record
