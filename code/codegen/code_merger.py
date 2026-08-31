# codegen/code_merger.py
"""
生成コードと既存コードのマージ処理
ユーザー編集部分を保持しながら自動生成コードを更新する
"""

import re
import os
import logging
from typing import Dict, List, Optional, Tuple

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
    }
    
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
        
        self._log_debug("ファイルユーザーコードが見つかりません")
        return ""
    
    def extract_func_user_code(self, existing_content: str, func_name: str) -> str:
        """関数単位のユーザーコードを抽出"""
        start = self.markers['func_user_start'].format(func_name=func_name)
        end = self.markers['func_user_end'].format(func_name=func_name)
        
        pattern = rf'{re.escape(start)}\s*\n(.*?)\n\s*{re.escape(end)}'
        match = re.search(pattern, existing_content, re.DOTALL)
        
        if match:
            self._log_debug(f"関数 {func_name} のユーザーコードを抽出しました")
            return match.group(1)
        
        self._log_debug(f"関数 {func_name} のユーザーコードが見つかりません")
        return ""
    
    def extract_all_func_user_codes(self, existing_content: str) -> Dict[str, str]:
        """全関数のユーザーコードを抽出"""
        func_user_codes = {}
        
        # 関数名を抽出
        func_pattern = r'RoleFunc_(\w+)\s*\('
        for match in re.finditer(func_pattern, existing_content):
            func_name = match.group(1)
            user_code = self.extract_func_user_code(existing_content, func_name)
            if user_code:
                func_user_codes[func_name] = user_code
        
        return func_user_codes
    
    # ===== 注入処理 =====
    def inject_file_user_code(self, generated_content: str, user_code: str) -> str:
        """生成コードにファイル全体のユーザーコードを注入"""
        if not user_code:
            return generated_content
        
        start = self.markers['file_user_start']
        end = self.markers['file_user_end']
        
        injection = f"{start}\n{user_code}\n{end}\n"
        
        # インクルード後に注入
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
        
        return '\n'.join(result_lines)
    
    def inject_func_user_code(self, generated_content: str, func_name: str, user_code: str) -> str:
        """生成コードに関数単位のユーザーコードを注入"""
        if not user_code:
            return generated_content
        
        start = self.markers['func_user_start'].format(func_name=func_name)
        end = self.markers['func_user_end'].format(func_name=func_name)
        
        injection = f"    {start}\n{user_code}\n    {end}"
        
        # 関数を検索
        func_pattern = rf'(?:void|bool|int|uint\d+_t|int\d+_t|float|double)\s+RoleFunc_{re.escape(func_name)}\s*\('
        match = re.search(func_pattern, generated_content)
        
        if not match:
            self._log_debug(f"関数 RoleFunc_{func_name} が見つかりません", 'warning')
            return generated_content
        
        # 関数ボディの開始位置
        body_start = generated_content.find('{', match.end())
        if body_start == -1:
            return generated_content
        
        # TODO コメントを検索
        todo_pattern = r'/\*\s*TODO[^*]*\*/'
        todo_match = re.search(todo_pattern, generated_content[body_start:])
        
        if todo_match:
            # TODO コメントの後に注入
            todo_end = body_start + todo_match.end()
            line_end = generated_content.find('\n', todo_end)
            if line_end == -1:
                line_end = todo_end
            inject_pos = line_end + 1
        else:
            # ボディ開始直後
            inject_pos = body_start + 1
        
        # インデントを揃える
        indented_user_code = user_code.replace('\n', '\n    ')
        
        injection = (
            f"    {start}\n"
            f"    {indented_user_code}\n"
            f"    {end}\n"
        )
        
        return (
            generated_content[:inject_pos] +
            injection +
            generated_content[inject_pos:]
        )
    
    # ===== マージ処理 =====
    def merge_file(self, generated_content: str, existing_content: Optional[str]) -> str:
        """生成コードと既存コードをマージ"""
        if existing_content is None or not existing_content.strip():
            self._log_debug("既存コードなし、生成コードをそのまま使用")
            return generated_content
        
        self._log_debug("マージ処理を開始")
        
        # ファイル全体のユーザーコードを抽出
        file_user_code = self.extract_file_user_code(existing_content)
        
        # 関数単位のユーザーコードを抽出
        func_user_codes = self.extract_all_func_user_codes(existing_content)
        
        self._log_debug(f"ファイルユーザーコード: {len(file_user_code)}文字")
        self._log_debug(f"関数ユーザーコード: {len(func_user_codes)}個")
        
        # 生成コードにユーザーコードを注入
        result = generated_content
        
        # ファイル全体のユーザーコードを注入
        result = self.inject_file_user_code(result, file_user_code)
        
        # 関数単位のユーザーコードを注入
        for func_name, user_code in func_user_codes.items():
            result = self.inject_func_user_code(result, func_name, user_code)
        
        return result
    
    def merge_all_files(self, generated_files: Dict[str, str], 
                       existing_dir: str) -> Dict[str, str]:
        """全ファイルをマージ"""
        self._log_debug(f"全ファイルマージ開始: {existing_dir}")
        merged_files = {}
        
        for filename, generated_content in generated_files.items():
            existing_path = os.path.join(existing_dir, filename)
            
            if os.path.exists(existing_path):
                self._log_debug(f"既存ファイルあり: {filename}")
                with open(existing_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            else:
                self._log_debug(f"既存ファイルなし: {filename}")
                existing_content = None
            
            merged_files[filename] = self.merge_file(generated_content, existing_content)
        
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
        }
        
        if self.has_user_code(content):
            file_code = self.extract_file_user_code(content)
            summary['file_user_code'] = len(file_code)
        
        func_codes = self.extract_all_func_user_codes(content)
        summary['func_user_codes'] = len(func_codes)
        
        return summary