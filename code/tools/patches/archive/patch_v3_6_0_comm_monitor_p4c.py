#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p4c.py

Patch 4c: .github/workflows/check.yml に v3.6.0 の新テスト 2 ファイルを追加。
"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
REPO = CODE.parent   # .github はリポジトリ直下（code/ の 1 つ上）


def patch_check_yml() -> bool:
    p = REPO / ".github" / "workflows" / "check.yml"
    if not p.exists():
        print(f"  [error] not found: {p}")
        return False

    text = p.read_text(encoding="utf-8")

    if "test_v3_6_0_comm_monitor_generator" in text:
        print("  [skip ] check.yml already has v3.6.0 comm_monitor tests")
        return True

    anchor = (
        "coverage run --parallel-mode "
        "tests/test_v3_5_3_eclipse_installer_deep.py"
    )
    if anchor not in text:
        print(f"  [error] anchor not found: {anchor}")
        return False

    lines = text.split("\n")
    inserted = False
    for i, line in enumerate(lines):
        if anchor in line:
            indent = line[: len(line) - len(line.lstrip())]
            new_lines = [
                line,
                f"{indent}coverage run --parallel-mode "
                f"tests/test_v3_6_0_comm_monitor_generator.py",
                f"{indent}coverage run --parallel-mode "
                f"tests/test_v3_6_0_comm_monitor_integration.py",
            ]
            lines = lines[:i] + new_lines + lines[i + 1:]
            inserted = True
            break

    if not inserted:
        print("  [error] could not insert lines")
        return False

    bak = p.with_suffix(p.suffix + ".bak_p4c")
    bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    p.write_text("\n".join(lines), encoding="utf-8")
    print("  [write ] .github/workflows/check.yml (2 lines added)")
    return True


def verify() -> None:
    p = REPO / ".github" / "workflows" / "check.yml"
    text = p.read_text(encoding="utf-8")
    for i, line in enumerate(text.split("\n"), 1):
        if "test_v3_6_0_comm_monitor" in line:
            print(f"  line {i}: {line.strip()}")


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p4c ===")
    print(f"repo: {REPO}")
    print(f"code: {CODE}")

    if not patch_check_yml():
        return 1

    print("--- verify ---")
    verify()

    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())