# tests/test_code_merger.py
"""
code_merger.CodeMerger のユニットテスト

【目的】
  ユーザーコード保持の回帰防止:
    - ファイル全体ユーザーコード（START/END マーカー）
    - 関数単位ユーザーコード（RoleFunc_XXX / ISR_XXX）
    - ファイル末尾ユーザーコード（TAIL_START/TAIL_END）
    - merge_file の完全サイクル
    - merge_all_files の複数ファイル処理

【対象】
  codegen/code_merger.py
"""
import os
import pytest
from pathlib import Path

from codegen.code_merger import CodeMerger


# ============================================================
# ヘルパー
# ============================================================

def _content_with_file_user(user_code: str) -> str:
    return (
        "// generated\n"
        "/* [[STABLE_USER_CODE_START]] */\n"
        f"{user_code}\n"
        "/* [[STABLE_USER_CODE_END]] */\n"
        "// more generated\n"
    )


def _content_with_func_user(func_name: str, user_code: str) -> str:
    return (
        f"int RoleFunc_{func_name}(...) {{\n"
        f"    /* [[STABLE_USER_CODE_START:{func_name}]] */\n"
        f"{user_code}\n"
        f"    /* [[STABLE_USER_CODE_END:{func_name}]] */\n"
        f"    return 0;\n"
        f"}}\n"
    )


def _content_with_tail_user(user_code: str) -> str:
    return (
        "// generated\n"
        "/* [[STABLE_USER_CODE_TAIL_START]] */\n"
        f"{user_code}\n"
        "/* [[STABLE_USER_CODE_TAIL_END]] */\n"
    )


# ============================================================
# ファイル全体ユーザーコード
# ============================================================

class TestFileUserCode:

    def test_extract_file_user_code(self):
        merger = CodeMerger()
        content = _content_with_file_user("int custom_func(void);")
        result = merger.extract_file_user_code(content)
        assert result == "int custom_func(void);"

    def test_extract_missing_returns_empty(self):
        merger = CodeMerger()
        assert merger.extract_file_user_code("no markers") == ""

    def test_has_user_code(self):
        merger = CodeMerger()
        assert merger.has_user_code(_content_with_file_user("x")) is True
        assert merger.has_user_code("no markers") is False

    def test_inject_file_user_code(self):
        merger = CodeMerger()
        generated = "#include <stdint.h>\n// generated body\n"
        user_code = "int custom(void);"
        result = merger.inject_file_user_code(generated, user_code)
        assert "/* [[STABLE_USER_CODE_START]] */" in result
        assert "int custom(void);" in result
        assert "/* [[STABLE_USER_CODE_END]] */" in result

    def test_inject_empty_user_code_noop(self):
        merger = CodeMerger()
        generated = "// body\n"
        result = merger.inject_file_user_code(generated, "")
        assert result == generated


# ============================================================
# 関数単位ユーザーコード
# ============================================================

class TestFuncUserCode:

    def test_extract_func_user_code_rodefunc(self):
        merger = CodeMerger()
        content = _content_with_func_user("Driver_Init", "// user")
        result = merger.extract_func_user_code(content, "Driver_Init")
        assert result == "// user"

    def test_extract_all_func_user_codes_rodefunc(self):
        merger = CodeMerger()
        content = (
            _content_with_func_user("Driver_Init", "// A") +
            _content_with_func_user("App_Start", "// B")
        )
        result = merger.extract_all_func_user_codes(content)
        assert "Driver_Init" in result
        assert "App_Start" in result
        assert result["Driver_Init"] == "// A"
        assert result["App_Start"] == "// B"

    def test_extract_all_func_user_codes_isr(self):
        """ISR_XXX パターンも抽出できる"""
        merger = CodeMerger()
        content = (
            "void ISR_TIMER0(void) {\n"
            "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
            "    // ISR user code\n"
            "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
            "}\n"
        )
        result = merger.extract_all_func_user_codes(content)
        assert "TIMER0" in result
        assert "// ISR user code" in result["TIMER0"]

    def test_inject_func_user_code(self):
        merger = CodeMerger()
        generated = _content_with_func_user("Driver_Init", "")
        result = merger.inject_func_user_code(
            generated, "Driver_Init", "// new user code")
        assert "// new user code" in result

    def test_inject_func_user_code_missing_marker_noop(self):
        merger = CodeMerger()
        generated = "// no markers\n"
        result = merger.inject_func_user_code(
            generated, "Driver_Init", "// user")
        # マーカーが無い場合は変更されない（新規挿入しない）
        assert result == generated

    def test_has_func_user_code(self):
        merger = CodeMerger()
        content = _content_with_func_user("Driver_Init", "x")
        assert merger.has_func_user_code(content, "Driver_Init") is True
        assert merger.has_func_user_code(content, "App_Start") is False


