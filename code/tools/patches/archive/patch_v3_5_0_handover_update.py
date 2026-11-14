"""v3.5.0: update HANDOVER_v3_5_0.md (S-4 + S-5)."""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DOC = REPO / "code" / "docs" / "HANDOVER_v3_5_0.md"


REPLACEMENTS: list[tuple[str, str]] = []

# --- 1) 最新コミット header + list ---
REPLACEMENTS.append((
    "### 最新コミット (CI green 3 連続)\n"
    "\n"
    "- `76cd6c2` ci(v3.5.0): pin all jobs to ubuntu-24.04 (S-3 Step 1)\n"
    "- `3cd1b45` feat(v3.5.0): add mypy foundation (Phase 1a, informational)\n"
    "- `a203daa` feat(v3.5.0): expand frozen exe smoke tests to 4 levels\n",
    "### 最新コミット (CI green 7 連続)\n"
    "\n"
    "- `29cf425` ci(v3.5.0): update GitHub Actions to Node.js 24 versions (S-5)\n"
    "- `1825170` fix(ci): add tomli fallback for Python 3.10 (S-4)\n"
    "- `6c39a34` ci(v3.5.0): add Python matrix (3.10-3.13) + coverage (S-4)\n"
    "- `f11fea1` docs(v3.5.0): add HANDOVER_v3_5_0.md (development status)\n"
    "- `76cd6c2` ci(v3.5.0): pin all jobs to ubuntu-24.04 (S-3 Step 1)\n"
    "- `3cd1b45` feat(v3.5.0): add mypy foundation (Phase 1a, informational)\n"
    "- `a203daa` feat(v3.5.0): expand frozen exe smoke tests to 4 levels\n",
))

# --- 2) 品質状態 ---
REPLACEMENTS.append((
    "- **CI: 完全 green (8 ジョブ全て成功)**\n"
    "  - 新規: `mypy-check` (informational), 13s\n"
    "- **テスト: 46 suites / 1657 PASS / 0 FAIL**\n",
    "- **CI: 完全 green (11 ジョブ全て成功)**\n"
    "  - Unit tests は **Python 3.10 / 3.11 / 3.12 / 3.13** の 4 matrix\n"
    "  - `mypy-check` (informational)\n"
    "- **テスト: 46 suites / 1657 PASS / 0 FAIL (py3.10-3.13 全て)**\n"
    "- **coverage: htmlcov を artifact 化 (matrix 毎に 4 種)**\n",
))

# --- 3) S-3 Step 1 の後に S-4 / S-5 を追加 ---
OLD_S3 = (
    "### S-3 Step 1: ubuntu-24.04 ピン留め (commit 76cd6c2)\n"
    "\n"
    "- 全 8 ジョブの `runs-on: ubuntu-latest` -> `runs-on: ubuntu-24.04`\n"
    "- 背景: ubuntu-latest が 2026-10-19〜2026-11-19 で Ubuntu 26.04 に移行\n"
    "- 移行期間中の予期せぬ自動切替を防止\n"
)
NEW_S3 = (
    OLD_S3
    + "\n"
    + "### S-4: Python matrix + coverage (commit 6c39a34, fix 1825170)\n"
    + "\n"
    + "- `tests` ジョブを Python 3.10 / 3.11 / 3.12 / 3.13 の 4 matrix に\n"
    + "  - `fail-fast: false` で 1 つ落ちても他は継続\n"
    + "- 各テストスイートを `coverage run --parallel-mode` でラップ\n"
    + "  - `test_v3_5_s1_smoke.py` は `os._exit(0)` のため除外（coverage の atexit が走らない）\n"
    + "- `coverage combine` + `coverage report` + `coverage html` を実行\n"
    + "- `coverage-py3.1x` として HTML を artifact 化\n"
    + "- `code/.coveragerc` 追加、`pyproject.toml` に `coverage>=7.0`\n"
    + "- Python 3.10 の `tomllib` 不在対応:\n"
    + "  - 4 テストファイルに `try: import tomllib / except: import tomli`\n"
    + "  - `pyproject.toml` に `tomli>=2.0; python_version < '3.11'`\n"
    + "  - `check.yml` の install に `tomli` 追加\n"
    + "\n"
    + "### S-5: GitHub Actions Node.js 24 対応 (commit 29cf425)\n"
    + "\n"
    + "- `actions/checkout@v4` -> `v5`（8 箇所）\n"
    + "- `actions/setup-python@v5` -> `v6`（8 箇所）\n"
    + "- `actions/upload-artifact@v4` -> `v5`（5 箇所）\n"
    + "- 効果: Node.js 20 deprecation 警告が 21 件 -> 1 件に削減\n"
    + "  - 残る 1 件は `upload-artifact@v5` 側の問題（GitHub 側の対応待ち）\n"
)
REPLACEMENTS.append((OLD_S3, NEW_S3))

