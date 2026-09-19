#!/usr/bin/env python3
"""Compare output_gui/ vs output/ file-by-file, ignoring @date lines."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUI_DIR = ROOT / "output_gui"
TEST_DIR = ROOT / "output_test"

DATE_RE = re.compile(r'@date\s+[\d\-: ]+')


def normalize(text):
    """Ignore @date lines and trailing whitespace."""
    lines = []
    for line in text.splitlines():
        line = DATE_RE.sub('@date <IGNORED>', line)
        lines.append(line.rstrip())
    return '\n'.join(lines)


def list_files(d):
    return {f.relative_to(d).as_posix(): f
            for f in d.rglob('*') if f.is_file()}


def main():
    if not GUI_DIR.exists():
        print(f"NG: {GUI_DIR} does not exist")
        print("    → run GUI code generation first")
        return 1
    if not TEST_DIR.exists():
        print(f"NG: {TEST_DIR} does not exist")
        return 1

    gui_files = list_files(GUI_DIR)
    test_files = list_files(TEST_DIR)

    print(f"GUI files:  {len(gui_files)}")
    print(f"Test files: {len(test_files)}")
    print()

    all_names = sorted(set(gui_files) | set(test_files))
    only_gui = sorted(set(gui_files) - set(test_files))
    only_test = sorted(set(test_files) - set(gui_files))
    common = sorted(set(gui_files) & set(test_files))

    if only_gui:
        print(f"[Only in GUI] {len(only_gui)}")
        for n in only_gui:
            print(f"  + {n}")
    if only_test:
        print(f"[Only in Test] {len(only_test)}")
        for n in only_test:
            print(f"  - {n}")

    print()
    diff_count = 0
    for name in common:
        gui_text = gui_files[name].read_text(encoding='utf-8', errors='replace')
        test_text = test_files[name].read_text(encoding='utf-8', errors='replace')
        if normalize(gui_text) != normalize(test_text):
            diff_count += 1
            print(f"[DIFF] {name}")
            # Show first differing line
            g_lines = normalize(gui_text).splitlines()
            t_lines = normalize(test_text).splitlines()
            for i, (g, t) in enumerate(zip(g_lines, t_lines)):
                if g != t:
                    print(f"  line {i+1}:")
                    print(f"    GUI : {g[:90]}")
                    print(f"    Test: {t[:90]}")
                    break
            else:
                if len(g_lines) != len(t_lines):
                    print(f"  line count differs: "
                          f"GUI={len(g_lines)} Test={len(t_lines)}")

    print()
    print("=" * 60)
    if diff_count == 0 and not only_gui and not only_test:
        print("  RESULT: identical (24/24 files match)")
        return 0
    else:
        print(f"  RESULT: {diff_count} diff(s) among common files")
        if only_gui:
            print(f"          {len(only_gui)} only-in-GUI")
        if only_test:
            print(f"          {len(only_test)} only-in-test")
        return 1


if __name__ == "__main__":
    sys.exit(main())