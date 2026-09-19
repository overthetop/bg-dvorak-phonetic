"""Internal Linux worker: fixed operations and destinations, never an arbitrary plan API."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

# Isolated Python execution deliberately does not trust PYTHONPATH or caller cwd.
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bg_dvorak_phonetic.diagnostics import InstallerError  # noqa: E402
from bg_dvorak_phonetic.models import validate_id  # noqa: E402
from bg_dvorak_phonetic.workflow import inventory, project_root  # noqa: E402


def validate_request(request: dict[str, object]) -> None:
    """Validate a small versioned request against the worker's own checkout assets."""
    allowed = {"schema_version", "action", "source_hashes", "observed_hashes", "run_id", "dry_run"}
    if (
        set(request) - allowed
        or type(request.get("schema_version")) is not int
        or request.get("schema_version") != 1
    ):
        raise InstallerError("Invalid worker request schema", 4)
    if request.get("action") not in ("inspect", "apply", "recover"):
        raise InstallerError("Invalid worker operation", 4)
    if request.get("source_hashes") != dict(inventory(project_root()).manifest):
        raise InstallerError("Worker source hashes changed", 4)
    if "dry_run" in request and type(request["dry_run"]) is not bool:
        raise InstallerError("Invalid preview flag", 4)
    if request.get("action") in ("recover", "apply"):
        try:
            validate_id(str(request.get("run_id", "")))
        except ValueError as exc:
            raise InstallerError("Invalid recovery ID", 4) from exc


def worker_command(*, interactive: bool) -> list[str]:
    """Use isolated Python and fixed worker path; never elevate uv or dependency setup."""
    sudo = ["sudo"] if interactive else ["sudo", "-n"]
    return [*sudo, "--", str(Path(sys.executable).absolute()), "-I", str(Path(__file__).resolve())]


def invoke(request: dict[str, object], *, interactive: bool) -> dict[str, object]:
    """Request authorized work, preserving the worker's classified failure code."""
    validate_request(request)
    try:
        result = subprocess.run(
            worker_command(interactive=interactive),
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (KeyboardInterrupt, subprocess.TimeoutExpired) as exc:
        if request["action"] != "inspect":
            raise InstallerError(
                "Worker interrupted; mutation outcome is unknown",
                5,
                path=Path("/var/lib/bg-dvorak-phonetic"),
                remedy="Inspect protected journals and recover before retrying.",
            ) from exc
        if isinstance(exc, KeyboardInterrupt):
            raise
        raise InstallerError("Protected inspection timed out; inspection is incomplete", 3) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise InstallerError(
            "Authorization unavailable; inspection is incomplete",
            3,
            remedy="Retry with terminal access and sudo authorization.",
        ) from exc
    try:
        response = json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        if request["action"] != "inspect" and not result.stderr.lstrip().startswith("sudo:"):
            raise InstallerError(
                "Worker ended without a known mutation outcome",
                5,
                path=Path("/var/lib/bg-dvorak-phonetic"),
                remedy="Inspect journals and recover before retrying.",
            ) from exc
        raise InstallerError(
            "Authorization denied or worker unavailable; inspection is incomplete",
            3,
            remedy="Check sudo access and retry; no clean state has been established.",
        ) from exc
    if not isinstance(response, dict):
        raise InstallerError("Invalid worker response", 4)
    if result.returncode:
        raise InstallerError(
            str(response.get("error", "Worker failed")),
            int(response.get("code", 3)),
            remedy=str(response.get("remedy", "Inspect state and retry.")),
            path=Path(str(response["path"])) if response.get("path") else None,
        )
    return cast(dict[str, object], response)


class LinuxRecoveryAccess:
    """Linux-only authorization transport kept outside shared workflow policy."""

    requires_authorization = True

    def __init__(self, source_hashes: tuple[tuple[str, str], ...]) -> None:
        self.source_hashes = source_hashes

    def _request(self, action: str, **extra: object) -> dict[str, object]:
        return invoke(
            {
                "schema_version": 1,
                "action": action,
                "source_hashes": dict(self.source_hashes),
                **extra,
            },
            interactive=sys.stdin.isatty(),
        )

    def pending(self) -> tuple[str, ...]:
        response = self._request("inspect")
        pending = response.get("pending")
        if not isinstance(pending, list) or not all(isinstance(item, str) for item in pending):
            raise InstallerError("Invalid protected inspection response", 4)
        return tuple(pending)

    def restore(self, run_id: str, *, dry_run: bool = False) -> None:
        self._request("recover", run_id=run_id, dry_run=dry_run)


def worker_main() -> int:
    """Dispatch fixed Linux operations; only adapters build filesystem change plans."""
    from dataclasses import replace

    from bg_dvorak_phonetic.platforms import get_adapter
    from bg_dvorak_phonetic.transaction import Transaction

    try:
        if sys.platform != "linux" or os.geteuid() != 0:
            raise InstallerError("Worker requires authorized Linux system scope", 3)
        raw = sys.stdin.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise InstallerError("Worker request too large", 4)
        request = json.loads(raw)
        if not isinstance(request, dict):
            raise InstallerError("Invalid worker request", 4)
        validate_request(request)
        adapter = get_adapter("linux")
        context = adapter.probe("system")
        engine = Transaction()
        action = request["action"]
        if action == "inspect":
            print(json.dumps({"pending": engine.pending(context)}))
            return 0
        if action == "recover":
            engine.restore(context, request["run_id"], dry_run=bool(request.get("dry_run", False)))
            print(json.dumps({"restored": not request.get("dry_run", False)}))
            return 0
        assets = inventory(project_root())
        if dict(assets.manifest) != request["source_hashes"]:
            raise InstallerError("Source changed during worker planning", 4)
        adapter.validate_assets(context, assets)
        state = adapter.inspect(context)
        plan = adapter.plan(state, assets)
        plan = replace(plan, run_id=request["run_id"])
        if dict(plan.observed_hashes) != request.get("observed_hashes"):
            raise InstallerError(
                "Worker snapshot differs from authorized plan",
                4,
                remedy="Inspect and authorize a fresh plan.",
            )
        engine.apply(context, plan, lambda: adapter.verify_installed(context, assets))
        print(json.dumps({"run_id": plan.run_id, "action": plan.action.value}))
        return 0
    except InstallerError as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "code": exc.code,
                    "remedy": exc.remedy,
                    "path": str(exc.path) if exc.path is not None else None,
                }
            )
        )
        return exc.code
    except KeyboardInterrupt:
        print(
            json.dumps({"error": "Interrupted; restoration completed or no mutation", "code": 130})
        )
        return 130
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(
            json.dumps(
                {
                    "error": f"Worker failed: {exc}",
                    "code": 1,
                    "remedy": "Inspect the scoped recovery state before retrying.",
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(worker_main())