# --- 4) コミット履歴 ---
REPLACEMENTS.append((
    "## v3.5.0 コミット履歴\n"
    "\n"
    "- `76cd6c2` ci(v3.5.0): pin all jobs to ubuntu-24.04 (S-3 Step 1)\n"
    "- `3cd1b45` feat(v3.5.0): add mypy foundation (Phase 1a, informational)\n"
    "- `a203daa` feat(v3.5.0): expand frozen exe smoke tests to 4 levels\n",
    "## v3.5.0 コミット履歴\n"
    "\n"
    "- `29cf425` ci(v3.5.0): update GitHub Actions to Node.js 24 versions (S-5)\n"
    "- `1825170` fix(ci): add tomli fallback for Python 3.10 (S-4)\n"
    "- `6c39a34` ci(v3.5.0): add Python matrix (3.10-3.13) + coverage (S-4)\n"
    "- `f11fea1` docs(v3.5.0): add HANDOVER_v3_5_0.md (development status)\n"
    "- `76cd6c2` ci(v3.5.0): pin all jobs to ubuntu-24.04 (S-3 Step 1)\n"
    "- `3cd1b45` feat(v3.5.0): add mypy foundation (Phase 1a, informational)\n"
    "- `a203daa` feat(v3.5.0): expand frozen exe smoke tests to 4 levels\n",
))

# --- 5) 次期開発の候補 (優先度 S の更新) ---
REPLACEMENTS.append((
    "### 優先度 S\n"
    "\n"
    "1. **v3.5.0 続行**\n"
    "   - Phase 1b: `CodeTemplates` の型問題解消 (~150 errors 削減)\n"
    "   - Phase 1c: `Optional[X]` -> `X | None` 統一 (88 箇所)\n"
    "   - S-3 Step 2: ubuntu-26.04 preview ジョブ追加 (**10/19 以降**)\n",
    "### 優先度 S\n"
    "\n"
    "1. **v3.5.0 続行**\n"
    "   - Phase 1b: `CodeTemplates` の型問題解消 (~150 errors 削減)\n"
    "   - Phase 1c: `Optional[X]` -> `X | None` 統一 (88 箇所)\n"
    "   - S-3 Step 2: ubuntu-26.04 preview ジョブ追加 (**10/19 以降**)\n"
    "   - 完了済み: S-4 (matrix + coverage), S-5 (Node.js 24 対応)\n",
))


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_0_handover_update")
    print("=" * 70)
    txt = DOC.read_text(encoding="utf-8")
    for i, (old, new) in enumerate(REPLACEMENTS, 1):
        if old not in txt:
            print(f"  [FAIL] replacement #{i}: pattern not found")
            print("----- expected (first 200 chars) -----")
            print(repr(old[:200]))
            sys.exit(1)
        txt = txt.replace(old, new, 1)
        print(f"  applied #{i}")
    DOC.write_text(txt, encoding="utf-8")
    print()
    print(f"[OK] wrote {DOC.relative_to(REPO)} ({len(txt)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())