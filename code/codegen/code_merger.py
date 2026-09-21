# codegen/code_merger.py
"""
Merging generated code with existing code.
Updates auto-generated code while preserving user-edited sections.

Supported markers:
  - File-level user area: [[STABLE_USER_CODE_START/END]]
  - Function-level user area: [[STABLE_USER_CODE_START:<name>/END:<name>]]
    - RoleFunc_XXX uses <name> in "Driver_Init" form (includes layer)
    - ISR_XXX uses <name> in "TIMER0" form (no layer)
  - File-tail user area: [[STABLE_USER_CODE_TAIL_START/END]]

Version History
---------------
v2.0 - inject_file_user_code: if an existing START/END block is present,
       replace its contents. Old implementation always inserted a new
       block after the includes, leaving the original block as dead code
       and the placeholder behind.

v2.1 - Idempotency fix. The replacement pattern previously captured
       the trailing newline into group(2), so each merge added one
       extra newline per marker (4 markers -> +4 chars per merge).
       The new pattern replaces the ENTIRE block (START..END) with a
       freshly constructed block (START\\n user_code \\n END), and
       uses a callable replacement to avoid re.sub escape handling.
       Verified by tests/test_v2_4_p1_merge.py §3.
"""

import re
import os
import logging
from typing import Dict, List, Optional, Tuple, Callable

logger = logging.getLogger(__name__)