# ============================================================
# ファイル末尾ユーザーコード
# ============================================================

class TestFileTailUserCode:

    def test_extract_tail_user_code(self):
        merger = CodeMerger()
        content = _content_with_tail_user("// tail")
        result = merger.extract_file_tail_user_code(content)
        assert result == "// tail"

    def test_extract_missing_tail_returns_empty(self):
        merger = CodeMerger()
        assert merger.extract_file_tail_user_code("no markers") == ""

    def test_inject_tail_user_code(self):
        merger = CodeMerger()
        generated = (
            "// body\n"
            "/* [[STABLE_USER_CODE_TAIL_START]] */\n"
            "/* placeholder */\n"
            "/* [[STABLE_USER_CODE_TAIL_END]] */\n"
        )
        result = merger.inject_file_tail_user_code(generated, "// new tail")
        assert "// new tail" in result
        assert "/* placeholder */" not in result


# ============================================================
# merge_file - 完全サイクル
# ============================================================

class TestMergeFile:

    def test_merge_no_existing(self):
        merger = CodeMerger()
        result = merger.merge_file("// new", None)
        assert result == "// new"

    def test_merge_empty_existing(self):
        merger = CodeMerger()
        result = merger.merge_file("// new", "")
        assert result == "// new"

    def test_merge_preserves_file_user_code(self):
        merger = CodeMerger()
        generated = (
            "#include <stdint.h>\n"
            "// body\n"
            "/* [[STABLE_USER_CODE_START]] */\n"
            "/* placeholder */\n"
            "/* [[STABLE_USER_CODE_END]] */\n"
        )
        existing = _content_with_file_user("int custom(void);")
        result = merger.merge_file(generated, existing)
        assert "int custom(void);" in result
        assert "/* placeholder */" not in result

    def test_merge_preserves_func_user_code(self):
        merger = CodeMerger()
        generated = _content_with_func_user("Driver_Init", "")
        existing = _content_with_func_user(
            "Driver_Init", "// user wrote this")
        result = merger.merge_file(generated, existing)
        assert "// user wrote this" in result

    def test_merge_preserves_tail_user_code(self):
        merger = CodeMerger()
        generated = _content_with_tail_user("")
        existing = _content_with_tail_user("// user tail")
        result = merger.merge_file(generated, existing)
        assert "// user tail" in result

    def test_merge_all_user_codes(self):
        """3 種類のユーザーコードが同時に保持される"""
        merger = CodeMerger()
        generated = (
            "#include <stdint.h>\n"
            "/* [[STABLE_USER_CODE_START]] */\n"
            "/* placeholder 1 */\n"
            "/* [[STABLE_USER_CODE_END]] */\n"
            "int RoleFunc_Driver_Init(...) {\n"
            "    /* [[STABLE_USER_CODE_START:Driver_Init]] */\n"
            "    /* placeholder 2 */\n"
            "    /* [[STABLE_USER_CODE_END:Driver_Init]] */\n"
            "}\n"
            "/* [[STABLE_USER_CODE_TAIL_START]] */\n"
            "/* placeholder 3 */\n"
            "/* [[STABLE_USER_CODE_TAIL_END]] */\n"
        )
        existing = (
            "#include <stdint.h>\n"
            "/* [[STABLE_USER_CODE_START]] */\n"
            "int file_custom(void);\n"
            "/* [[STABLE_USER_CODE_END]] */\n"
            "int RoleFunc_Driver_Init(...) {\n"
            "    /* [[STABLE_USER_CODE_START:Driver_Init]] */\n"
            "    do_something();\n"
            "    /* [[STABLE_USER_CODE_END:Driver_Init]] */\n"
            "}\n"
            "/* [[STABLE_USER_CODE_TAIL_START]] */\n"
            "int tail_helper(void);\n"
            "/* [[STABLE_USER_CODE_TAIL_END]] */\n"
        )
        result = merger.merge_file(generated, existing)
        assert "int file_custom(void);" in result
        assert "do_something();" in result
        assert "int tail_helper(void);" in result
        # プレースホルダは残らない
        assert "/* placeholder 1 */" not in result
        assert "/* placeholder 2 */" not in result
        assert "/* placeholder 3 */" not in result


