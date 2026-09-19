"""Public CLI: explicit scopes, read-only previews and classified failures."""

import argparse
import sys
import traceback
from collections.abc import Sequence

from bg_dvorak_phonetic import __version__
from bg_dvorak_phonetic.diagnostics import Diagnostics, InstallerError, redact
from bg_dvorak_phonetic.platforms import get_adapter
from bg_dvorak_phonetic.workflow import execute, project_root, verify_environment


def main(argv: Sequence[str] | None = None) -> int:
    """Run one command; help/version never request privileges or alter OS state."""
    args_list = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description="Install the Bulgarian Dvorak phonetic layout")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("install", "status", "recover"):
        sub = commands.add_parser(name)
        if name == "recover":
            sub.add_argument("run_id")
        sub.add_argument("--scope", choices=("user", "system"))
        sub.add_argument("--dry-run", action="store_true")
        sub.add_argument("--yes", action="store_true")
        sub.add_argument("--verbose", action="store_true")
    if not args_list or (
        args_list[0].startswith("-") and args_list[0] not in ("-h", "--help", "--version")
    ):
        args_list.insert(0, "install")
    args = parser.parse_args(args_list)
    events = Diagnostics()
    try:
        verify_environment(project_root())
        platform_id = {"linux": "linux", "darwin": "macos"}.get(sys.platform)
        if platform_id is None:
            raise InstallerError("Unsupported operating system", 2)
        adapter = get_adapter(platform_id)
        scope = args.scope
        if platform_id == "linux" and args.command == "status" and scope is None:
            scope = "system"
        context = adapter.probe(scope)
        result = execute(
            adapter,
            context,
            command=args.command,
            dry_run=args.dry_run,
            yes=args.yes,
            recovery_id=getattr(args, "run_id", None),
            diagnostics=events,
        )
        print(
            f"action={result.action} health={result.installation_status} "
            f"activation={result.activation_status}"
        )
        for path in result.changed_paths:
            print(f"changed={path}")
        if result.recovery_id:
            print(
                f"recovery={result.recovery_id} location={context.state_root / result.recovery_id}"
            )
        for message in (*result.warnings, *result.next_steps):
            print(message)
        return result.exit_code
    except InstallerError as exc:
        events.error(exc)
        if args.verbose:
            print(redact("".join(traceback.format_exception(exc))), file=sys.stderr)
        return exc.code
    except KeyboardInterrupt:
        events.error(
            InstallerError(
                "Interrupted before mutation or after restoration", 130, remedy="Retry when ready."
            )
        )
        return 130
    except (OSError, ValueError) as exc:
        events.error(
            InstallerError(
                str(exc), remedy="Inspect prerequisites and recovery state before retrying."
            )
        )
        if args.verbose:
            print(redact("".join(traceback.format_exception(exc))), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
