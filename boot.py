from pathlib import Path
import py_compile
import sys


def _has_merge_markers(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "<<<<<<<" in text or "=======" in text or ">>>>>>>" in text


def _syntax_ok(path: Path) -> bool:
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except py_compile.PyCompileError as exc:
        print("FATAL: main.py has a syntax/indentation error.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return False


def main() -> None:
    target = Path(__file__).with_name("main.py")
    if _has_merge_markers(target):
        print(
            "FATAL: unresolved git merge markers found in main.py. "
            "Please deploy a clean commit.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if not _syntax_ok(target):
        raise SystemExit(1)

    from main import main as run_main

    run_main()


if __name__ == "__main__":
    main()
