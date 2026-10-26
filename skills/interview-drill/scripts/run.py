#!/usr/bin/env python3
"""Run the hidden test suite for one practice problem.

Usage:
  python3 .tests/run.py p3            # full suite (this is "submit")
  python3 .tests/run.py p3 --sample   # only the sample cases (the OA "Run" button)

Layout (created by `init_workspace.py`, filled in by the skill when it generates a problem):
  <workspace>/p3_two_sum.py           the user's file: a bare stub, they write everything
  <workspace>/.tests/cases/p3.py      the hidden suite

A cases file defines:
  FUNC = "two_sum"                    required: the function (or class) name the stub asks for
  CASES = [((args...), expected), …]  required: positional args tuple + expected value
  SAMPLES = 2                         optional: how many leading CASES count as samples
  TIMEOUT = 2                         optional: seconds per case
  def check(args, got) -> bool        optional: for problems with more than one right answer
  def drive(target, args)             optional: build inputs / drive a class (trees, LRU, ...)
  def normalize(x)                    optional: applied to both got and expected before ==
"""
import copy, datetime, importlib.util, json, pathlib, signal, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_path(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def save_result(key, path, passed, total):
    """log_attempt.py reads this, so the logged score is never hand-copied."""
    (ROOT / ".tests" / "last_result.json").write_text(json.dumps(
        {"id": key, "passed": passed, "total": total, "file_mtime": path.stat().st_mtime,
         "at": datetime.datetime.now().isoformat(timespec="seconds")}))


def short(x, n=120):
    s = repr(x)
    return s if len(s) <= n else s[:n] + "…"


def _alarm(signum, frame):
    raise TimeoutError


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    key = sys.argv[1].lower()
    sample_only = "--sample" in sys.argv[2:]

    files = sorted(ROOT.glob(f"{key}_*.py"))
    if not files:
        sys.exit(f"no problem file matching {key}_*.py in {ROOT}")
    cases_path = ROOT / ".tests" / "cases" / f"{key}.py"
    if not cases_path.exists():
        sys.exit(f"no test suite at {cases_path}")

    suite = load_path(cases_path, f"cases_{key}")
    try:
        user = load_path(files[0], files[0].stem)
    except BaseException as e:          # SyntaxError, EOFError from input(), SystemExit, ...
        save_result(key, files[0], 0, len(suite.CASES))
        sys.exit(f"{files[0].name} does not import: {type(e).__name__}: {e}\n0/{len(suite.CASES)}")

    target = getattr(user, suite.FUNC, None)
    if target is None:
        save_result(key, files[0], 0, len(suite.CASES))
        sys.exit(f"{files[0].name} has no `{suite.FUNC}` (the name the problem asked for)\n0/{len(suite.CASES)}")

    cases = suite.CASES[: getattr(suite, "SAMPLES", 2)] if sample_only else suite.CASES
    check = getattr(suite, "check", None)
    drive = getattr(suite, "drive", None)
    norm = getattr(suite, "normalize", lambda x: x)
    timeout = getattr(suite, "TIMEOUT", 2)
    signal.signal(signal.SIGALRM, _alarm)

    passed = 0
    for i, (args, expected) in enumerate(cases, 1):
        call_args = copy.deepcopy(args)
        signal.alarm(timeout)
        try:
            got = drive(target, call_args) if drive else target(*call_args)
            ok = check(copy.deepcopy(args), got) if check else norm(got) == norm(expected)
            verdict = "PASS" if ok else "FAIL"
        except TimeoutError:
            got, ok, verdict = None, False, f"TIMEOUT (>{timeout}s)"
        except Exception as e:
            got, ok, verdict = None, False, f"ERROR {type(e).__name__}: {e}"
        finally:
            signal.alarm(0)
        passed += ok
        line = f"  case {i:>2}: {verdict}"
        if not ok:
            line += f"\n           input:    {short(args)}"
            line += f"\n           expected: {short(expected)}" if not check else ""
            line += f"\n           got:      {short(got)}" if got is not None else ""
        print(line)

    label = "sample" if sample_only else "full suite"
    print(f"\n{files[0].name}: {passed}/{len(cases)} ({label})")
    if not sample_only:
        save_result(key, files[0], passed, len(cases))
    sys.exit(0 if passed == len(cases) else 1)


if __name__ == "__main__":
    main()
