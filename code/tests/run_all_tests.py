# tests/run_all_tests.py
"""
StaTable 全テスト一括実行ランナー

全テストファイルをサブプロセスで順次実行し、結果を 1 画面に集約する。

使い方:
    cd C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code

    python -m tests.run_all_tests                  # 全テスト実行
    python -m tests.run_all_tests --list           # 発見のみ（実行しない）
    python -m tests.run_all_tests --stage 3        # Stage 3 のみ
    python -m tests.run_all_tests --stage 1,2,3    # 複数指定
    python -m tests.run_all_tests --only isr       # 名前部分一致
    python -m tests.run_all_tests --verbose        # 各テストの全出力
    python -m tests.run_all_tests --stop-on-fail   # 失敗で即停止
    python -m tests.run_all_tests --timeout 300    # タイムアウト秒（既定: 180）
    python -m tests.run_all_tests --logdir _logs   # ログ出力先

Exit code: 0 = 全合格, 1 = 失敗あり, 2 = 発見失敗

版: 1.1（2026-09-13）
  - extract_counts() が stderr も参照するよう修正
    （unittest はデフォルトで stderr に出力するため）
"""

import argparse
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# ============================================================
# パス設定
# ============================================================
THIS_DIR = Path(__file__).resolve().parent
CODE_DIR = THIS_DIR.parent


# ============================================================
# テスト定義
# ============================================================
@dataclass
class TestDef:
    module: str           # 'tests.test_xxx'
    filename: str         # 'test_xxx.py'
    category: str         # 'stage1' / 'stage2' / 'stage3' / 'integration' / 'legacy' / 'other'
    label: str            # 表示用短縮名
    expected_count: int   # 想定テスト数（目安、0 = 未定義）


# カテゴリの表示順とラベル
CATEGORY_ORDER = ['stage1', 'stage2', 'stage3', 'integration', 'legacy', 'other']
CATEGORY_LABELS = {
    'stage1':      'Stage 1 (データモデル)',
    'stage2':      'Stage 2 (生成器)',
    'stage3':      'Stage 3 (ISR)',
    'integration': '統合テスト',
    'legacy':      '既存回帰',
    'other':       'その他',
}


# テスト登録簿（明示的に分類）
TEST_REGISTRY: List[TestDef] = [
    # === Stage 1 ===
    TestDef('tests.test_role_function_namespace',
            'test_role_function_namespace.py', 'stage1',
            'namespace (model/lib)', 10),
    TestDef('tests.test_xml_namespace',
            'test_xml_namespace.py', 'stage1',
            'XML namespace 保存/復元', 8),

    # === Stage 2 ===
    TestDef('tests.test_role_function_generator',
            'test_role_function_generator.py', 'stage2',
            'role_function_generator', 89),
    TestDef('tests.test_code_merger_isr',
            'test_code_merger_isr.py', 'stage2',
            'code_merger ISR', 8),
    TestDef('tests.test_role_null_guard',
            'test_role_null_guard.py', 'stage2',
            'NULL ガード', 15),

    # === Stage 3 ===
    TestDef('tests.test_isr_context',
            'test_isr_context.py', 'stage3',
            'ISR コンテキスト', 43),

    # === 統合 ===
    TestDef('tests.test_stage12_integration',
            'test_stage12_integration.py', 'integration',
            'Stage 1+2 統合', 62),

    # === 既存回帰 ===
    TestDef('tests.test_c_code_generator',
            'test_c_code_generator.py', 'legacy',
            'Cコード生成', 30),
    TestDef('tests.test_transition_config',
            'test_transition_config.py', 'legacy',
            '遷移コンフィグ', 12),
    TestDef('tests.test_warning_collector',
            'test_warning_collector.py', 'legacy',
            '警告収集', 15),
    TestDef('tests.test_folder_structure',
            'test_folder_structure.py', 'legacy',
            'フォルダ構成', 20),
    TestDef('tests.test_super_include',
            'test_super_include.py', 'legacy',
            'スーパーインクルード', 21),
    TestDef('tests.test_super_loop',
            'test_super_loop.py', 'legacy',
            'スーパーループ', 39),
    TestDef('tests.test_layer_name',
            'test_layer_name.py', 'legacy',
            'layer_name', 24),
    TestDef('tests.test_multi_layer',
            'test_multi_layer.py', 'legacy',
            '複数層', 16),
    TestDef('tests.test_by_layer',
            'test_by_layer.py', 'legacy',
            'by_layer', 17),
]


