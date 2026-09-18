# apply_batch11_fstrings.py - v2 (single-quote safe, comprehensive)
import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIRS = ["statable", "statable_gui", "codegen"]

REPLACEMENTS = [
    # ===== Long patterns first (must not be swallowed by short ones) =====
    ('コード生成に失敗しました:\\n', 'Code generation failed:\\n'),
    ('保存に失敗しました:\\n', 'Save failed:\\n'),
    ('設定を保存しました: ', 'Settings saved: '),
    ('設定保存に失敗: ', 'Failed to save settings: '),
    ('前回の設定を読み込みました: ', 'Loaded previous settings: '),
    ('設定読み込みに失敗: ', 'Failed to load settings: '),
    ('生成しました。\\n出力先: ', 'generated.\\nOutput: '),
    ('保存しました。\\n\\n', 'saved.\\n\\n'),
    ('保存しました。', 'saved.'),
    ('派生タイマ変数（{d.period_name}）', 'Derived timer variable ({d.period_name})'),
    (' をグローバル変数として登録', ' as global variable'),
    (' をイベントフラグとして登録', ' as event flag'),
    ('は削除できません。\\n\\n以下の遷移で使用されています：\\n\\n',
     ' cannot be deleted.\\n\\nUsed by the following transitions:\\n\\n'),
    ("' は割り込み処理 '", "' is used by interrupt handler '"),
    ("' で使用されています。", "'."),
    ('自動収集 (', 'Auto-collected ('),
    ('件の変更を抽出しました。', ' change(s) extracted.'),
    ('件の変更を反映しました。\\n', ' change(s) applied.\\n'),
    ("{result['failed']}件", "{result['failed']} item(s)"),
    (' は既に存在します。', ' already exists.'),
    (' を削除しますか？', ': confirm delete?'),
    ('種別: グローバル変数', 'Kind: Global variable'),
    ('種別: イベントフラグ', 'Kind: Event flag'),
    ('種別: ロール関数戻り値', 'Kind: Role function return value'),
    ('イベントをエンキューする（{name}）', 'Enqueue event ({name})'),
    ('イベントをデキューする（{name}）', 'Dequeue event ({name})'),
    # ===== change_applier (single-quote inside) =====
    ('未対応のアクション: ', 'Unsupported action: '),
    ('状態「{state}」が存在しません', "State '{state}' does not exist"),
    ('初期状態を「{state}」に設定しました', "Initial state set to '{state}'"),
    ('遷移「{source} --[{event}]--> {target}」を追加しました',
     "Transition '{source} --[{event}]--> {target}' added"),
    ('遷移「{source} --[{event}]--> {target}」を削除しました',
     "Transition '{source} --[{event}]--> {target}' deleted"),
    ('遷移「{source} --[{event}]-->」を更新しました',
     "Transition '{source} --[{event}]-->' updated"),
    ('状態「{name}」は既に存在します', "State '{name}' already exists"),
    ('状態「{name}」を追加しました', "State '{name}' added"),
    ('イベント「{name}」は既に存在します', "Event '{name}' already exists"),
    ('イベント「{name}」を追加しました', "Event '{name}' added"),
    ('関数「{name}」は既に存在します', "Function '{name}' already exists"),
    ('ロール関数「{name}」を追加しました', "Role function '{name}' added"),
    ('ロール関数「{name}」を削除しました', "Role function '{name}' deleted"),
    ('関数「{name}」が見つかりません', "Function '{name}' not found"),
    ('変数「{name}」を追加しました', "Variable '{name}' added"),
    ('フラグ「{name}」を追加しました', "Flag '{name}' added"),
    # ===== prompt_generator =====
    (' [条件: ', ' [condition: '),
    (' [アクション: ', ' [action: '),
    ('\\n### 初期状態\\n', '\\n### Initial state\\n'),
    # ===== Code-generated string fragments =====
    ('/* 未定義参照（無効な識別子）: ', '/* Undefined reference (invalid identifier): '),
    ('/* 不正な参照: ', '/* Invalid reference: '),
    (' (直前:', ' (pre: '),
    ('/* イベントキュー: ', '/* Event queue: '),
    (' 割り込みハンドラ', ' interrupt handler'),
    ('return false;  /* キュー満杯 */', 'return false;  /* Queue full */'),
    ('return false;  /* キュー空 */', 'return false;  /* Queue empty */'),
    # ===== Event/object prefix with space + quote (MUST come before short tags) =====
    ("イベント '", "Event '"),
    ("イベント「", 'Event "'),  # safety net (rare)
    # ===== Short tag prefixes (longest first) =====
    ('タイマ基準:', 'Timer base:'),
    ('状態遷移条件:', 'State transition condition:'),
    ('ロール関数:', 'Role function:'),
    ('タイマ:', 'Timer:'),
    ('メンバ:', 'Member:'),
    ('イベント:', 'Event:'),
    ('割り込み:', 'Interrupt:'),
    ('デバイス:', 'Device:'),
    ('キュー:', 'Queue:'),
    ('変数:', 'Variable:'),
    ('フラグ:', 'Flag:'),
    ('型:', 'Type:'),
    ('タイトル:', 'Title:'),
    ('遷移先:', 'Target:'),
    ('種別:', 'Kind:'),
    ('名前:', 'Name:'),
    ('単位:', 'Unit:'),
    ('初期値:', 'Initial value:'),
    ('グループ:', 'Group:'),
    ('説明:', 'Description:'),
    ('最小値:', 'Min value:'),
    ('最大値:', 'Max value:'),
    ('ビット幅:', 'Bit width:'),
    ('戻り値:', 'Return value:'),
    ('関数:', 'Function:'),
    ('一時変数:', 'Temp variable:'),
    ('エラー:', 'Error:'),
    ('警告:', 'Warning:'),
    ('情報:', 'Info:'),
    ('失敗:', 'Failed:'),
    ('条件:', 'Condition:'),
    ('アクション:', 'Action:'),
    ('出力先: ', 'Output: '),
    ('ファイルを', ' files '),
    # ===== Bullet =====
    ('・', '- '),
]


def process_file(path, dry_run):
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        return None, 0, str(e)
    original = src
    count = 0
    for ja, en in REPLACEMENTS:
        if ja in src:
            n = src.count(ja)
            src = src.replace(ja, en)
            count += n
    if src == original:
        return None, 0, None
    if not dry_run:
        path.write_text(src, encoding="utf-8")
    return path, count, None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--backup", action="store_true")
    args = p.parse_args()
    if not args.dry_run and not args.apply:
        args.dry_run = True

    files = []
    for d in DIRS:
        root = PROJECT_ROOT / d
        if root.exists():
            files.extend(root.rglob("*.py"))

    backup_dir = None
    if args.apply and args.backup:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = PROJECT_ROOT / ("_backup_" + ts)
        backup_dir.mkdir()

    total = 0
    changed = 0
    for f in files:
        rel = f.relative_to(PROJECT_ROOT)
        if backup_dir:
            bp = backup_dir / rel
            bp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, bp)
        p2, cnt, err = process_file(f, dry_run=args.dry_run)
        if err:
            print("[ERR] " + str(rel) + ": " + err)
        elif p2:
            changed += 1
            total += cnt
            tag = "DRY" if args.dry_run else "CHG"
            print("[" + tag + "] " + str(rel) + ": " + str(cnt) + " replacements")

    print("")
    print("Changed: " + str(changed) + " files, total replacements: " + str(total))
    if backup_dir:
        print("Backup : " + str(backup_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())