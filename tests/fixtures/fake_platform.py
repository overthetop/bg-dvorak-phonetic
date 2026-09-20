"""Test-only adapter proving extension; this is not Windows implementation."""

from pathlib import Path

from bg_dvorak_phonetic.models import (
    Action,
    ChangePlan,
    FileOperation,
    Health,
    InstallationState,
    PlatformContext,
)
from bg_dvorak_phonetic.transaction import scope_lock
from bg_dvorak_phonetic.workflow import digest


class FakeAdapter:
    def __init__(self, root: Path, destination: Path):
        self.root = root
        self.destination = destination
        self.source = root / "fake-layout"
        self.source.write_bytes(b"initial")
        self.target = destination / "layout"
        self.context = None
        self.last = None

    def recovery_access(self, context, assets):
        from bg_dvorak_phonetic.transaction import LocalRecoveryAccess

        return LocalRecoveryAccess(context)

    def probe(self, requested_scope):
        self.context = PlatformContext(
            "fake",
            "1",
            "fixture",
            "none",
            "user",
            self.root,
            (self.destination,),
            self.destination.parent / "fake-state",
        )
        return self.context

    def validate_assets(self, context, assets):
        assert self.source.is_file()
        return ("fake-source",)

    def inspect(self, context):
        actual = digest(self.target)
        expected = digest(self.source)
        health = (
            Health.ABSENT
            if actual is None
            else Health.CURRENT
            if actual == expected
            else Health.OUTDATED
            if actual == self.last
            else Health.REPAIRABLE
        )
        return InstallationState(health)

    def plan(self, state, assets):
        action = {
            Health.ABSENT: Action.INSTALL,
            Health.CURRENT: Action.NOOP,
            Health.OUTDATED: Action.UPDATE,
            Health.REPAIRABLE: Action.REPAIR,
        }[state.health]
        operations = (
            ()
            if action == Action.NOOP
            else (
                FileOperation(
                    "replace" if self.target.exists() else "create",
                    self.target,
                    digest(self.target),
                    digest(self.source),
                    self.source,
                ),
            )
        )
        return ChangePlan("fake", "user", action, operations)

    def validate_staged(self, context, staged):
        return ("fake-staged",)

    def acquire_lock(self, context):
        return scope_lock(context)

    def apply_authorized(self, context, plan, engine):
        engine.apply(context, plan, lambda: self.verify_installed(context, None))
        self.last = digest(self.target)

    def verify_installed(self, context, assets):
        assert digest(self.target) == digest(self.source)

    def activation_guidance(self, context, result):
        return ("Test adapter only; no keyboard activation.",)