class CodeMerger:
    """Merge class for generated code and existing code"""

    # Marker definitions
    MARKERS = {
        'file_user_start': '/* [[STABLE_USER_CODE_START]] */',
        'file_user_end': '/* [[STABLE_USER_CODE_END]] */',
        'func_user_start': '/* [[STABLE_USER_CODE_START:{func_name}]] */',
        'func_user_end': '/* [[STABLE_USER_CODE_END:{func_name}]] */',
        'auto_start': '/* [[STABLE_AUTO_GENERATED_START]] */',
        'auto_end': '/* [[STABLE_AUTO_GENERATED_END]] */',
        # File-tail user area
        'file_tail_user_start': '/* [[STABLE_USER_CODE_TAIL_START]] */',
        'file_tail_user_end':   '/* [[STABLE_USER_CODE_TAIL_END]] */',
    }

    # Function name extraction patterns (RoleFunc_ / ISR_)
    FUNC_NAME_PATTERNS = [
        r'RoleFunc_(\w+)\s*\(',   # RoleFunc_Driver_Init(
        r'ISR_(\w+)\s*\(',        # ISR_TIMER0(
    ]

    def __init__(self):
        self.markers = self.MARKERS

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ===== Extraction =====
    def extract_file_user_code(self, existing_content: str) -> str:
        """Extract file-level user code (contents between START and END)."""
        start = self.markers['file_user_start']
        end = self.markers['file_user_end']

        pattern = rf'{re.escape(start)}\s*\n(.*?)\n\s*{re.escape(end)}'
        match = re.search(pattern, existing_content, re.DOTALL)

        if match:
            self._log_debug("Extracted file user code")
            return match.group(1)
        return ""

    def extract_func_user_code(self, existing_content: str,
                               func_name: str) -> str:
        """Extract per-function user code."""
        start = self.markers['func_user_start'].format(func_name=func_name)
        end = self.markers['func_user_end'].format(func_name=func_name)

        pattern = rf'{re.escape(start)}\s*\n(.*?)\n\s*{re.escape(end)}'
        match = re.search(pattern, existing_content, re.DOTALL)

        if match:
            self._log_debug(f"Extracted user code for function {func_name}")
            return match.group(1)
        return ""

    def extract_all_func_user_codes(self, existing_content: str
                                    ) -> Dict[str, str]:
        """
        Extract all per-function user codes.

        Supports both RoleFunc_XXX and ISR_XXX.
        - RoleFunc_Driver_Init -> key "Driver_Init"
        - ISR_TIMER0           -> key "TIMER0"
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

    def extract_file_tail_user_code(self, existing_content: str) -> str:
        """Extract file-tail user code."""
        start = self.markers['file_tail_user_start']
        end = self.markers['file_tail_user_end']

        pattern = rf'{re.escape(start)}\s*\n(.*?)\n\s*{re.escape(end)}'
        match = re.search(pattern, existing_content, re.DOTALL)

        if match:
            self._log_debug("Extracted tail user code")
            return match.group(1)
        return ""

    # ===== Helper: block replacement (idempotent) =====
    @staticmethod
    def _replace_block(text: str, start_marker: str, end_marker: str,
                       user_code: str) -> Tuple[str, int]:
        """
        Replace the contents of an existing START..END block with a
        canonical block:

            START
            <user_code>
            END

        Returns (new_text, replaced_count).
        The replacement uses a callable to bypass re.sub escape handling.
        """
        pattern = re.compile(
            rf'{re.escape(start_marker)}.*?{re.escape(end_marker)}',
            re.DOTALL,
        )
        canonical = f"{start_marker}\n{user_code}\n{end_marker}"
        new_text, count = pattern.subn(
            lambda m: canonical, text, count=1,
        )
        return new_text, count

    # ===== Injection =====
    def inject_file_user_code(self, generated_content: str,
                              user_code: str) -> str:
        """
        Inject file-level user code into the generated code.

        [v2.0]
          If an existing START/END block is present, replace its contents.
          Old: always inserted a new block after includes -> the original
               block became dead code.
          New: replace existing block -> always exactly one block.

        [v2.1]
          Idempotency fix. The whole block (START..END) is now replaced
          with a freshly constructed one, so repeated merges do not
          accumulate extra newlines.
        """
        if not user_code:
            return generated_content

        start = self.markers['file_user_start']
        end = self.markers['file_user_end']

        # ---- 1. Replace if existing block found ----
        result, count = self._replace_block(
            generated_content, start, end, user_code,
        )
        if count:
            self._log_debug("Replaced file user code")
            return result

        # ---- 2. No block: insert new one after includes ----
        canonical = f"{start}\n{user_code}\n{end}"
        lines = generated_content.split('\n')
        result_lines = []
        injected = False
        last_include_idx = -1

        for i, line in enumerate(lines):
            if line.startswith('#include'):
                last_include_idx = i

        if last_include_idx >= 0:
            for i, line in enumerate(lines):
                result_lines.append(line)
                if i == last_include_idx:
                    result_lines.append("")
                    result_lines.append(canonical)
                    injected = True

        if not injected:
            result_lines.insert(0, canonical)

        self._log_debug("Inserted new file user code block")
        return '\n'.join(result_lines)

    def inject_func_user_code(self, generated_content: str,
                              func_name: str, user_code: str) -> str:
        """
        Replace existing per-function marker block with user_code.

        - Assumes the generated code already has the marker; replaces
          the content between them.
        - If the marker is missing, does nothing (no new insertion).
        """
        if not user_code:
            return generated_content

        start = self.markers['func_user_start'].format(func_name=func_name)
        end = self.markers['func_user_end'].format(func_name=func_name)

        result, count = self._replace_block(
            generated_content, start, end, user_code,
        )
        if count:
            self._log_debug(f"Injected user code for function {func_name}")
        else:
            self._log_debug(
                f"Marker not found for function {func_name}", 'warning'
            )
        return result

    def inject_file_tail_user_code(self, generated_content: str,
                                   user_code: str) -> str:
        """Inject user code into the file-tail marker (replace)."""
        if not user_code:
            return generated_content

        start = self.markers['file_tail_user_start']
        end = self.markers['file_tail_user_end']

        result, count = self._replace_block(
            generated_content, start, end, user_code,
        )
        if count:
            self._log_debug("Injected tail user code")
        else:
            self._log_debug("Tail marker not found", 'warning')
        return result

    # ===== Merge =====
    def merge_file(self, generated_content: str,
                   existing_content: Optional[str]) -> str:
        """Merge generated code with existing code"""
        if existing_content is None or not existing_content.strip():
            self._log_debug("No existing code, using generated code as-is")
            return generated_content

        self._log_debug("Starting merge")

        # Extract user codes
        file_user_code = self.extract_file_user_code(existing_content)
        func_user_codes = self.extract_all_func_user_codes(existing_content)
        tail_user_code = self.extract_file_tail_user_code(existing_content)

        self._log_debug(f"File user code: {len(file_user_code)} chars")
        self._log_debug(f"Function user codes: {len(func_user_codes)} funcs")
        self._log_debug(f"Tail user code: {len(tail_user_code)} chars")

        # Inject user codes into generated code
        result = generated_content

        result = self.inject_file_user_code(result, file_user_code)

        for func_name, user_code in func_user_codes.items():
            result = self.inject_func_user_code(
                result, func_name, user_code
            )

        result = self.inject_file_tail_user_code(result, tail_user_code)

        return result

    # Folder structure aware version
    def merge_all_files(self, generated_files: Dict[str, str],
                        existing_dir: str,
                        path_resolver: Optional[Callable] = None,
                        layer_name: str = '') -> Dict[str, str]:
        """
        Merge all files (folder structure aware).

        Args:
            generated_files: generated file dictionary
            existing_dir:    base directory for existing file lookup
            path_resolver:   function returning relative path
                             (filename, layer_name) -> rel_path
                             If None, use filename as-is
            layer_name:      layer name (for by_layer)
        """
        self._log_debug(f"Starting merge all files: {existing_dir}")
        merged_files = {}

        for filename, generated_content in generated_files.items():
            # Path resolution
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
                self._log_debug(f"Existing file found: {existing_path}")
                with open(existing_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            else:
                self._log_debug(f"No existing file: {existing_path}")
                existing_content = None

            merged_files[filename] = self.merge_file(
                generated_content, existing_content,
            )

        return merged_files

    # ===== Marker existence =====
    def has_user_code(self, content: str) -> bool:
        """Whether the content contains user code"""
        return self.markers['file_user_start'] in content

    def has_func_user_code(self, content: str, func_name: str) -> bool:
        """Whether a specific function contains user code"""
        start = self.markers['func_user_start'].format(func_name=func_name)
        return start in content

    def get_user_code_summary(self, content: str) -> Dict[str, int]:
        """Get user code summary"""
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