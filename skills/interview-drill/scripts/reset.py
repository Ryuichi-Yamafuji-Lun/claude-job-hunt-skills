#!/usr/bin/env python3
"""Archive an attempt and restore the bare stub, so a re-do measures recall, not reading.

Usage:  python3 .tests/reset.py p3

The previous attempt is copied to .archive/<file>.<timestamp>.py and never deleted:
diffing today's attempt against last week's is the most useful thing the log can show.
The stub comes from .tests/stubs/<file>, which the skill writes when it creates the problem.
"""
import datetime, pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    key = sys.argv[1].lower()
    files = sorted(ROOT.glob(f"{key}_*.py"))
    if not files:
        sys.exit(f"no problem file matching {key}_*.py")
    f = files[0]
    stub = ROOT / ".tests" / "stubs" / f.name
    if not stub.exists():
        sys.exit(f"no stored stub at {stub}; refusing to reset without one")

    archive = ROOT / ".archive"
    archive.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = archive / f"{f.stem}.{stamp}.py"
    shutil.copy2(f, dest)
    shutil.copy2(stub, f)
    print(f"archived previous attempt -> {dest.relative_to(ROOT)}")
    print(f"reset {f.name} to the bare stub")


if __name__ == "__main__":
    main()
