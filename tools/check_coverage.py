"""Gate a complete native aggregate using exact line counts, never rounded percentages."""

import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    try:
        if len(args) != 1:
            raise ValueError("Expected one combined coverage JSON path")
        totals = json.loads(Path(args[0]).read_text(encoding="utf-8"))["totals"]
        covered, statements = totals["covered_lines"], totals["num_statements"]
        if type(covered) is not int or type(statements) is not int:
            raise ValueError("Line counts must be integers")
        if statements <= 0 or not 0 <= covered <= statements:
            raise ValueError("Invalid or empty line counts")
        passed = covered * 100 > statements * 80
        print(f"Lines: {covered}/{statements}; strict >80%: {'PASS' if passed else 'FAIL'}")
        return 0 if passed else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Coverage gate failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