# ============================================================
# ユーティリティ
# ============================================================
def discover_extra_tests(registered_filenames: set) -> List[TestDef]:
    """レジストリに未登録の test_*.py を自動検出"""
    extra: List[TestDef] = []
    for path in sorted(THIS_DIR.glob('test_*.py')):
        fname = path.name
        if fname in registered_filenames:
            continue
        module = f'tests.{path.stem}'
        extra.append(TestDef(
            module=module,
            filename=fname,
            category='other',
            label=fname.replace('test_', '').replace('.py', ''),
            expected_count=0,
        ))
    return extra


# ★ 修正: stdout + stderr の両方を対象にする
def extract_counts(
    stdout: str, stderr: str = '',
) -> Tuple[Optional[int], Optional[int]]:
    """
    テスト出力から (pass, fail) 数を抽出

    対応形式:
      - カスタム: "pass=N  fail=N"
      - unittest: "Ran N tests" + "OK" / "FAILED (failures=X, errors=Y)"
        ※ unittest は stderr に出力するため、両方を結合して検索
    """
    combined = (stdout or '') + '\n' + (stderr or '')

    # カスタムランナー形式を優先
    m = re.search(r'pass\s*=\s*(\d+)\s+fail\s*=\s*(\d+)', combined)
    if m:
        return int(m.group(1)), int(m.group(2))

    # unittest 形式
    m_ran = re.search(r'Ran\s+(\d+)\s+tests?', combined)
    if m_ran:
        total = int(m_ran.group(1))
        fail = 0
        m_fail = re.search(
            r'FAILED\s*\(failures=(\d+)(?:,\s*errors=(\d+))?',
            combined,
        )
        if m_fail:
            fail = int(m_fail.group(1))
            if m_fail.group(2):
                fail += int(m_fail.group(2))
        return total - fail, fail

    return None, None


def extract_first_failure(stdout: str, stderr: str) -> str:
    """失敗の最初の行を抽出（NG 表示用）"""
    for src in (stderr, stdout):
        if not src:
            continue
        for line in src.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(('AssertionError', 'Error', 'FAILED')):
                return stripped[:100]
            if 'FAIL:' in stripped:
                return stripped[:100]
    return ''


# ============================================================
# テスト実行
# ============================================================
@dataclass
class TestResult:
    test: TestDef
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    duration: float
    timeout: bool = False
    pass_count: Optional[int] = None
    fail_count: Optional[int] = None

    @property
    def status_mark(self) -> str:
        if self.timeout:
            return '[TO]'
        return '[OK]' if self.ok else '[NG]'


def run_one_test(
    test: TestDef, timeout: int, verbose: bool,
) -> TestResult:
    """1 テストをサブプロセスで実行"""
    cmd = [sys.executable, '-m', test.module]
    start = time.time()

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(CODE_DIR),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
        )
        duration = time.time() - start
        # ★ 修正: stdout と stderr の両方を渡す
        pass_count, fail_count = extract_counts(
            proc.stdout, proc.stderr,
        )
        return TestResult(
            test=test,
            ok=(proc.returncode == 0),
            returncode=proc.returncode,
            stdout=proc.stdout or '',
            stderr=proc.stderr or '',
            duration=duration,
            timeout=False,
            pass_count=pass_count,
            fail_count=fail_count,
        )
    except subprocess.TimeoutExpired as e:
        duration = time.time() - start
        def _decode(x):
            if isinstance(x, bytes):
                return x.decode('utf-8', 'replace')
            return x or ''
        return TestResult(
            test=test,
            ok=False,
            returncode=-1,
            stdout=_decode(e.stdout),
            stderr=f'TIMEOUT after {timeout}s',
            duration=duration,
            timeout=True,
        )


