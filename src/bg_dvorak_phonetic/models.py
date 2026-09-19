"""Immutable workflow values and strictly versioned recovery records."""

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Self
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


@dataclass(frozen=True)
class ChangePlan:
    platform: str
    scope: str
    action: Action
    operations: tuple[FileOperation, ...] = ()
    observed_hashes: tuple[tuple[str, str | None], ...] = ()
    source_hashes: tuple[tuple[str, str], ...] = ()
    validation_results: tuple[str, ...] = ()
    schema_version: int = 1
    run_id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        validate_id(self.run_id)
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("Unsupported plan schema")
        if self.action == Action.NOOP and self.operations:
            raise ValueError("Noop cannot mutate")


@dataclass(frozen=True)
class RecoveryRecord:
    """Durable state; all mutation steps are persisted before further writes."""

    scope: str
    run_id: str = field(default_factory=new_id)
    schema_version: int = 1
    phase: str = "prepared"
    ordered_operations: tuple[FileOperation, ...] = ()
    completed_steps: tuple[int, ...] = ()
    retained_originals: tuple[str, ...] = ()
    timestamps: tuple[str, ...] = field(default_factory=lambda: (datetime.now(UTC).isoformat(),))

    def __post_init__(self) -> None:
        validate_id(self.run_id)
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("Unsupported journal schema")
        if self.scope not in ("user", "system"):
            raise ValueError("Invalid scope")
        if self.phase not in (
            "prepared",
            "applying",
            "verified",
            "committed",
            "rolling_back",
            "restored",
            "recovery_required",
        ):
            raise ValueError("Invalid recovery phase")
        if any(
            type(step) is not int or step < 0 or step >= len(self.ordered_operations)
            for step in self.completed_steps
        ):
            raise ValueError("Invalid completed step")

    def to_json(self) -> str:
        """Serialize JSON for explicit UTF-8 storage by the transaction engine."""
        return json.dumps(asdict(self), default=str, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> Self:
        """Parse trusted-root journal data, rejecting unsupported schemas."""
        data = json.loads(text)
        if (
            not isinstance(data, dict)
            or type(data.get("schema_version")) is not int
            or data.get("schema_version") != 1
        ):
            raise ValueError("Unsupported journal schema")
        operations = []
        for raw in data["ordered_operations"]:
            for name in ("destination", "staged_path", "backup_path"):
                if raw[name] is not None:
                    raw[name] = Path(raw[name])
            raw["metadata"] = tuple(tuple(item) for item in raw["metadata"])
            operations.append(FileOperation(**raw))
        data["ordered_operations"] = tuple(operations)
        for name in ("completed_steps", "retained_originals", "timestamps"):
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
