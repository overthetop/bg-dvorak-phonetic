"""Immutable workflow values and strictly versioned recovery records."""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Self
from uuid import UUID, uuid4


def new_id() -> str:
    """Generate an opaque transaction identifier, never a user path fragment."""
    return str(uuid4())


def validate_id(value: str) -> None:
    """Reject noncanonical and non-v4 transaction identifiers."""
    if not isinstance(value, str) or str(UUID(value)) != value or UUID(value).version != 4:
        raise ValueError("Invalid generated run ID")


class Health(StrEnum):
    ABSENT = "absent"
    CURRENT = "current"
    OUTDATED = "outdated"
    REPAIRABLE = "repairable"
    UNSAFE = "unsafe"


class Action(StrEnum):
    INSTALL = "install"
    UPDATE = "update"
    REPAIR = "repair"
    NOOP = "noop"


@dataclass(frozen=True)
class PlatformContext:
    """Adapter-validated platform facts and canonical scope roots."""

    os_id: str
    os_version: str
    architecture: str
    session_type: str
    scope: str
    project_root: Path
    destination_roots: tuple[Path, ...]
    state_root: Path

    def __post_init__(self) -> None:
        if self.scope not in ("user", "system"):
            raise ValueError("Unsupported scope")
        if not all(
            p.is_absolute() for p in (*self.destination_roots, self.state_root, self.project_root)
        ):
            raise ValueError("Roots must be absolute")


@dataclass(frozen=True)
class LayoutAssets:
    """Complete source inventory with byte-based identities."""

    layout_id: str
    project_revision: str
    relative_paths: tuple[str, ...]
    manifest: tuple[tuple[str, str], ...]
    native_identifiers: tuple[str, ...]


@dataclass(frozen=True)
class InstallationState:
    health: Health
    installed_manifest: tuple[tuple[str, str], ...] = ()
    registrations: tuple[str, ...] = ()
    owned_paths: tuple[Path, ...] = ()
    conflicts: tuple[str, ...] = ()
    activation: str = "pending"


@dataclass(frozen=True)
class FileOperation:
    """Data-only, scoped operation; adapters additionally restrict destinations."""

    kind: str
    destination: Path
    before_hash_or_absent: str | None = None
    after_hash_or_absent: str | None = None
    staged_path: Path | None = None
    backup_path: Path | None = None
    metadata: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in ("replace", "create", "remove-owned-duplicate"):
            raise ValueError("Unsupported operation")
        if not self.destination.is_absolute() or ".." in self.destination.parts:
            raise ValueError("Destination must be canonical and absolute")


def _fingerprint(value: object) -> str:
    encoded = json.dumps(
        value, default=str, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode()).hexdigest()


@dataclass(frozen=True)
class RegistryValue:
    name: str
    value_type: str
    value: str | int | tuple[str, ...]

    def __post_init__(self) -> None:
        supported = {
            "REG_SZ",
            "REG_EXPAND_SZ",
            "REG_MULTI_SZ",
            "REG_BINARY",
            "REG_DWORD",
            "REG_QWORD",
        }
        if not self.name or self.value_type not in supported:
            raise ValueError("Unsupported registry value")


@dataclass(frozen=True)
class RegistrySnapshot:
    exists: bool
    values: tuple[RegistryValue, ...] = ()
    security_descriptor: str | None = None

    def __post_init__(self) -> None:
        names = [item.name.casefold() for item in self.values]
        if len(names) != len(set(names)):
            raise ValueError("Case-insensitive duplicate registry value")
        if not self.exists and (self.values or self.security_descriptor is not None):
            raise ValueError("Absent registry key cannot contain values")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(asdict(self))


@dataclass(frozen=True)
class WindowsFileOperation:
    resource_id: str
    kind: str
    before_fingerprint: str | None
    after_fingerprint: str | None
    security_fingerprint: str | None
    ownership_evidence: str
    destination: Path
    staged_digest: str | None = None
    backup_reference: str | None = None
    acl_metadata: str | None = None
    resource_type: str = field(default="file", init=False)

    def __post_init__(self) -> None:
        if not self.resource_id or self.kind not in {
            "create",
            "replace",
            "remove-owned-duplicate",
        }:
            raise ValueError("Unsupported file resource operation")
        if not self.destination.is_absolute() or ".." in self.destination.parts:
            raise ValueError("Destination must be canonical and absolute")


