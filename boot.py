import os
import sys
from pathlib import Path
import runpy

def file_has_real_merge_markers(path: str) -> bool:
    p = Path(path)
    if not p.exists():
        return False

    text = p.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("<<<<<<<") or s.startswith(">>>>>>>"):
            return True
    return False

def main() -> None:
    print("BOOT CWD:", os.getcwd())
    print("BOOT main.py path:", str(Path("main.py").resolve()))

    if file_has_real_merge_markers("main.py"):
        print("FATAL: unresolved git merge markers found in main.py")
        sys.exit(1)

    runpy.run_path("main.py", run_name="__main__")

if __name__ == "__main__":
    main()