# ============================================================
# レポーター
# ============================================================
class Runner:
    LINE = 72

    def __init__(self, verbose: bool, logdir: Optional[Path]):
        self.verbose = verbose
        self.logdir = logdir
        if logdir:
            logdir.mkdir(parents=True, exist_ok=True)

    def _bar(self, ch: str = '='):
        print(ch * self.LINE)

    # ---- ヘッダ ----
    def header(self, args: argparse.Namespace, n_tests: int):
        self._bar()
        print("  StaTable 全テスト一括実行")
        self._bar()
        print(f"  Python:    {sys.version.split()[0]}")
        print(f"  発見:      {n_tests} テストファイル")
        print(f"  タイムアウト: {args.timeout}s")
        print(f"  フィルタ:  stage={args.stage or 'all'}  "
              f"only={args.only or '-'}")
        self._bar()

    # ---- カテゴリヘッダ ----
    def category_header(self, category: str):
        label = CATEGORY_LABELS.get(category, category)
        print(f"\n[{label}]")

    # ---- 結果行 ----
    def result_line(self, r: TestResult):
        mark = r.status_mark
        name = r.test.filename
        # pass/fail の表示
        if r.pass_count is not None and r.fail_count is not None:
            counts = f"{r.pass_count:>4} pass / {r.fail_count:>3} fail"
        else:
            counts = " " * 20

        # 想定数チェック
        warn = ''
        if (r.pass_count is not None
                and r.test.expected_count > 0
                and r.pass_count != r.test.expected_count):
            warn = (f"  ⚠ 想定 {r.test.expected_count} "
                    f"≠ 実測 {r.pass_count}")

        print(f"  {mark}  {name:<42}  "
              f"{counts}  ({r.duration:5.2f}s){warn}")

        # NG / TO の場合は詳細
        if not r.ok:
            detail = extract_first_failure(r.stdout, r.stderr)
            if detail:
                print(f"         └─ {detail}")
            if self.logdir:
                log_path = self.logdir / f"{r.test.filename}.log"
                self._write_log(log_path, r)
                print(f"         └─ 全出力: {log_path}")

        # verbose 出力
        if self.verbose:
            print("         " + "-" * 60)
            for line in (r.stdout or '').splitlines():
                print(f"         | {line}")
            if r.stderr:
                print("         [stderr]")
                for line in r.stderr.splitlines():
                    print(f"         ! {line}")
            print("         " + "-" * 60)

    def _write_log(self, path: Path, r: TestResult):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# {r.test.module}\n")
            f.write(f"# returncode={r.returncode}\n")
            f.write(f"# duration={r.duration:.2f}s\n")
            f.write("\n===== STDOUT =====\n")
            f.write(r.stdout or '')
            f.write("\n===== STDERR =====\n")
            f.write(r.stderr or '')

    # ---- サマリ ----
    def summary(self, results: List[TestResult]) -> bool:
        print()
        self._bar()
        print("  サマリ")
        self._bar()

        # カテゴリ別集計
        by_cat = {}
        for r in results:
            c = r.test.category
            d = by_cat.setdefault(c, {
                'total': 0, 'ok': 0, 'ng': 0,
                'pass': 0, 'fail': 0, 'time': 0.0,
            })
            d['total'] += 1
            d['time'] += r.duration
            if r.ok:
                d['ok'] += 1
            else:
                d['ng'] += 1
            if r.pass_count is not None:
                d['pass'] += r.pass_count
            if r.fail_count is not None:
                d['fail'] += r.fail_count

        # ヘッダ行
        print(f"  {'カテゴリ':<22}  {'実行':>4}  {'合格':>4}  "
              f"{'失敗':>4}  {'pass':>5}  {'fail':>5}  {'時間':>7}")
        print("  " + "-" * 68)

        total = {'total': 0, 'ok': 0, 'ng': 0,
                 'pass': 0, 'fail': 0, 'time': 0.0}

        for cat in CATEGORY_ORDER:
            if cat not in by_cat:
                continue
            d = by_cat[cat]
            label = CATEGORY_LABELS.get(cat, cat)
            print(f"  {label:<22}  {d['total']:>4}  {d['ok']:>4}  "
                  f"{d['ng']:>4}  {d['pass']:>5}  {d['fail']:>5}  "
                  f"{d['time']:>6.2f}s")
            for k in total:
                total[k] += d[k]

        print("  " + "-" * 68)
        print(f"  {'合計':<22}  {total['total']:>4}  {total['ok']:>4}  "
              f"{total['ng']:>4}  {total['pass']:>5}  {total['fail']:>5}  "
              f"{total['time']:>6.2f}s")
        self._bar()

        if total['ng'] == 0:
            print("\n  ★ 全テスト合格 ★\n")
            return True
        print(f"\n  ⚠  {total['ng']} 件のテストファイルで失敗\n")
        return False


