from pathlib import Path
import sys


def _has_merge_markers(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "<<<<<<<" in text or "=======" in text or ">>>>>>>" in text


def main() -> None:
    target = Path(__file__).with_name("main.py")
    if _has_merge_markers(target):
        print(
            "FATAL: unresolved git merge markers found in main.py. "
            "Please deploy a clean commit.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    from main import main as run_main

    run_main()


if __name__ == "__main__":
    main()
