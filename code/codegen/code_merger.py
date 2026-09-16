# codegen/code_merger.py
"""
生成コードと既存コードのマージ処理
ユーザー編集部分を保持しながら自動生成コードを更新する

対応マーカー:
  - ファイル全体ユーザー領域: [[STABLE_USER_CODE_START/END]]
  - 関数単位ユーザー領域: [[STABLE_USER_CODE_START:<name>/END:<name>]]
    - RoleFunc_XXX の <name> は "Driver_Init" 形式（層名込み）
    - ISR_XXX の <name> は "TIMER0" 形式（層名なし）
  - ファイル末尾ユーザー領域: [[STABLE_USER_CODE_TAIL_START/END]]

【v2.0 修正】
  - inject_file_user_code: 既存 START/END ブロックがあればその中身を
    置換するよう変更。旧実装は常に include の後に新規挿入していたため、
    生成コード元のブロックが残骸化し、プレースホルダが残り続けていた。
"""

import re
import os
import logging
from typing import Dict, List, Optional, Tuple, Callable

logger = logging.getLogger(__name__)


class CodeMerger:
    """生成コードと既存コードのマージクラス"""

    # マーカー定義
    MARKERS = {
        'file_user_start': '/* [[STABLE_USER_CODE_START]] */',
        'file_user_end': '/* [[STABLE_USER_CODE_END]] */',
        'func_user_start': '/* [[STABLE_USER_CODE_START:{func_name}]] */',
        'func_user_end': '/* [[STABLE_USER_CODE_END:{func_name}]] */',
        'auto_start': '/* [[STABLE_AUTO_GENERATED_START]] */',
        'auto_end': '/* [[STABLE_AUTO_GENERATED_END]] */',
        # ファイル末尾ユーザー領域
        'file_tail_user_start': '/* [[STABLE_USER_CODE_TAIL_START]] */',
        'file_tail_user_end':   '/* [[STABLE_USER_CODE_TAIL_END]] */',
    }

    # ★ 関数名抽出パターン（RoleFunc_ / ISR_ 両対応）
    FUNC_NAME_PATTERNS = [
        r'RoleFunc_(\w+)\s*\(',   # RoleFunc_Driver_Init(
        r'ISR_(\w+)\s*\(',        # ISR_TIMER0(
    ]

    def __init__(self):
        self.markers = self.MARKERS

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ===== 抽出処理 =====
    def extract_file_user_code(self, existing_content: str) -> str:
        """ファイル全体のユーザーコードを抽出"""
        start = self.markers['file_user_start']
        end = self.markers['file_user_end']

        pattern = rf'{re.escape(start)}\s*\n(.*?)\n\s*{re.escape(end)}'
        match = re.search(pattern, existing_content, re.DOTALL)

        if match:
            self._log_debug("ファイルユーザーコードを抽出しました")
            return match.group(1)
        return ""

    def extract_func_user_code(self, existing_content: str,
                               func_name: str) -> str:
        """関数単位のユーザーコードを抽出"""
        start = self.markers['func_user_start'].format(func_name=func_name)
        end = self.markers['func_user_end'].format(func_name=func_name)

        pattern = rf'{re.escape(start)}\s*\n(.*?)\n\s*{re.escape(end)}'
        match = re.search(pattern, existing_content, re.DOTALL)

        if match:
            self._log_debug(f"関数 {func_name} のユーザーコードを抽出しました")
            return match.group(1)
        return ""

    def extract_all_func_user_codes(self, existing_content: str
                                    ) -> Dict[str, str]:
        """
        全関数のユーザーコードを抽出

        RoleFunc_XXX と ISR_XXX の両方に対応
        - RoleFunc_Driver_Init → キー "Driver_Init"
        - ISR_TIMER0           → キー "TIMER0"
        """
        func_user_codes = {}
        seen = set()

        for pattern in self.FUNC_NAME_PATTERNS:
            for match in re.finditer(pattern, existing_content):
                func_name = match.group(1)
                if func_name in seen:
                    continue
                seen.add(func_name)
                user_code = self.extract_func_user_code(
                    existing_content, func_name
                )
                if user_code:
                    func_user_codes[func_name] = user_code

        self._log_debug(
            f"extract_all_func_user_codes: {len(func_user_codes)} funcs"
        )
        return func_user_codes

    # ファイル末尾ユーザーコード抽出
    def extract_file_tail_user_code(self, existing_content: str) -> str:
        """ファイル末尾のユーザーコードを抽出"""
        start = self.markers['file_tail_user_start']
        end = self.markers['file_tail_user_end']

        pattern = rf'{re.escape(start)}\s*\n(.*?)\n\s*{re.escape(end)}'
        match = re.search(pattern, existing_content, re.DOTALL)

        if match:
            self._log_debug("末尾ユーザーコードを抽出しました")
            return match.group(1)
        return ""

    # ===== 注入処理 =====
    def inject_file_user_code(self, generated_content: str,
                              user_code: str) -> str:
        """
        生成コードにファイル全体のユーザーコードを注入

        【v2.0 修正】
          既存の START/END ブロックがあれば、その中身を user_code で置換する。
          ブロックが無い場合のみ、include の後に新規挿入する。

          旧: 常に include の後に新規挿入 → 生成コード元のブロックが残骸化
          新: 既存ブロックを置換 → 常に 1 つのブロックのみ
        """
        if not user_code:
            return generated_content

        start = self.markers['file_user_start']
        end = self.markers['file_user_end']

        # ---- 1. 既存ブロックがあれば置換 ----
        pattern = rf'({re.escape(start)}\s*\n).*?(\n\s*{re.escape(end)})'
        replacement = rf'\g<1>{user_code}\n\g<2>'
        result, count = re.subn(
            pattern, replacement, generated_content,
            count=1, flags=re.DOTALL,
        )
        if count:
            self._log_debug("ファイルユーザーコードを置換しました")
            return result

        # ---- 2. ブロックが無ければ include の後に新規挿入 ----
        injection = f"{start}\n{user_code}\n{end}\n"
        lines = generated_content.split('\n')
        result_lines = []
        injected = False
        last_include_idx = -1

        for i, line in enumerate(lines):
            if line.startswith('#include'):
                last_include_idx = i

        if last_include_idx >= 0:
            # インクルードの後に注入
            for i, line in enumerate(lines):
                result_lines.append(line)
                if i == last_include_idx:
                    result_lines.append("")
                    result_lines.append(injection.rstrip('\n'))
                    injected = True

        if not injected:
            # インクルードがない場合は先頭に注入
            result_lines.insert(0, injection.rstrip('\n'))

        self._log_debug("ファイルユーザーコードを新規挿入しました")
        return '\n'.join(result_lines)

    # ★ 関数ユーザーコード注入: 既存マーカーブロックを置換
    def inject_func_user_code(self, generated_content: str,
                              func_name: str, user_code: str) -> str:
        """
        生成コード内の既存マーカーブロックを user_code で置換

        - 生成コード側に既にマーカーがある前提で、その間の内容を置換する
        - マーカーが存在しない場合は何もしない（新規挿入はしない）
        """
        if not user_code:
            return generated_content

        start = self.markers['func_user_start'].format(func_name=func_name)
        end = self.markers['func_user_end'].format(func_name=func_name)

        pattern = rf'({re.escape(start)}\s*\n).*?(\n\s*{re.escape(end)})'
        replacement = rf'\g<1>{user_code}\n\g<2>'

        result, count = re.subn(
            pattern, replacement, generated_content,
            count=1, flags=re.DOTALL,
        )
        if count:
            self._log_debug(f"関数 {func_name} のユーザーコードを注入しました")
        else:
            self._log_debug(
                f"関数 {func_name} のマーカーが見つかりません", 'warning'
            )
        return result

    # ★ ファイル末尾ユーザーコード注入
    def inject_file_tail_user_code(self, generated_content: str,
                                   user_code: str) -> str:
        """生成コード末尾のマーカー内にユーザーコードを注入（置換）"""
        if not user_code:
            return generated_content

        start = self.markers['file_tail_user_start']
        end = self.markers['file_tail_user_end']

        pattern = rf'({re.escape(start)}\s*\n).*?(\n\s*{re.escape(end)})'
        replacement = rf'\g<1>{user_code}\n\g<2>'

        result, count = re.subn(
            pattern, replacement, generated_content,
            count=1, flags=re.DOTALL,
        )
        if count:
            self._log_debug("末尾ユーザーコードを注入しました")
        else:
            self._log_debug("末尾マーカーが見つかりません", 'warning')
        return result

    # ===== マージ処理 =====
    def merge_file(self, generated_content: str,
                   existing_content: Optional[str]) -> str:
        """生成コードと既存コードをマージ"""
        if existing_content is None or not existing_content.strip():
            self._log_debug("既存コードなし、生成コードをそのまま使用")
            return generated_content

        self._log_debug("マージ処理を開始")

        # 各種ユーザーコード抽出
        file_user_code = self.extract_file_user_code(existing_content)

        # 関数単位のユーザーコードを抽出
        func_user_codes = self.extract_all_func_user_codes(existing_content)
        tail_user_code = self.extract_file_tail_user_code(existing_content)

        self._log_debug(f"ファイルユーザーコード: {len(file_user_code)}文字")
        self._log_debug(f"関数ユーザーコード: {len(func_user_codes)}個")
        self._log_debug(f"末尾ユーザーコード: {len(tail_user_code)}文字")

        # 生成コードにユーザーコードを注入
        result = generated_content

        # ファイル全体のユーザーコードを注入
        result = self.inject_file_user_code(result, file_user_code)

        # 関数単位のユーザーコードを注入
        for func_name, user_code in func_user_codes.items():
            result = self.inject_func_user_code(
                result, func_name, user_code
            )

        result = self.inject_file_tail_user_code(result, tail_user_code)

        return result

    # ★ フォルダ構成対応版
    def merge_all_files(self, generated_files: Dict[str, str],
                        existing_dir: str,
                        path_resolver: Optional[Callable] = None,
                        layer_name: str = '') -> Dict[str, str]:
        """
        全ファイルをマージ（フォルダ構成対応）

        Args:
            generated_files: 生成ファイル辞書
            existing_dir:    既存ファイル探索の基点
            path_resolver:   ファイル名→相対パスを返す関数
                             (filename, layer_name) -> rel_path
                             None なら filename そのまま
            layer_name:      層名（by_layer 用）
        """
        self._log_debug(f"全ファイルマージ開始: {existing_dir}")
        merged_files = {}

        for filename, generated_content in generated_files.items():
            # ★ パス解決
            if path_resolver is not None:
                try:
                    rel_path = path_resolver(filename, layer_name)
                except Exception as e:
                    self._log_debug(
                        f"path_resolver failed for {filename}: {e}",
                        'warning'
                    )
                    rel_path = filename
            else:
                rel_path = filename

            existing_path = os.path.join(existing_dir, rel_path)

            if os.path.exists(existing_path):
                self._log_debug(f"既存ファイルあり: {existing_path}")
                with open(existing_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            else:
                self._log_debug(f"既存ファイルなし: {existing_path}")
                existing_content = None

            merged_files[filename] = self.merge_file(
                generated_content, existing_content,
            )

        return merged_files

    # ===== マーカー存在確認 =====
    def has_user_code(self, content: str) -> bool:
        """ユーザーコードが含まれているか"""
        return self.markers['file_user_start'] in content

    def has_func_user_code(self, content: str, func_name: str) -> bool:
        """特定の関数にユーザーコードが含まれているか"""
        start = self.markers['func_user_start'].format(func_name=func_name)
        return start in content

    def get_user_code_summary(self, content: str) -> Dict[str, int]:
        """ユーザーコードの概要を取得"""
        summary = {
            'file_user_code': 0,
            'func_user_codes': 0,
            'file_tail_user_code': 0,
        }

        if self.has_user_code(content):
            file_code = self.extract_file_user_code(content)
            summary['file_user_code'] = len(file_code)

        func_codes = self.extract_all_func_user_codes(content)
        summary['func_user_codes'] = len(func_codes)

        tail_code = self.extract_file_tail_user_code(content)
        summary['file_tail_user_code'] = len(tail_code)

        return summary