# ============================================================
# フィルタ
# ============================================================
def filter_tests(
    tests: List[TestDef],
    stage: Optional[str],
    only: Optional[str],
) -> List[TestDef]:
    """--stage / --only フィルタ"""
    result = tests

    if stage:
        wanted = {s.strip() for s in stage.split(',') if s.strip()}
        result = [t for t in result if t.category in wanted]

    if only:
        needle = only.lower()
        result = [
            t for t in result
            if (needle in t.filename.lower()
                or needle in t.label.lower()
                or needle in t.category.lower())
        ]

    return result


# ============================================================
# メイン
# ============================================================
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='StaTable 全テスト一括実行ランナー',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument('--list', action='store_true',
                   help='発見したテストを一覧表示のみ（実行しない）')
    p.add_argument('--stage', type=str, default=None,
                   help='カテゴリで絞り込み (例: 1,2,3 / stage1 / legacy / integration)')
    p.add_argument('--only', type=str, default=None,
                   help='ファイル名・ラベルの部分一致で絞り込み')
    p.add_argument('--verbose', action='store_true',
                   help='各テストの全出力を表示')
    p.add_argument('--stop-on-fail', action='store_true',
                   help='最初の失敗で停止')
    p.add_argument('--timeout', type=int, default=180,
                   help='1 テストあたりのタイムアウト秒 (既定: 180)')
    p.add_argument('--logdir', type=str, default=None,
                   help='失敗ログの出力先ディレクトリ')
    return p.parse_args()


def normalize_stage(stage: Optional[str]) -> Optional[str]:
    """'1' → 'stage1' などの正規化"""
    if not stage:
        return None
    parts = []
    for s in stage.split(','):
        s = s.strip()
        if not s:
            continue
        if s.isdigit():
            parts.append(f'stage{s}')
        else:
            parts.append(s)
    return ','.join(parts) if parts else None


def main() -> int:
    args = parse_args()
    args.stage = normalize_stage(args.stage)
    logdir = Path(args.logdir) if args.logdir else None

    # 発見
    registered = {t.filename for t in TEST_REGISTRY}
    tests = list(TEST_REGISTRY) + discover_extra_tests(registered)

    # 存在チェック
    existing = []
    missing = []
    for t in tests:
        if (THIS_DIR / t.filename).exists():
            existing.append(t)
        else:
            missing.append(t)

    # フィルタ
    existing = filter_tests(existing, args.stage, args.only)

    if not existing:
        print("[ERROR] 実行対象のテストが見つかりません。")
        if missing:
            print(f"  未作成: {', '.join(t.filename for t in missing)}")
        return 2

    # --list
    if args.list:
        print(f"\n発見したテスト ({len(existing)} 件):")
        for cat in CATEGORY_ORDER:
            group = [t for t in existing if t.category == cat]
            if not group:
                continue
            print(f"\n[{CATEGORY_LABELS.get(cat, cat)}]")
            for t in group:
                exp = (f"  (想定 {t.expected_count} 件)"
                       if t.expected_count else "")
                print(f"  - {t.filename:<42} {t.label}{exp}")
        if missing:
            print(f"\n[未作成]")
            for t in missing:
                print(f"  - {t.filename}")
        return 0

    # 実行
    runner = Runner(verbose=args.verbose, logdir=logdir)
    runner.header(args, len(existing))

    results: List[TestResult] = []
    current_cat = None
    start = time.time()

    for t in existing:
        if t.category != current_cat:
            current_cat = t.category
            runner.category_header(current_cat)

        r = run_one_test(t, args.timeout, args.verbose)
        results.append(r)
        runner.result_line(r)

        if args.stop_on_fail and not r.ok:
            print("\n[--stop-on-fail] 失敗のため中断しました。")
            break

    total_duration = time.time() - start
    ok = runner.summary(results)
    print(f"  総実行時間: {total_duration:.2f}s")

    if missing:
        print(f"\n  [参考] 未作成のテスト: "
              f"{', '.join(t.filename for t in missing)}")

    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())