@dataclass(frozen=True)
class RegistryOperation:
    resource_id: str
    kind: str
    before_fingerprint: str | None
    after_fingerprint: str | None
    security_fingerprint: str | None
    ownership_evidence: str
    hive: str
    view: str
    subkey: str
    before: RegistrySnapshot
    after: RegistrySnapshot
    key_created: bool
    resource_type: str = field(default="registry", init=False)

    def __post_init__(self) -> None:
        if not self.resource_id or self.kind not in {
            "create",
            "replace",
            "remove-owned-duplicate",
        }:
            raise ValueError("Unsupported registry resource operation")
        if not isinstance(self.hive, str) or self.hive != "HKLM" or self.view != "64":
            raise ValueError("Unsupported registry hive or view")
        normalized = self.subkey.replace("\\\\", "\\") if isinstance(self.subkey, str) else ""
        prefix = "SYSTEM\\CurrentControlSet\\Control\\Keyboard Layouts\\"
        if not normalized.startswith(prefix) or ".." in normalized:
            raise ValueError("Registry subkey is outside the bounded layout root")


@dataclass(frozen=True)
class ChangePlan:
    platform: str
    scope: str
    action: Action
    operations: tuple[Any, ...] = ()
    observed_hashes: tuple[tuple[str, str | None], ...] = ()
    source_hashes: tuple[tuple[str, str], ...] = ()
    validation_results: tuple[str, ...] = ()
    schema_version: int = 1
    run_id: str = field(default_factory=new_id)
    plan_digest: str = ""

    def __post_init__(self) -> None:
        validate_id(self.run_id)
        if type(self.schema_version) is not int or self.schema_version not in (1, 2):
            raise ValueError("Unsupported plan schema")
        if self.action == Action.NOOP and self.operations:
            raise ValueError("Noop cannot mutate")
        if self.schema_version == 1 and any(
            not isinstance(operation, FileOperation) for operation in self.operations
        ):
            raise ValueError("Schema-v1 plans contain only file operations")
        if self.schema_version == 2 and any(
            isinstance(operation, FileOperation) for operation in self.operations
        ):
            raise ValueError("Schema-v2 plans require tagged resource operations")
        if self.schema_version == 2 and self.action != Action.NOOP:
            computed = _fingerprint([asdict(operation) for operation in self.operations])
            if self.plan_digest and self.plan_digest != computed:
                raise ValueError("Plan digest mismatch")
            object.__setattr__(self, "plan_digest", computed)