# ============================================================
# merge_all_files
# ============================================================

class TestMergeAllFiles:

    def test_merge_all_files_basic(self, tmp_path):
        merger = CodeMerger()
        # 既存ファイル配置
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        (existing_dir / "a.h").write_text(
            _content_with_file_user("int user_a(void);"),
            encoding="utf-8"
        )
        (existing_dir / "b.h").write_text(
            _content_with_file_user("int user_b(void);"),
            encoding="utf-8"
        )

        generated = {
            "a.h": "#include <stdint.h>\n/* [[STABLE_USER_CODE_START]] */\n/* x */\n/* [[STABLE_USER_CODE_END]] */\n",
            "b.h": "#include <stdint.h>\n/* [[STABLE_USER_CODE_START]] */\n/* x */\n/* [[STABLE_USER_CODE_END]] */\n",
            "c.h": "// no existing\n",
        }

        result = merger.merge_all_files(generated, str(existing_dir))
        assert "int user_a(void);" in result["a.h"]
        assert "int user_b(void);" in result["b.h"]
        # c.h は既存なし → そのまま
        assert result["c.h"] == "// no existing\n"

    def test_merge_all_files_with_path_resolver(self, tmp_path):
        """path_resolver 使用時: 生成キーと既存パスが異なる"""
        merger = CodeMerger()
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        (existing_dir / "Driver").mkdir()
        (existing_dir / "Driver" / "statable_role_functions_Driver.c").write_text(
            _content_with_file_user("int driver_user(void);"),
            encoding="utf-8"
        )

        # 生成キーは "Driver/statable_role_functions.c"
        # 実際の既存パスは "Driver/statable_role_functions_Driver.c"
        generated = {
            "Driver/statable_role_functions.c":
                "#include <stdint.h>\n"
                "/* [[STABLE_USER_CODE_START]] */\n"
                "/* x */\n"
                "/* [[STABLE_USER_CODE_END]] */\n",
        }

        def resolver(filename, layer_name):
            # 層サフィックスを付与
            if "role_functions" in filename:
                stem, ext = os.path.splitext(filename)
                return f"{stem}_Driver{ext}"
            return filename

        result = merger.merge_all_files(
            generated, str(existing_dir),
            path_resolver=resolver,
            layer_name="Driver",
        )
        assert "int driver_user(void);" in result[
            "Driver/statable_role_functions.c"]


# ============================================================
# サマリー取得
# ============================================================

class TestSummary:

    def test_get_user_code_summary(self):
        merger = CodeMerger()
        content = (
            "/* [[STABLE_USER_CODE_START]] */\n"
            "int a(void);\n"
            "/* [[STABLE_USER_CODE_END]] */\n"
            "void RoleFunc_Driver_Init(...) {\n"
            "    /* [[STABLE_USER_CODE_START:Driver_Init]] */\n"
            "    do_x();\n"
            "    /* [[STABLE_USER_CODE_END:Driver_Init]] */\n"
            "}\n"
            "/* [[STABLE_USER_CODE_TAIL_START]] */\n"
            "int tail(void);\n"
            "/* [[STABLE_USER_CODE_TAIL_END]] */\n"
        )
        summary = merger.get_user_code_summary(content)
        assert summary['file_user_code'] > 0
        assert summary['func_user_codes'] >= 1
        assert summary['file_tail_user_code'] > 0


# ============================================================
# エッジケース
# ============================================================

class TestEdgeCases:

    def test_empty_user_code_preserved_as_empty(self):
        """空のユーザーコードブロックは正常に処理される"""
        merger = CodeMerger()
        content = (
            "/* [[STABLE_USER_CODE_START]] */\n"
            "\n"
            "/* [[STABLE_USER_CODE_END]] */\n"
        )
        result = merger.extract_file_user_code(content)
        assert result.strip() == ""

    def test_multiline_user_code(self):
        merger = CodeMerger()
        user_code = "int a(void);\nint b(void);\nint c(void);"
        content = _content_with_file_user(user_code)
        result = merger.extract_file_user_code(content)
        assert "int a" in result
        assert "int b" in result
        assert "int c" in result