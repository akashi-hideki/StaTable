"""patch_v3_5_handover_release.py

Append v3.5.0 release section to HANDOVER_v3_5_0.md.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HD = ROOT / "docs" / "HANDOVER_v3_5_0.md"

APPEND = """

---

## v3.5.0 リリース確定 (2026-10-11)

### 追加コミット (v3.5.0 リリース分)

- `27e2fbf` docs(v3.5.0): update README test counts (47 suites / 1682 PASS)
- `9e6e38a` test(v3.5.0): add test_v3_5_gui_output_clean.py (25 tests)
- `7044d2c` feat(v3.5.0): add stale-file warning + Clean & Regenerate UI
- `d58a6d9` feat(v3.5.0): record last_orphans in save_generated_code
- `7d9cd02` feat(v3.5.0): add find_orphan_files public API

### S-GUI 完了: GUI output クリア問題 (優先度 S)

**症状**: GUI コード生成時、output/ をクリアせず生成するため、
旧アーキテクチャの残骸 (Driver/ 層等) が残存し、リンク失敗。

**解決策 (B + C 併用)**:

1. **公開 API** `statable/output_utils.find_orphan_files()`
   - `output_dir` を再帰走査、`saved_files` に無いファイルを返す
   - codegen / GUI / CLI から再利用可能

2. **codegen 側記録** `CCodeGenerator.last_orphans`
   - `save_generated_code` 直後に orphan 一覧を保持
   - API 互換 (戻り値は `saved_files` のまま)

3. **GUI 警告** `statable_gui/output_warning.show_orphan_warning()`
   - 警告ダイアログに [Clean && Regenerate] [Ignore]
   - main_window / code_generation_dialog の両経路から呼ぶ

4. **堅牢削除** `statable_gui/fs_cleanup.robust_rmtree()`
   - `os.chmod(path, stat.S_IWRITE)` + 3 回リトライ
   - Windows + OneDrive (PINNED / REPARSE_POINT) の
     WinError 5 を解消

5. **UI 追加** main_window に `clean_generate_code()`
   - toolbar / menu に「Clean generate」アクション
   - `skip_confirm=True` で警告ダイアログから直接呼び出し

### 検証結果

- **新テスト**: `test_v3_5_gui_output_clean.py` 25 PASS
- **CI 登録**: 47 test files / all registered
- **README**: 47 suites / 1682 PASS に更新
- **ビルド検証** (Clean & Regenerate 後):
  - gcc 構文: 27/27 PASS
  - ARM 構文: 27/27 PASS
  - ARM リンク: LINK PASS
  - firmware.bin: **28540 bytes** (v3.4.3 と同一)
- **GUI 実機**: WinError 5 解消、警告ダイアログに
  Clean && Regenerate ボタン表示確認

### v3.5.0 の残課題 (v3.5.1 以降)

- Phase 1c: mypy 残 58 errors (statable/xml_io.py 中心)
- S-3 Step 2: ubuntu-26.04 preview (2026-10-19 以降)
- ビジネススレッド: WeChat 投稿、知財弁護士候補

---

End of v3.5.0 release section.
"""

t = HD.read_text(encoding="utf-8")
if "v3.5.0 \u30ea\u30ea\u30fc\u30b9\u78ba\u5b9a" in t:
    print("[SKIP] already appended")
else:
    HD.write_text(t + APPEND, encoding="utf-8")
    print(f"[OK] appended to {HD}")
