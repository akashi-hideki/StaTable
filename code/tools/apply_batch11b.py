# apply_batch11b.py - Final pass: 7 residual Japanese tags in f-strings
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPLACEMENTS = [
    ("型 '", "Type '"),
    ("メンバ '", "Member '"),
    ("基準タイマ '", "Base timer '"),
    ("層数:", "Layers:"),
    ("一時Variable:", "Temp variable:"),
    ("リテラル '", "Literal '"),
]


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = PROJECT_ROOT / ("_backup_" + ts)
    backup.mkdir()
    print("Backup: " + str(backup))

    total_files = 0
    total_repl = 0
    for d in ["statable", "statable_gui", "codegen"]:
        root = PROJECT_ROOT / d
        if not root.exists():
            continue
        for f in root.rglob("*.py"):
            src = f.read_text(encoding="utf-8")
            orig = src
            n = 0
            for ja, en in REPLACEMENTS:
                cnt = src.count(ja)
                if cnt:
                    src = src.replace(ja, en)
                    n += cnt
            if src != orig:
                rel = f.relative_to(PROJECT_ROOT)
                bp = backup / rel
                bp.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, bp)
                f.write_text(src, encoding="utf-8")
                print("[CHG] " + str(rel) + ": " + str(n) + " replacements")
                total_files += 1
                total_repl += n

    print("")
    print("Changed: " + str(total_files) + " files, total replacements: "
          + str(total_repl))


if __name__ == "__main__":
    main()