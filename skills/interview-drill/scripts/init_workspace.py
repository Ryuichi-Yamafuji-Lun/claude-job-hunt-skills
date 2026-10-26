#!/usr/bin/env python3
"""Create the practice workspace the interview-drill skill writes problems into.

Usage:  init_workspace.py [path]      (default: ~/interview-practice)

Idempotent: re-running refreshes the runner scripts and never touches problem files,
the hidden suites, stubs, or the archive.
"""
import json, pathlib, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent

README = """# Interview practice workspace

Problems appear here as `pN_<slug>.py` (measured) or `sN_<slug>.py` (study / guided).
Each file is a bare stub: the problem name and the function name the tests call.
You write the imports, the signature, and everything else.

House rules for a mock: AI autocomplete off, no looking anything up, talk out loud,
and don't run the code until the interviewer says so.

Don't open `.tests/`; it holds the hidden suites and reference answers.
"""

VSCODE = {
    "files.autoSave": "onFocusChange",
    "editor.inlineSuggest.enabled": False,
    "github.copilot.enable": {"*": False},
    "files.exclude": {".tests": True, ".archive": True, "**/__pycache__": True},
}


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "~/interview-practice").expanduser()
    for d in (root, root / ".tests" / "cases", root / ".tests" / "stubs", root / ".archive", root / ".vscode"):
        d.mkdir(parents=True, exist_ok=True)
    for name in ("run.py", "reset.py"):
        shutil.copy2(HERE / name, root / ".tests" / name)
    if not (root / "README.md").exists():
        (root / "README.md").write_text(README)
    settings = root / ".vscode" / "settings.json"
    if not settings.exists():
        settings.write_text(json.dumps(VSCODE, indent=2) + "\n")
    print(f"workspace ready: {root}")


if __name__ == "__main__":
    main()
