"""v3.4.1: bump README suite count 44->45, PASS 1642->1649."""
from __future__ import annotations
import sys
from pathlib import Path

README = (Path(__file__).resolve().parent.parent.parent.parent / "README.md")


def main() -> int:
    if not README.exists():
        print(f"[ERR] {README} not found")
        return 1
    text = README.read_text(encoding="utf-8")

    if "1649" in text and "1642" not in text:
        print("[SKIP] README already at 1649 / 45 suites")
        return 0

    orig = text

    # PASS count
    text = text.replace("1642%20PASS", "1649%20PASS")
    text = text.replace("1642 PASS", "1649 PASS")

    # Suite count (multiple contexts)
    text = text.replace("across 44 suites", "across 45 suites")
    text = text.replace("**44 test suites", "**45 test suites")
    text = text.replace("(44 suites,", "(45 suites,")
    text = text.replace("All 44 suites should pass",
                        "All 45 suites should pass")

    if text == orig:
        print("[WARN] no changes applied — check current values")
        print("       Search README for '1642' or '44 suites' manually.")
        return 1

    README.write_text(text, encoding="utf-8", newline="\n")
    print("[OK]   README.md updated: 1642 -> 1649, 44 -> 45 suites")
    return 0


if __name__ == "__main__":
    sys.exit(main())