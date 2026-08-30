"""全Pythonファイルのエンコーディングチェック

UTF-8で読み込めるか確認し、問題のあるファイルを検出する。
"""

import sys
import os
from pathlib import Path

# プロジェクトルートを sys.path に追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def check_file_encoding(filepath: Path) -> tuple:
    """ファイルがUTF-8で読み込めるかチェック
    
    Returns:
        (success: bool, error_message: str)
    """
    try:
        # UTF-8で読み込み
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read()
        return True, ""
    except UnicodeDecodeError as e:
        return False, f"UTF-8デコードエラー: {e}"
    except Exception as e:
        return False, f"その他のエラー: {e}"


def check_python_syntax(filepath: Path) -> tuple:
    """Pythonファイルの構文チェック
    
    Returns:
        (success: bool, error_message: str)
    """
    try:
        import py_compile
        py_compile.compile(str(filepath), doraise=True)
        return True, ""
    except SyntaxError as e:
        return False, f"構文エラー: {e}"
    except Exception as e:
        return False, f"その他のエラー: {e}"


def get_all_python_files(root: Path) -> list:
    """プロジェクト内の全Pythonファイルを取得"""
    python_files = []
    exclude_dirs = {'__pycache__', '.git', '.venv', 'venv', 'Resources'}
    
    for filepath in root.rglob('*.py'):
        # 除外ディレクトリをスキップ
        if any(exclude_dir in filepath.parts for exclude_dir in exclude_dirs):
            continue
        python_files.append(filepath)
    
    return sorted(python_files)


def main():
    print("=" * 70)
    print("StaTable エンコーディングチェック")
    print("=" * 70)

    python_files = get_all_python_files(PROJECT_ROOT)
    print(f"\n検出されたPythonファイル: {len(python_files)}個\n")

    errors = []
    checked = 0

    for filepath in python_files:
        relative = filepath.relative_to(PROJECT_ROOT)
        
        # エンコーディングチェック
        enc_ok, enc_err = check_file_encoding(filepath)
        
        # 構文チェック
        syntax_ok, syntax_err = check_python_syntax(filepath)
        
        checked += 1
        
        if enc_ok and syntax_ok:
            print(f"  [OK] {relative}")
        else:
            print(f"  [NG] {relative}")
            if not enc_ok:
                print(f"       -> {enc_err}")
                errors.append((str(relative), enc_err))
            if not syntax_ok:
                print(f"       -> {syntax_err}")
                errors.append((str(relative), syntax_err))

    print("\n" + "=" * 70)
    print(f"チェック完了: {checked}ファイル中、{len(errors)}ファイルに問題あり")
    
    if errors:
        print("\n問題のあるファイル:")
        for filepath, err in errors:
            print(f"  {filepath}")
            print(f"    {err}")
    else:
        print("すべてのファイルがUTF-8で正常に読み込めます。")
    
    print("=" * 70)
    
    return len(errors)


if __name__ == "__main__":
    try:
        error_count = main()
        sys.exit(1 if error_count > 0 else 0)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)