@dataclass(frozen=True)
class RecoveryRecord:
    """Durable state; all mutation steps are persisted before further writes."""

    scope: str
    run_id: str = field(default_factory=new_id)
    schema_version: int = 1
    phase: str = "prepared"
    ordered_operations: tuple[Any, ...] = ()
    completed_steps: tuple[int, ...] = ()
    retained_originals: tuple[str, ...] = ()
    timestamps: tuple[str, ...] = field(default_factory=lambda: (datetime.now(UTC).isoformat(),))
    platform: str = "posix"
    request_digest: str = ""
    source_revision: str = ""
    installed_revision: str = ""
    expected_post_state: str = ""
    intent_step: int | None = None
    recovery_diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_id(self.run_id)
        if type(self.schema_version) is not int or self.schema_version not in (1, 2):
            raise ValueError("Unsupported journal schema")
        if self.scope not in ("user", "system"):
            raise ValueError("Invalid scope")
        phases = {
            "prepared",
            "applying",
            "verified",
            "committed",
            "rolling_back",
            "restored",
            "recovery_required",
        }
        if self.phase not in phases:
            raise ValueError("Invalid recovery phase")
        if any(
            type(step) is not int or step < 0 or step >= len(self.ordered_operations)
            for step in self.completed_steps
        ):
            raise ValueError("Invalid completed step")
        if self.intent_step is not None and (
            type(self.intent_step) is not int
            or self.intent_step < 0
            or self.intent_step >= len(self.ordered_operations)
        ):
            raise ValueError("Invalid intent step")
        if self.schema_version == 1 and any(
            not isinstance(operation, FileOperation) for operation in self.ordered_operations
        ):
            raise ValueError("Schema-v1 journals contain only file operations")
        if self.schema_version == 2:
            if self.platform != "windows":
                raise ValueError("Unsupported journal schema: v2 requires Windows platform")
            if any(isinstance(operation, FileOperation) for operation in self.ordered_operations):
                raise ValueError("Unsupported journal schema: v2 requires tagged operations")

    def to_json(self) -> str:
        """Serialize without changing the established schema-v1 wire representation."""
        data = asdict(self)
        if self.schema_version == 1:
            keep = {
                "scope",
                "run_id",
                "schema_version",
                "phase",
                "ordered_operations",
                "completed_steps",
                "retained_originals",
                "timestamps",
            }
            data = {name: value for name, value in data.items() if name in keep}
        return json.dumps(data, default=str, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> Self:
        """Parse trusted-root journal data, rejecting unsupported schemas."""
        data = json.loads(text)
        if not isinstance(data, dict) or type(data.get("schema_version")) is not int:
            raise ValueError("Unsupported journal schema")
        version = data["schema_version"]
        if version not in (1, 2):
            raise ValueError("Unsupported journal schema")
        operations: list[Any] = []
        for source in data["ordered_operations"]:
            raw = dict(source)
            if version == 1:
                for name in ("destination", "staged_path", "backup_path"):
                    if raw[name] is not None:
                        raw[name] = Path(raw[name])
                raw["metadata"] = tuple(tuple(item) for item in raw["metadata"])
                operations.append(FileOperation(**raw))
                continue
            resource_type = raw.pop("resource_type", None)
            if resource_type == "file":
                raw["destination"] = Path(raw["destination"])
                operations.append(WindowsFileOperation(**raw))
            elif resource_type == "registry":
                for name in ("before", "after"):
                    snapshot = raw[name]
                    snapshot["values"] = tuple(
                        RegistryValue(**value) for value in snapshot["values"]
                    )
                    raw[name] = RegistrySnapshot(**snapshot)
                operations.append(RegistryOperation(**raw))
            else:
                raise ValueError("Unknown resource operation type")
        data["ordered_operations"] = tuple(operations)
        for name in (
            "completed_steps",
            "retained_originals",
            "timestamps",
            "recovery_diagnostics",
        ):
            if name in data:
                data[name] = tuple(data[name])
        return cls(**data)


@dataclass(frozen=True)
class RunResult:
    action: str
    run_id: str = field(default_factory=new_id)
    installation_status: str = "unknown"
    activation_status: str = "pending"
    changed_paths: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()
    recovery_id: str | None = None
    next_steps: tuple[str, ...] = ()
    exit_code: int = 0


@dataclass(frozen=True)
class DiagnosticEvent:
    run_id: str
    level: str
    stage: str
    message: str
    timestamp_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    operation: str | None = None
    path: Path | None = None
    cause: str | None = None
    remedy: str | None = None


@dataclass(frozen=True)
class ValidationRecord:
    """Same-revision evidence; missing native artifacts can never claim a pass."""

    commit: str
    os_version: str
    runtime_version: str
    architecture: str
    scenario: str
    result: str
    diagnostics: str = ""
    coverage_artifact: str = ""
    manual_evidence: str = ""

    def __post_init__(self) -> None:
        if len(self.commit) != 40 or any(c not in "0123456789abcdef" for c in self.commit):
            raise ValueError("Expected a full commit identifier")
        if self.result not in ("passed", "failed", "pending"):
            raise ValueError("Invalid validation result")
        if self.result == "passed" and not (self.coverage_artifact or self.manual_evidence):
            raise ValueError("Missing required evidence is not success")

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> Self:
        return cls(**json.loads(text))
